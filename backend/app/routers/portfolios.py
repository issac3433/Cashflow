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
    """Create a new portfolio."""
    name = payload.get("name", "Default")
    
    portfolio = Portfolio(user_id=user_id, name=name, created_at=datetime.utcnow())
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
    
    # Calculate portfolio value with error handling
    symbols = [h.symbol for h in holdings]
    prices = {}
    
    try:
        prices = batch_fetch_latest_prices(symbols) if symbols else {}
    except Exception as e:
        print(f"[Portfolio] Error fetching prices: {e}")
        # Continue with avg_price as fallback
    
    total_value = 0.0
    holdings_with_quotes = []
    
    for holding in holdings:
        latest_price = prices.get(holding.symbol, holding.avg_price)
        market_value = latest_price * holding.shares
        total_value += market_value
        
        holdings_with_quotes.append({
            "id": holding.id,
            "symbol": holding.symbol,
            "shares": holding.shares,
            "avg_price": holding.avg_price,
            "latest_price": latest_price,
            "market_value": market_value,
            "reinvest_dividends": holding.reinvest_dividends,
        })
    
    return {
        "portfolio": {
            "id": portfolio.id,
            "name": portfolio.name,
            "user_id": portfolio.user_id,
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