# app/routers/portfolios.py
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import Dict, Any, List
from datetime import datetime

from app.core.security import get_current_user_id
from app.db import get_session
from app.models import Portfolio, Holding
from app.services.prices import batch_fetch_latest_prices

router = APIRouter(tags=["portfolios"])

@router.get("")
def list_my_portfolios(
    user_id: str = Depends(get_current_user_id),
    session: Session = Depends(get_session)
):
    """Get all portfolios for the current user."""
    portfolios = session.exec(select(Portfolio).where(Portfolio.user_id == user_id)).all()
    return portfolios

@router.post("")
def create_portfolio(
    payload: Dict[str, Any],
    user_id: str = Depends(get_current_user_id),
    session: Session = Depends(get_session)
):
    """Create a new portfolio with type limits (max 1 Individual + 1 Retirement)."""
    name = payload.get("name", "Default")
    portfolio_type = payload.get("portfolio_type", "individual")
    
    # Validate portfolio type
    if portfolio_type not in ["individual", "retirement"]:
        raise HTTPException(400, detail="Portfolio type must be 'individual' or 'retirement'")
    
    # Check existing portfolios of this type
    existing_portfolios = session.exec(
        select(Portfolio).where(
            Portfolio.user_id == user_id,
            Portfolio.portfolio_type == portfolio_type
        )
    ).all()
    
    if len(existing_portfolios) >= 1:
        raise HTTPException(
            400, 
            detail=f"You can only have 1 {portfolio_type} portfolio. You already have: {existing_portfolios[0].name}"
        )
    
    # Create new portfolio
    portfolio = Portfolio(
        user_id=user_id, 
        name=name, 
        portfolio_type=portfolio_type,
        created_at=datetime.utcnow()
    )
    session.add(portfolio)
    session.commit()
    session.refresh(portfolio)
    
    return portfolio

@router.get("/{portfolio_id}")
def get_portfolio(
    portfolio_id: int,
    user_id: str = Depends(get_current_user_id),
    session: Session = Depends(get_session)
):
    """Get a specific portfolio with holdings and summary."""
    portfolio = session.get(Portfolio, portfolio_id)
    if not portfolio or portfolio.user_id != user_id:
        raise HTTPException(404, detail="Portfolio not found")
    
    # Get holdings with quotes
    holdings = session.exec(
        select(Holding).where(Holding.portfolio_id == portfolio_id)
    ).all()
    
    # Debug: Log all holdings found
    print(f"[Portfolio] Found {len(holdings)} holdings for portfolio {portfolio_id}")
    for h in holdings:
        print(f"[Portfolio] Holding: {h.symbol} ({h.shares} shares)")
    
    # Calculate portfolio value with error handling
    symbols = [h.symbol for h in holdings]
    prices = {}
    
    # Try to fetch prices, but use avg_price as fallback if it fails or times out
    # This prevents the entire endpoint from being slow
    if symbols:
        try:
            prices = batch_fetch_latest_prices(symbols)
        except Exception as e:
            print(f"[Portfolio] Error fetching prices: {e}")
            # Continue with avg_price as fallback - don't fail the whole request
            prices = {}
    
    total_value = 0.0
    holdings_with_quotes = []
    
    for holding in holdings:
        # Use fetched price if available, otherwise fallback to avg_price
        symbol_key = holding.symbol.upper()
        current_price = prices.get(symbol_key) if prices.get(symbol_key) is not None else holding.avg_price
        current_value = current_price * holding.shares
        total_value += current_value
        
        # Calculate gain/loss
        cost_basis = holding.avg_price * holding.shares
        gain_loss = current_value - cost_basis
        gain_loss_percent = (gain_loss / cost_basis * 100) if cost_basis > 0 else 0
        
        holdings_with_quotes.append({
            "id": holding.id,
            "symbol": holding.symbol,
            "shares": holding.shares,
            "avg_price": holding.avg_price,
            "current_price": current_price,  # Changed from latest_price to match frontend
            "current_value": current_value,   # Added to match frontend
            "gain_loss": gain_loss,           # Added for frontend display
            "gain_loss_percent": gain_loss_percent,  # Added for frontend display
            "reinvest_dividends": holding.reinvest_dividends,
        })
    
    return {
        "portfolio": {
            "id": portfolio.id,
            "name": portfolio.name,
            "portfolio_type": portfolio.portfolio_type,
            "user_id": portfolio.user_id,
            "cash_balance": portfolio.cash_balance or 0.0,
            "created_at": portfolio.created_at,
        },
        "holdings": holdings_with_quotes,
        "total_value": total_value,
        "holdings_count": len(holdings),
    }

@router.delete("/{portfolio_id}")
def delete_portfolio(
    portfolio_id: int,
    user_id: str = Depends(get_current_user_id),
    session: Session = Depends(get_session)
):
    """Delete a portfolio and all its holdings."""
    portfolio = session.get(Portfolio, portfolio_id)
    if not portfolio or portfolio.user_id != user_id:
        raise HTTPException(404, detail="Portfolio not found")
    
    # Delete all holdings first
    holdings = session.exec(
        select(Holding).where(Holding.portfolio_id == portfolio_id)
    ).all()
    for holding in holdings:
        session.delete(holding)
    
    # Delete portfolio
    session.delete(portfolio)
    session.commit()
    
    return {"message": f"Portfolio {portfolio_id} deleted successfully"}