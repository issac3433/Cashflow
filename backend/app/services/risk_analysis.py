# backend/app/services/risk_analysis.py
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from sqlmodel import Session, select
from app.models import Holding, Portfolio
from app.services.earnings_risk import generate_earnings_risk_report
from app.services.prices import fetch_latest_price, batch_fetch_latest_prices
import statistics
import math

def calculate_portfolio_volatility(returns: List[float]) -> float:
    """Calculate portfolio volatility (standard deviation of returns)"""
    if len(returns) < 2:
        return 0.0
    return statistics.stdev(returns)

def calculate_beta(portfolio_returns: List[float], market_returns: List[float]) -> float:
    """Calculate portfolio beta relative to market"""
    if len(portfolio_returns) != len(market_returns) or len(portfolio_returns) < 2:
        return 1.0  # Default to market beta
    
    # Calculate covariance and variance
    portfolio_mean = statistics.mean(portfolio_returns)
    market_mean = statistics.mean(market_returns)
    
    covariance = sum((p - portfolio_mean) * (m - market_mean) 
                    for p, m in zip(portfolio_returns, market_returns)) / (len(portfolio_returns) - 1)
    
    market_variance = statistics.variance(market_returns)
    
    if market_variance == 0:
        return 1.0
    
    return covariance / market_variance

def calculate_sharpe_ratio(returns: List[float], risk_free_rate: float = 0.02) -> float:
    """Calculate Sharpe ratio (risk-adjusted return)"""
    if not returns:
        return 0.0
    
    avg_return = statistics.mean(returns)
    volatility = calculate_portfolio_volatility(returns)
    
    if volatility == 0:
        return 0.0
    
    return (avg_return - risk_free_rate) / volatility

def calculate_max_drawdown(portfolio_values: List[float]) -> Dict[str, float]:
    """Calculate maximum drawdown"""
    if not portfolio_values:
        return {"max_drawdown": 0.0, "max_drawdown_period": 0}
    
    peak = portfolio_values[0]
    max_dd = 0.0
    max_dd_period = 0
    current_dd_period = 0
    
    for value in portfolio_values:
        if value > peak:
            peak = value
            current_dd_period = 0
        else:
            drawdown = (peak - value) / peak
            current_dd_period += 1
            
            if drawdown > max_dd:
                max_dd = drawdown
                max_dd_period = current_dd_period
    
    return {
        "max_drawdown": max_dd,
        "max_drawdown_period": max_dd_period
    }

def calculate_var(returns: List[float], confidence_level: float = 0.05) -> float:
    """Calculate Value at Risk (VaR)"""
    if not returns:
        return 0.0
    
    sorted_returns = sorted(returns)
    index = int(confidence_level * len(sorted_returns))
    
    if index >= len(sorted_returns):
        index = len(sorted_returns) - 1
    
    return abs(sorted_returns[index])

def calculate_concentration_risk(holdings: List[Holding]) -> Dict[str, float]:
    """Calculate concentration risk metrics"""
    if not holdings:
        return {"herfindahl_index": 0.0, "max_weight": 0.0, "top_5_weight": 0.0}
    
    print(f"[Risk Analysis] Calculating concentration risk for {len(holdings)} holdings")
    
    # Get current prices and calculate weights
    total_value = 0.0
    holding_values = []
    
    # Batch fetch prices for better performance
    symbols = [h.symbol.upper() for h in holdings]
    prices = batch_fetch_latest_prices(symbols)
    
    for holding in holdings:
        symbol_key = holding.symbol.upper()
        price = prices.get(symbol_key) or holding.avg_price or 100.0  # Use fetched price, then avg_price, then fallback
        value = holding.shares * price
        holding_values.append(value)
        total_value += value
        print(f"[Risk Analysis] {holding.symbol}: {holding.shares} shares @ ${price:.2f} = ${value:.2f}")
    
    if total_value == 0:
        return {"herfindahl_index": 0.0, "max_weight": 0.0, "top_5_weight": 0.0}
    
    # Calculate weights
    weights = [value / total_value for value in holding_values]
    
    # Herfindahl-Hirschman Index (concentration measure)
    hhi = sum(w ** 2 for w in weights)
    
    # Maximum weight
    max_weight = max(weights) if weights else 0.0
    
    # Top 5 holdings weight
    sorted_weights = sorted(weights, reverse=True)
    top_5_weight = sum(sorted_weights[:5])
    
    # Create list of holdings with their weights for top holdings display
    holdings_with_weights = [
        {"symbol": holdings[i].symbol, "weight": weights[i]}
        for i in range(len(holdings))
    ]
    # Sort by weight descending
    holdings_with_weights.sort(key=lambda x: x["weight"], reverse=True)
    
    return {
        "herfindahl_index": hhi,
        "max_weight": max_weight,
        "top_5_weight": top_5_weight,
        "num_holdings": len(holdings),
        "top_holdings": holdings_with_weights[:10]  # Top 10 holdings by weight
    }

def calculate_dividend_risk(holdings: List[Holding], session: Session) -> Dict[str, any]:
    """Calculate dividend sustainability and risk metrics"""
    from app.models import DividendEvent
    
    dividend_risks = {}
    
    for holding in holdings:
        # Get recent dividend events
        recent_dividends = session.exec(
            select(DividendEvent)
            .where(DividendEvent.symbol == holding.symbol)
            .order_by(DividendEvent.ex_date.desc())
            .limit(12)  # Last 12 payments
        ).all()
        
        if not recent_dividends:
            dividend_risks[holding.symbol] = {
                "sustainability_score": 0.0,
                "volatility": 0.0,
                "growth_trend": 0.0,
                "risk_level": "Unknown"
            }
            continue
        
        # Calculate dividend volatility
        amounts = [d.amount for d in recent_dividends]
        volatility = calculate_portfolio_volatility(amounts) if len(amounts) > 1 else 0.0
        
        # Calculate growth trend
        if len(amounts) >= 4:
            first_half = statistics.mean(amounts[:len(amounts)//2])
            second_half = statistics.mean(amounts[len(amounts)//2:])
            growth_trend = (second_half - first_half) / first_half if first_half > 0 else 0.0
        else:
            growth_trend = 0.0
        
        # Calculate sustainability score (0-100)
        sustainability_score = 50.0  # Base score
        
        # Adjust based on volatility (lower volatility = higher score)
        if volatility > 0:
            sustainability_score -= min(volatility * 100, 30)
        
        # Adjust based on growth trend
        if growth_trend > 0:
            sustainability_score += min(growth_trend * 50, 20)
        else:
            sustainability_score += max(growth_trend * 50, -20)
        
        # Determine risk level
        if sustainability_score >= 70:
            risk_level = "Low"
        elif sustainability_score >= 50:
            risk_level = "Medium"
        elif sustainability_score >= 30:
            risk_level = "High"
        else:
            risk_level = "Very High"
        
        dividend_risks[holding.symbol] = {
            "sustainability_score": max(0, min(100, sustainability_score)),
            "volatility": volatility,
            "growth_trend": growth_trend,
            "risk_level": risk_level,
            "recent_amounts": amounts[:5]  # Last 5 payments
        }
    
    return dividend_risks

def generate_risk_report(session: Session, portfolio_id: int) -> Dict[str, any]:
    """Generate comprehensive risk analysis report"""
    
    # Get portfolio holdings - ensure we get all holdings including newly added ones
    # Refresh the session to ensure we see the latest data
    session.expire_all()
    
    holdings = session.exec(
        select(Holding).where(Holding.portfolio_id == portfolio_id)
    ).all()
    
    # Debug logging
    print(f"[Risk Analysis] Found {len(holdings)} holdings for portfolio {portfolio_id}")
    for h in holdings:
        print(f"[Risk Analysis] Holding: {h.symbol} ({h.shares} shares, id={h.id})")
    
    if not holdings:
        print(f"[Risk Analysis] No holdings found for portfolio {portfolio_id}")
        return {"error": "No holdings found for portfolio"}
    
    # Calculate portfolio metrics
    # Batch fetch prices for all holdings at once (more efficient)
    symbols = [h.symbol.upper() for h in holdings]
    prices = batch_fetch_latest_prices(symbols)
    
    portfolio_value = 0.0
    holding_details = []
    
    for holding in holdings:
        symbol_key = holding.symbol.upper()
        # Use fetched price, fallback to avg_price, then default
        price = prices.get(symbol_key) if prices.get(symbol_key) is not None else (holding.avg_price or 100.0)
        value = holding.shares * price
        portfolio_value += value
        
        holding_details.append({
            "symbol": holding.symbol,
            "shares": holding.shares,
            "price": price,
            "value": value,
            "weight": 0.0  # Will calculate after total
        })
        print(f"[Risk Analysis] Processing {holding.symbol}: {holding.shares} shares @ ${price:.2f} = ${value:.2f}")
    
    # Calculate weights
    for detail in holding_details:
        detail["weight"] = detail["value"] / portfolio_value if portfolio_value > 0 else 0.0
    
    # Mock historical returns (in real implementation, you'd fetch historical data)
    # For now, we'll simulate based on typical stock behavior
    mock_returns = []
    for _ in range(252):  # 1 year of daily returns
        # Simulate returns based on portfolio composition
        daily_return = 0.0
        for detail in holding_details:
            # Simulate individual stock returns
            stock_return = (statistics.NormalDist(0, 0.02).samples(1)[0]) * detail["weight"]
            daily_return += stock_return
        mock_returns.append(daily_return)
    
    # Calculate risk metrics
    volatility = calculate_portfolio_volatility(mock_returns)
    beta = calculate_beta(mock_returns, mock_returns)  # Using same data as market proxy
    sharpe_ratio = calculate_sharpe_ratio(mock_returns)
    
    # Calculate portfolio values for drawdown
    portfolio_values = [1000]  # Starting value
    for ret in mock_returns:
        portfolio_values.append(portfolio_values[-1] * (1 + ret))
    
    max_dd = calculate_max_drawdown(portfolio_values)
    var_95 = calculate_var(mock_returns, 0.05)
    var_99 = calculate_var(mock_returns, 0.01)
    
    # Concentration risk
    concentration = calculate_concentration_risk(holdings)
    
    # Dividend risk
    dividend_risks = calculate_dividend_risk(holdings, session)
    
    # Earnings risk analysis
    earnings_risks = {}
    total_earnings_risk = 0.0
    
    for holding in holdings:
        current_price = fetch_latest_price(holding.symbol) or 100.0
        earnings_risk = generate_earnings_risk_report(holding.symbol, current_price)
        earnings_risks[holding.symbol] = earnings_risk
        total_earnings_risk += earnings_risk["earnings_risk_score"] * holding.shares
    
    # Normalize earnings risk by total shares
    total_shares = sum(h.shares for h in holdings)
    avg_earnings_risk = total_earnings_risk / total_shares if total_shares > 0 else 50.0
    
    # Risk score calculation (0-100, lower is riskier)
    risk_score = 50.0  # Base score
    
    # Adjust based on volatility
    if volatility > 0.03:  # High volatility
        risk_score -= 20
    elif volatility > 0.02:  # Medium volatility
        risk_score -= 10
    
    # Adjust based on concentration
    if concentration["max_weight"] > 0.5:  # Highly concentrated
        risk_score -= 15
    elif concentration["max_weight"] > 0.3:  # Moderately concentrated
        risk_score -= 8
    
    # Adjust based on dividend risk
    avg_dividend_risk = statistics.mean([
        risk["sustainability_score"] for risk in dividend_risks.values()
    ]) if dividend_risks else 50
    
    risk_score += (avg_dividend_risk - 50) / 5  # Adjust based on dividend sustainability
    
    # Adjust based on earnings risk
    if avg_earnings_risk > 60:  # High earnings risk
        risk_score -= 15
    elif avg_earnings_risk > 40:  # Medium earnings risk
        risk_score -= 8
    else:
        risk_score -= 3  # Low earnings risk
    
    # Determine overall risk level
    if risk_score >= 70:
        overall_risk = "Low"
    elif risk_score >= 50:
        overall_risk = "Medium"
    elif risk_score >= 30:
        overall_risk = "High"
    else:
        overall_risk = "Very High"
    
    return {
        "portfolio_id": portfolio_id,
        "portfolio_value": portfolio_value,
        "num_holdings": len(holdings),
        "risk_score": max(0, min(100, risk_score)),
        "overall_risk_level": overall_risk,
        
        # Market risk metrics
        "volatility": volatility,
        "beta": beta,
        "sharpe_ratio": sharpe_ratio,
        "max_drawdown": max_dd["max_drawdown"],
        "max_drawdown_period": max_dd["max_drawdown_period"],
        "var_95": var_95,
        "var_99": var_99,
        
        # Concentration risk
        "concentration": concentration,
        
        # Dividend risk
        "dividend_risks": dividend_risks,
        
        # Earnings risk
        "earnings_risks": earnings_risks,
        "avg_earnings_risk": avg_earnings_risk,
        
        # Holdings breakdown
        "holdings": holding_details,
        
        # Risk recommendations
        "recommendations": generate_risk_recommendations(
            volatility, concentration, dividend_risks, risk_score, earnings_risks
        )
    }

def generate_risk_recommendations(volatility: float, concentration: Dict, 
                                dividend_risks: Dict, risk_score: float, 
                                earnings_risks: Dict = None) -> List[str]:
    """Generate risk management recommendations"""
    recommendations = []
    
    # Volatility recommendations
    if volatility > 0.03:
        recommendations.append("Consider reducing portfolio volatility by adding more stable assets")
    elif volatility < 0.01:
        recommendations.append("Portfolio is very stable - consider adding growth opportunities")
    
    # Concentration recommendations
    if concentration["max_weight"] > 0.4:
        recommendations.append("High concentration risk - consider diversifying holdings")
    elif concentration["num_holdings"] < 5:
        recommendations.append("Low diversification - consider adding more holdings")
    
    # Dividend risk recommendations
    high_risk_dividends = [symbol for symbol, risk in dividend_risks.items() 
                          if risk["risk_level"] in ["High", "Very High"]]
    
    if high_risk_dividends:
        recommendations.append(f"Monitor dividend sustainability for: {', '.join(high_risk_dividends)}")
    
    # Earnings risk recommendations
    if earnings_risks:
        high_earnings_risk = [symbol for symbol, risk in earnings_risks.items() 
                             if risk["overall_risk_level"] in ["High"]]
        
        if high_earnings_risk:
            recommendations.append(f"High earnings risk detected for: {', '.join(high_earnings_risk)}")
            recommendations.append("Consider monitoring upcoming earnings calls and guidance")
        
        # Check for earnings surprise patterns
        surprise_risks = [symbol for symbol, risk in earnings_risks.items() 
                         if risk["surprise_analysis"].get("risk_level") == "High"]
        
        if surprise_risks:
            recommendations.append(f"Monitor earnings surprises for: {', '.join(surprise_risks)}")
    
    # Overall risk recommendations
    if risk_score < 30:
        recommendations.append("Portfolio has high risk - consider risk management strategies")
    elif risk_score > 80:
        recommendations.append("Portfolio is very conservative - consider growth opportunities")
    
    return recommendations
