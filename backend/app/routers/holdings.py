# app/routers/holdings.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select
from sqlalchemy import func
from typing import Optional, List, Dict, Any
from datetime import datetime

from app.db import get_session
from app.models import Holding, UserProfile, Portfolio
from app.core.security import get_current_user_id
from app.services.prices import fetch_latest_price, batch_fetch_latest_prices
from app.services.dividends import fetch_dividends, upsert_dividends

router = APIRouter(tags=["holdings"])

@router.post("")
def create_holding(
    payload: Dict[str, Any],
    user_id: str = Depends(get_current_user_id),
    session: Session = Depends(get_session),
):
    """
    Create a new holding in a portfolio and deduct cash.
    payload: { portfolio_id:int, symbol:str, shares:float, avg_price:float|null, reinvest_dividends?:bool }
    If avg_price is null/None, we fetch the latest price and store that.
    """
    try:
        portfolio_id = int(payload["portfolio_id"])
        symbol = str(payload["symbol"]).upper().strip()
        shares = float(payload["shares"])
    except Exception:
        raise HTTPException(400, detail="portfolio_id, symbol, shares are required")

    reinvest = bool(payload.get("reinvest_dividends", True))
    avg_price = payload.get("avg_price")
    quote_used = None

    if avg_price is None:
        quote_used = fetch_latest_price(symbol)
        if quote_used is None:
            # Use a default price when external fetching fails (for performance)
            avg_price = 100.0  # Default price
            quote_used = avg_price
        else:
            avg_price = quote_used

    # Calculate total cost
    total_cost = float(avg_price) * shares
    
    # Get the portfolio and verify ownership
    portfolio = session.get(Portfolio, portfolio_id)
    if not portfolio:
        raise HTTPException(404, detail="Portfolio not found")
    
    if portfolio.user_id != user_id:
        raise HTTPException(403, detail="You don't have access to this portfolio")
    
    # Check if portfolio has enough cash
    current_balance = portfolio.cash_balance or 0.0
    if current_balance < total_cost:
        raise HTTPException(
            400, 
            detail=f"Insufficient cash. Required: ${total_cost:,.2f}, Available: ${current_balance:,.2f}"
        )
    
    # Deduct cash from portfolio balance
    portfolio.cash_balance = current_balance - total_cost
    session.add(portfolio)

    # Check if holding with same symbol already exists in this portfolio
    # Find ALL existing holdings (case-insensitive) to merge them together
    existing_holdings = session.exec(
        select(Holding).where(
            Holding.portfolio_id == portfolio_id,
            func.upper(Holding.symbol) == symbol.upper()
        )
    ).all()
    
    if existing_holdings:
        # Merge all existing holdings + new purchase into one
        # Calculate total shares and weighted average across all
        total_existing_shares = sum(h.shares for h in existing_holdings)
        total_existing_cost = sum(h.shares * h.avg_price for h in existing_holdings)
        new_shares = shares
        new_price = float(avg_price)
        new_cost = new_shares * new_price
        
        # Calculate new weighted average across all holdings
        total_shares = total_existing_shares + new_shares
        total_cost = total_existing_cost + new_cost
        new_avg_price = total_cost / total_shares if total_shares > 0 else new_price
        
        # Use the first existing holding as the primary one to update
        primary_holding = existing_holdings[0]
        primary_holding.shares = total_shares
        primary_holding.avg_price = new_avg_price
        # Keep the earliest purchase_date
        primary_holding.purchase_date = min(h.purchase_date for h in existing_holdings if h.purchase_date)
        
        session.add(primary_holding)
        
        # Delete all other duplicate holdings
        for duplicate in existing_holdings[1:]:
            session.delete(duplicate)
        
        session.commit()
        session.refresh(primary_holding)
        
        h = primary_holding
        action = "updated" if len(existing_holdings) == 1 else "merged"
    else:
        # Create new holding
        h = Holding(
            portfolio_id=portfolio_id,
            symbol=symbol,
            shares=shares,
            avg_price=float(avg_price),
            reinvest_dividends=reinvest,
            purchase_date=datetime.utcnow(),
        )
        session.add(h)
        session.commit()
        session.refresh(h)
        action = "created"
    
    # Refresh portfolio to get updated balance
    session.refresh(portfolio)
    
    # Automatically sync dividends for the new/updated symbol (non-blocking)
    # This runs in the background so it doesn't slow down the holding creation response
    import threading
    def sync_dividends_async():
        try:
            # Use a separate session for the async operation to avoid blocking
            from app.db import Session as DBSession, engine
            with DBSession(engine) as async_session:
                print(f"[Holdings] Auto-syncing dividends for {symbol} (async)...")
                dividend_events = fetch_dividends(symbol)
                print(f"[Holdings] fetch_dividends returned {len(dividend_events)} events for {symbol}")
                
                if dividend_events:
                    inserted_count = upsert_dividends(async_session, dividend_events, commit=True)
                    print(f"[Holdings] Auto-synced {inserted_count} dividend events for {symbol} (total events: {len(dividend_events)})")
                else:
                    print(f"[Holdings] No dividend events found for {symbol} - this may be normal for some stocks/ETFs")
        except Exception as e:
            # Log error but don't fail - this is background work
            print(f"[Holdings] Failed to auto-sync dividends for {symbol}: {e}")
            import traceback
            traceback.print_exc()
    
    # Start async sync in background thread (non-blocking)
    sync_thread = threading.Thread(target=sync_dividends_async, daemon=True)
    sync_thread.start()
    # Don't wait for it - let it run in background
    
    return {
        "holding": {
            "id": h.id,
            "portfolio_id": h.portfolio_id,
            "symbol": h.symbol,
            "shares": h.shares,
            "avg_price": h.avg_price,
            "reinvest_dividends": h.reinvest_dividends,
        },
        "quote_used": float(quote_used) if quote_used is not None else float(avg_price),
        "cash_deducted": total_cost,
        "new_cash_balance": portfolio.cash_balance,
        "action": action,  # "created" or "updated"
    }

@router.get("/with-quotes")
def holdings_with_quotes(
    portfolio_id: int = Query(..., description="Portfolio ID"),
    session: Session = Depends(get_session),
):
    """
    Returns holdings with latest market quotes and computed market_value.
    """
    rows: List[Holding] = session.exec(
        select(Holding).where(Holding.portfolio_id == portfolio_id)
    ).all()

    syms = [r.symbol.upper() for r in rows]
    price_map = batch_fetch_latest_prices(syms)

    out: List[Dict[str, Any]] = []
    for r in rows:
        sym = r.symbol.upper()
        lp = price_map.get(sym)
        mv = (lp or 0.0) * float(r.shares or 0.0)
        out.append({
            "id": r.id,
            "portfolio_id": r.portfolio_id,
            "symbol": sym,
            "shares": float(r.shares or 0.0),
            "avg_price": float(r.avg_price or 0.0),
            "reinvest_dividends": bool(r.reinvest_dividends),
            "latest_price": lp,
            "market_value": mv,
        })
    return out

@router.get("")
def list_holdings(
    portfolio_id: int = Query(..., description="Portfolio ID"),
    session: Session = Depends(get_session),
):
    """
    Returns basic holdings without quotes (faster).
    """
    rows: List[Holding] = session.exec(
        select(Holding).where(Holding.portfolio_id == portfolio_id)
    ).all()
    
    return [
        {
            "id": r.id,
            "portfolio_id": r.portfolio_id,
            "symbol": r.symbol,
            "shares": r.shares,
            "avg_price": r.avg_price,
            "reinvest_dividends": r.reinvest_dividends,
        }
        for r in rows
    ]

@router.post("/{holding_id}/sell")
def sell_holding(
    holding_id: int,
    payload: Dict[str, Any],
    user_id: str = Depends(get_current_user_id),
    session: Session = Depends(get_session),
):
    """
    Sell shares of a holding and add cash back to portfolio balance.
    payload: { shares: float } - number of shares to sell (must be <= current shares)
    If shares not provided or equals current shares, sells all shares and deletes holding.
    """
    holding = session.get(Holding, holding_id)
    if not holding:
        raise HTTPException(404, detail="Holding not found")
    
    # Get the portfolio and verify ownership
    portfolio = session.get(Portfolio, holding.portfolio_id)
    if not portfolio:
        raise HTTPException(404, detail="Portfolio not found")
    
    if portfolio.user_id != user_id:
        raise HTTPException(403, detail="You don't have access to this portfolio")
    
    shares_to_sell = payload.get("shares")
    if shares_to_sell is None:
        shares_to_sell = holding.shares  # Sell all if not specified
    
    shares_to_sell = float(shares_to_sell)
    
    if shares_to_sell <= 0:
        raise HTTPException(400, detail="Shares to sell must be positive")
    
    if shares_to_sell > holding.shares:
        raise HTTPException(400, detail=f"Cannot sell more shares than owned. Owned: {holding.shares}, Requested: {shares_to_sell}")
    
    # Get current market price
    current_price = fetch_latest_price(holding.symbol)
    if current_price is None:
        # Use average price if current price unavailable
        current_price = holding.avg_price
    
    # Calculate proceeds
    proceeds = float(current_price) * shares_to_sell
    
    # Add cash back to portfolio balance
    current_balance = portfolio.cash_balance or 0.0
    portfolio.cash_balance = current_balance + proceeds
    session.add(portfolio)
    
    # Update or delete holding
    if shares_to_sell >= holding.shares:
        # Selling all shares - delete holding
        session.delete(holding)
        message = f"Sold all {holding.shares} shares of {holding.symbol}"
    else:
        # Selling partial shares - update holding
        holding.shares -= shares_to_sell
        session.add(holding)
        message = f"Sold {shares_to_sell} shares of {holding.symbol} (remaining: {holding.shares})"
    
    session.commit()
    session.refresh(portfolio)
    
    return {
        "message": message,
        "shares_sold": shares_to_sell,
        "price_per_share": current_price,
        "proceeds": proceeds,
        "new_cash_balance": portfolio.cash_balance,
    }

@router.delete("/{holding_id}")
def delete_holding(
    holding_id: int,
    user_id: str = Depends(get_current_user_id),
    session: Session = Depends(get_session),
):
    """
    Delete a holding by ID (legacy endpoint - use sell endpoint instead).
    This will NOT add cash back - use /sell endpoint for that.
    """
    holding = session.get(Holding, holding_id)
    if not holding:
        raise HTTPException(404, detail="Holding not found")
    
    session.delete(holding)
    session.commit()
    return {"message": f"Holding {holding_id} deleted successfully (no cash refunded)"}