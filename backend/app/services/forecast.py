# backend/app/services/forecast.py
from datetime import date, datetime, timedelta
from sqlmodel import Session, select
from app.models import Holding, DividendEvent
from typing import Dict, List, Tuple
from collections import defaultdict

def analyze_dividend_patterns(session: Session, symbols: List[str]) -> Dict[str, Dict]:
    """Analyze dividend payment patterns for each symbol"""
    patterns = {}
    
    for symbol in symbols:
        # Get dividend events for this symbol
        events = session.exec(
            select(DividendEvent).where(DividendEvent.symbol == symbol)
            .order_by(DividendEvent.ex_date)
        ).all()
        
        if not events:
            continue
            
        # Analyze payment frequency using basic Python
        monthly_counts = defaultdict(int)
        amounts = []
        
        for event in events:
            month = event.ex_date.month
            monthly_counts[month] += 1
            amounts.append(event.amount)
        
        payment_months = sorted([m for m, count in monthly_counts.items() if count > 0])
        
        # Calculate growth rate (simplified)
        growth_rate = 0.0
        if len(amounts) > 1:
            # Simple linear growth calculation
            first_half = sum(amounts[:len(amounts)//2]) / (len(amounts)//2)
            second_half = sum(amounts[len(amounts)//2:]) / (len(amounts) - len(amounts)//2)
            if first_half > 0:
                growth_rate = (second_half / first_half) - 1
                growth_rate = max(0, min(growth_rate, 0.15))  # Cap between 0% and 15%
        
        # Recent average amount
        recent_avg = sum(amounts[-12:]) / min(len(amounts), 12) if amounts else 0
        
        patterns[symbol] = {
            'payment_months': payment_months,
            'frequency': len(payment_months),
            'is_quarterly': len(payment_months) == 4,
            'is_monthly': len(payment_months) >= 10,
            'growth_rate': growth_rate,
            'recent_avg_amount': recent_avg,
            'total_events': len(events)
        }
    
    return patterns

def monthly_cashflow_forecast(session: Session, portfolio_id: int, months: int = 12,
                             assume_reinvest: bool = True, recurring_deposit: float = 0.0,
                             deposit_freq: str = "monthly", start_date: date | None = None,
                             growth_scenario: str = "moderate") -> Dict:
    """
    Enhanced forecasting with realistic dividend patterns and compound growth
    """
    # Refresh session to ensure we see the latest holdings including newly added ones
    session.expire_all()
    
    holdings = session.exec(select(Holding).where(Holding.portfolio_id == portfolio_id)).all()
    
    # Debug logging
    print(f"[Forecast] Found {len(holdings)} holdings for portfolio {portfolio_id}")
    for h in holdings:
        print(f"[Forecast] Holding: {h.symbol} ({h.shares} shares, id={h.id})")
    
    if not holdings:
        print(f"[Forecast] No holdings found for portfolio {portfolio_id}")
        return {"series": [], "total": 0.0, "scenarios": {}}
    
    symbols = [h.symbol for h in holdings]
    print(f"[Forecast] Analyzing dividend patterns for symbols: {symbols}")
    
    # Analyze dividend patterns
    patterns = analyze_dividend_patterns(session, symbols)
    print(f"[Forecast] Found dividend patterns for {len(patterns)} symbols: {list(patterns.keys())}")
    
    # Create date range using basic Python
    start = datetime.now().replace(day=1) if not start_date else datetime.combine(start_date, datetime.min.time())
    date_range = []
    current_date = start
    for _ in range(months):
        date_range.append(current_date)
        # Add one month
        if current_date.month == 12:
            current_date = current_date.replace(year=current_date.year + 1, month=1)
        else:
            current_date = current_date.replace(month=current_date.month + 1)
    
    # Initialize results
    cash_flow = [0.0] * months
    total_shares = {h.symbol: h.shares for h in holdings}
    
    # Growth scenarios
    growth_rates = {
        "conservative": 0.0,
        "moderate": 0.02,
        "optimistic": 0.05,
        "pessimistic": -0.05
    }
    base_growth = growth_rates.get(growth_scenario, 0.02)
    
    # Calculate monthly projections
    for holding in holdings:
        symbol = holding.symbol
        if symbol not in patterns:
            print(f"[Forecast] Warning: No dividend pattern found for {symbol}, skipping in forecast")
            continue
        
        print(f"[Forecast] Processing {symbol}: {holding.shares} shares, pattern: {patterns[symbol]}")
            
        pattern = patterns[symbol]
        shares = total_shares[symbol]
        
        # Calculate base monthly dividend
        if pattern['is_monthly']:
            base_monthly = pattern['recent_avg_amount'] * shares
        elif pattern['is_quarterly']:
            base_monthly = pattern['recent_avg_amount'] * shares / 3  # Quarterly spread over 3 months
        else:
            # Irregular - use annual average
            annual_total = pattern['recent_avg_amount'] * pattern['frequency'] * shares
            base_monthly = annual_total / 12
        
        # Apply growth
        dividend_growth = pattern['growth_rate']
        total_growth = base_growth + dividend_growth
        
        # Generate monthly projections
        for i, month_date in enumerate(date_range):
            month_num = month_date.month
            
            # Check if this month has dividend payments
            if month_num in pattern['payment_months']:
                # Calculate dividend amount with growth
                growth_factor = (1 + total_growth) ** (i / 12)
                dividend_amount = base_monthly * growth_factor
                
                if assume_reinvest:
                    # DRIP: Buy more shares (simplified)
                    current_price = 150.0  # This should come from price service
                    new_shares = dividend_amount / current_price
                    total_shares[symbol] += new_shares
                    
                    # Update future dividends based on new share count
                    base_monthly = pattern['recent_avg_amount'] * total_shares[symbol]
                    if pattern['is_quarterly']:
                        base_monthly /= 3
                
                cash_flow[i] += dividend_amount
            
            # Add recurring deposits
            if recurring_deposit > 0:
                cash_flow[i] += recurring_deposit
    
    # Create results
    series = []
    cumulative = 0.0
    
    for i, month_date in enumerate(date_range):
        monthly_amount = cash_flow[i]
        cumulative += monthly_amount
        
        series.append({
            "month": month_date.strftime("%Y-%m"),
            "income": round(monthly_amount, 2),
            "cumulative": round(cumulative, 2),
            "has_dividend": monthly_amount > 0
        })
    
    # Calculate scenarios - include all scenarios including the selected one
    total_income = sum(cash_flow)
    scenarios = {}
    for scenario_name, growth_rate in growth_rates.items():
        if scenario_name == growth_scenario:
            # For the selected scenario, use the actual calculated total
            scenarios[scenario_name] = round(total_income, 2)
        else:
            # For other scenarios, calculate based on different growth rates
            scenario_total = total_income * (1 + growth_rate)
            scenarios[scenario_name] = round(scenario_total, 2)
    
    print(f"[Forecast] Total income: ${total_income:.2f}, Scenarios: {scenarios}")
    
    return {
        "series": series,
        "total": round(total_income, 2),
        "scenarios": scenarios,
        "patterns": {symbol: {
            "frequency": patterns[symbol]["frequency"],
            "payment_months": patterns[symbol]["payment_months"],
            "growth_rate": round(patterns[symbol]["growth_rate"] * 100, 1)
        } for symbol in symbols if symbol in patterns},
        "assumptions": {
            "reinvest": assume_reinvest,
            "growth_scenario": growth_scenario,
            "recurring_deposit": recurring_deposit
        }
    }