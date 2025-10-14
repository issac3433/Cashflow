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
    
    for portfolio in portfolios:
        holdings = session.exec(select(Holding).where(Holding.portfolio_id == portfolio.id)).all()
        portfolio_value = 0.0
        
        for holding in holdings:
            # Get latest price (simplified - you might want to use your price service)
            from app.services.prices import fetch_latest_price
            latest_price = fetch_latest_price(holding.symbol) or 0.0
            holding_value = holding.shares * latest_price
            portfolio_value += holding_value
            
            # Calculate upcoming dividends
            upcoming_divs = session.exec(
                select(DividendEvent)
                .where(DividendEvent.symbol == holding.symbol)
                .where(DividendEvent.ex_date >= date.today())
            ).all()
            
            for div in upcoming_divs:
                upcoming_dividends += div.amount * holding.shares
        
        total_portfolio_value += portfolio_value
        portfolio_summary.append({
            "id": portfolio.id,
            "name": portfolio.name,
            "value": portfolio_value,
            "holdings_count": len(holdings)
        })
    
    return {
        "user_id": user_id,
        "cash_balance": profile.cash_balance,
        "total_dividends_received": profile.total_dividends_received,
        "total_portfolio_value": total_portfolio_value,
        "upcoming_dividends": upcoming_dividends,
        "total_net_worth": profile.cash_balance + total_portfolio_value,
        "portfolios": portfolio_summary,
        "last_updated": profile.last_updated
    }

@router.post("/profile/cash/add")
def add_cash(request: Dict[str, float], user_id: str = Depends(get_current_user_id), session: Session = Depends(get_session)):
    """Add cash to user's balance"""
    amount = request.get("amount", 0.0)
    if amount <= 0:
        raise HTTPException(400, detail="Amount must be positive")
    
    profile = session.exec(select(UserProfile).where(UserProfile.user_id == user_id)).first()
    if not profile:
        profile = UserProfile(user_id=user_id, cash_balance=0.0, total_dividends_received=0.0)
        session.add(profile)
    
    profile.cash_balance += amount
    profile.last_updated = datetime.utcnow()
    session.add(profile)
    session.commit()
    session.refresh(profile)
    
    return {"message": f"Added ${amount:,.2f} to cash balance", "new_balance": profile.cash_balance}

@router.post("/profile/cash/withdraw")
def withdraw_cash(request: Dict[str, float], user_id: str = Depends(get_current_user_id), session: Session = Depends(get_session)):
    """Withdraw cash from user's balance"""
    amount = request.get("amount", 0.0)
    if amount <= 0:
        raise HTTPException(400, detail="Amount must be positive")
    
    profile = session.exec(select(UserProfile).where(UserProfile.user_id == user_id)).first()
    if not profile:
        raise HTTPException(404, detail="User profile not found")
    
    if profile.cash_balance < amount:
        raise HTTPException(400, detail="Insufficient cash balance")
    
    profile.cash_balance -= amount
    profile.last_updated = datetime.utcnow()
    session.add(profile)
    session.commit()
    session.refresh(profile)
    
    return {"message": f"Withdrew ${amount:,.2f} from cash balance", "new_balance": profile.cash_balance}

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
        # Get dividend events for this symbol
        dividend_events = session.exec(
            select(DividendEvent)
            .where(DividendEvent.symbol == holding.symbol)
            .where(DividendEvent.ex_date <= date.today())  # Only past dividends
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
                
                # Add to cash balance (or reinvest if enabled)
                if holding.reinvest_dividends:
                    # For now, just add to cash - you could implement actual reinvestment later
                    profile.cash_balance += total_amount
                    profile.total_dividends_received += total_amount
                else:
                    profile.cash_balance += total_amount
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
