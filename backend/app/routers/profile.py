# app/routers/profile.py
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import Dict, Any
from datetime import datetime, date

from app.db import get_session
from app.models import UserProfile, DividendPayment, Portfolio, Holding, DividendEvent
from app.core.security import get_current_user_id

router = APIRouter(tags=["profile"])

@router.get("/profile")
def get_user_profile(user_id: str = Depends(get_current_user_id), session: Session = Depends(get_session)):
    """Get user profile with cash balance and portfolio summary"""
    # Get or create user profile
    profile = session.exec(select(UserProfile).where(UserProfile.user_id == user_id)).first()
    if not profile:
        profile = UserProfile(user_id=user_id, cash_balance=0.0, total_dividends_received=0.0)
        session.add(profile)
        session.commit()
        session.refresh(profile)
    
    # Get portfolio summary
    portfolios = session.exec(select(Portfolio).where(Portfolio.user_id == user_id)).all()
    portfolio_summary = []
    
    total_portfolio_value = 0.0
    upcoming_dividends = 0.0
    
    # Collect all symbols across all portfolios for batch price fetch
    all_symbols = []
    portfolio_holdings_map = {}
    
    for portfolio in portfolios:
        holdings = session.exec(select(Holding).where(Holding.portfolio_id == portfolio.id)).all()
        portfolio_holdings_map[portfolio.id] = holdings
        for holding in holdings:
            if holding.symbol not in all_symbols:
                all_symbols.append(holding.symbol)
    
    # Skip price fetching and dividend queries for home screen - prioritize speed!
    # Home screen is just a summary view, doesn't need real-time data
    # This makes the endpoint instant (no external API calls, no complex queries)
    prices = {}  # Empty dict means we'll use avg_price for all holdings
    upcoming_dividend_events = {}  # Skip dividend queries for speed - not critical for home screen
    
    # Calculate portfolio values using batched prices
    for portfolio in portfolios:
        holdings = portfolio_holdings_map.get(portfolio.id, [])
        portfolio_value = 0.0
        
        for holding in holdings:
            # Use batched price or fallback to avg_price
            latest_price = prices.get(holding.symbol.upper(), holding.avg_price) or holding.avg_price
            holding_value = holding.shares * latest_price
            portfolio_value += holding_value
            
            # Calculate upcoming dividends using batched data
            symbol_key = holding.symbol.upper()
            if symbol_key in upcoming_dividend_events:
                for div in upcoming_dividend_events[symbol_key]:
                    upcoming_dividends += div.amount * holding.shares
        
        total_portfolio_value += portfolio_value
        portfolio_summary.append({
            "id": portfolio.id,
            "name": portfolio.name,
            "portfolio_type": portfolio.portfolio_type,
            "total_value": portfolio_value,  # Changed from "value" to "total_value" to match mobile app
            "cash_balance": portfolio.cash_balance or 0.0,
            "holdings_count": len(holdings)
        })
    
    # Calculate total cash across all portfolios
    total_cash_balance = sum(p.cash_balance or 0.0 for p in portfolios)
    
    return {
        "user_id": user_id,
        "cash_balance": profile.cash_balance,  # Legacy field - kept for compatibility
        "total_dividends_received": profile.total_dividends_received,
        "total_portfolio_value": total_portfolio_value,
        "total_portfolio_cash": total_cash_balance,  # Sum of all portfolio cash balances
        "upcoming_dividends": upcoming_dividends,
        "total_net_worth": total_cash_balance + total_portfolio_value,  # Portfolio cash + portfolio value
        "portfolios": portfolio_summary,
        "last_updated": profile.last_updated
    }

@router.post("/profile/cash/add")
def add_cash(request: Dict[str, Any], user_id: str = Depends(get_current_user_id), session: Session = Depends(get_session)):
    """Add cash to a portfolio's balance"""
    amount = request.get("amount", 0.0)
    portfolio_id = request.get("portfolio_id")
    
    if amount <= 0:
        raise HTTPException(400, detail="Amount must be positive")
    
    if not portfolio_id:
        raise HTTPException(400, detail="portfolio_id is required")
    
    # Get the portfolio and verify ownership
    portfolio = session.get(Portfolio, portfolio_id)
    if not portfolio:
        raise HTTPException(404, detail="Portfolio not found")
    
    if portfolio.user_id != user_id:
        raise HTTPException(403, detail="You don't have access to this portfolio")
    
    # Add cash to portfolio
    portfolio.cash_balance = (portfolio.cash_balance or 0.0) + amount
    session.add(portfolio)
    session.commit()
    session.refresh(portfolio)
    
    return {
        "message": f"Added ${amount:,.2f} to portfolio '{portfolio.name}'",
        "new_balance": portfolio.cash_balance,
        "portfolio_id": portfolio.id,
        "portfolio_name": portfolio.name
    }

@router.post("/profile/cash/withdraw")
def withdraw_cash(request: Dict[str, Any], user_id: str = Depends(get_current_user_id), session: Session = Depends(get_session)):
    """Withdraw cash from a portfolio's balance"""
    amount = request.get("amount", 0.0)
    portfolio_id = request.get("portfolio_id")
    
    if amount <= 0:
        raise HTTPException(400, detail="Amount must be positive")
    
    if not portfolio_id:
        raise HTTPException(400, detail="portfolio_id is required")
    
    # Get the portfolio and verify ownership
    portfolio = session.get(Portfolio, portfolio_id)
    if not portfolio:
        raise HTTPException(404, detail="Portfolio not found")
    
    if portfolio.user_id != user_id:
        raise HTTPException(403, detail="You don't have access to this portfolio")
    
    current_balance = portfolio.cash_balance or 0.0
    if current_balance < amount:
        raise HTTPException(400, detail=f"Insufficient cash balance. Available: ${current_balance:,.2f}, Requested: ${amount:,.2f}")
    
    # Withdraw cash from portfolio
    portfolio.cash_balance = current_balance - amount
    session.add(portfolio)
    session.commit()
    session.refresh(portfolio)
    
    return {
        "message": f"Withdrew ${amount:,.2f} from portfolio '{portfolio.name}'",
        "new_balance": portfolio.cash_balance,
        "portfolio_id": portfolio.id,
        "portfolio_name": portfolio.name
    }

@router.post("/dividends/process")
def process_dividend_payments(user_id: str = Depends(get_current_user_id), session: Session = Depends(get_session)):
    """Process dividend payments and add them to cash balance"""
    # Get all holdings for this user
    portfolios = session.exec(select(Portfolio).where(Portfolio.user_id == user_id)).all()
    portfolio_ids = [p.id for p in portfolios]
    
    if not portfolio_ids:
        return {"message": "No portfolios found", "processed": 0, "total_added": 0.0}
    
    holdings = session.exec(
        select(Holding).where(Holding.portfolio_id.in_(portfolio_ids))
    ).all()
    
    total_added = 0.0
    processed_count = 0
    
    # Get user profile
    profile = session.exec(select(UserProfile).where(UserProfile.user_id == user_id)).first()
    if not profile:
        profile = UserProfile(user_id=user_id, cash_balance=0.0, total_dividends_received=0.0)
        session.add(profile)
    
    for holding in holdings:
        # Get dividend events for this symbol that occurred AFTER purchase date
        dividend_events = session.exec(
            select(DividendEvent)
            .where(DividendEvent.symbol == holding.symbol)
            .where(DividendEvent.ex_date <= date.today())  # Only past dividends
            .where(DividendEvent.ex_date >= holding.purchase_date.date())  # Only after purchase
        ).all()
        
        for div_event in dividend_events:
            # Check if we've already processed this dividend
            existing_payment = session.exec(
                select(DividendPayment)
                .where(DividendPayment.user_id == user_id)
                .where(DividendPayment.symbol == holding.symbol)
                .where(DividendPayment.ex_date == div_event.ex_date)
            ).first()
            
            if not existing_payment:
                # Calculate total dividend amount
                total_amount = div_event.amount * holding.shares
                
                # Create dividend payment record
                payment = DividendPayment(
                    user_id=user_id,
                    portfolio_id=holding.portfolio_id,
                    symbol=holding.symbol,
                    ex_date=div_event.ex_date,
                    pay_date=div_event.pay_date,
                    amount_per_share=div_event.amount,
                    shares_owned=holding.shares,
                    total_amount=total_amount,
                    reinvested=holding.reinvest_dividends
                )
                session.add(payment)
                
                # Get the portfolio for this holding and add dividend to portfolio's cash balance
                portfolio = session.get(Portfolio, holding.portfolio_id)
                if portfolio:
                    # Add dividend to portfolio's cash balance
                    portfolio.cash_balance = (portfolio.cash_balance or 0.0) + total_amount
                    session.add(portfolio)
                
                # Also track total dividends received in user profile (for reporting)
                profile.total_dividends_received += total_amount
                
                total_added += total_amount
                processed_count += 1
    
    profile.last_updated = datetime.utcnow()
    session.add(profile)
    session.commit()
    
    return {
        "message": f"Processed {processed_count} dividend payments",
        "processed": processed_count,
        "total_added": total_added,
        "new_cash_balance": profile.cash_balance
    }

@router.get("/dividends/history")
def get_dividend_history(user_id: str = Depends(get_current_user_id), session: Session = Depends(get_session)):
    """Get user's dividend payment history"""
    payments = session.exec(
        select(DividendPayment)
        .where(DividendPayment.user_id == user_id)
        .order_by(DividendPayment.ex_date.desc())
    ).all()
    
    return {
        "payments": [
            {
                "symbol": p.symbol,
                "ex_date": p.ex_date,
                "pay_date": p.pay_date,
                "amount_per_share": p.amount_per_share,
                "shares_owned": p.shares_owned,
                "total_amount": p.total_amount,
                "reinvested": p.reinvested,
                "processed_at": p.processed_at
            }
            for p in payments
        ]
    }
