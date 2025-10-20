# app/routers/holdings.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select
from typing import Optional, List, Dict, Any
from datetime import datetime

from app.db import get_session
from app.models import Holding
from app.services.prices import fetch_latest_price, batch_fetch_latest_prices

router = APIRouter(tags=["holdings"])

@router.post("")
def create_holding(
    payload: Dict[str, Any],
    session: Session = Depends(get_session),
):
    """
    Create a new holding in a portfolio.
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

@router.delete("/{holding_id}")
def delete_holding(
    holding_id: int,
    session: Session = Depends(get_session),
):
    """
    Delete a holding by ID.
    """
    holding = session.get(Holding, holding_id)
    if not holding:
        raise HTTPException(404, detail="Holding not found")
    
    session.delete(holding)
    session.commit()
    return {"message": f"Holding {holding_id} deleted successfully"}