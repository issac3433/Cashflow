# backend/app/services/earnings_risk.py
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import requests
import os
from dotenv import load_dotenv

load_dotenv()

POLYGON_API_KEY = os.getenv("POLYGON_API_KEY")
ALPHA_KEY = os.getenv("ALPHAVANTAGE_API_KEY")

def fetch_earnings_data(symbol: str) -> Dict[str, any]:
    """Fetch earnings data from Polygon API"""
    if not POLYGON_API_KEY:
        return {"error": "No API key available"}
    
    url = f"https://api.polygon.io/v2/reference/financials"
    params = {
        "ticker": symbol.upper(),
        "limit": 8,  # Last 8 quarters
        "apiKey": POLYGON_API_KEY
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data.get("results", [])
        else:
            return {"error": f"API error: {response.status_code}"}
    except Exception as e:
        return {"error": str(e)}

def fetch_earnings_calendar(symbol: str) -> Dict[str, any]:
    """Fetch upcoming earnings dates and estimates"""
    if not POLYGON_API_KEY:
        return {"error": "No API key available"}
    
    url = f"https://api.polygon.io/v1/meta/symbols/{symbol.upper()}/company"
    params = {"apiKey": POLYGON_API_KEY}
    
    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data
        else:
            return {"error": f"API error: {response.status_code}"}
    except Exception as e:
        return {"error": str(e)}

def analyze_earnings_surprise(earnings_data: List[Dict]) -> Dict[str, any]:
    """Analyze earnings surprise patterns"""
    if not earnings_data or "error" in earnings_data:
        return {"error": "No earnings data available"}
    
    surprises = []
    beats = 0
    misses = 0
    
    for quarter in earnings_data[:8]:  # Last 8 quarters
        if "earnings_per_share" in quarter and "earnings_per_share_estimate" in quarter:
            actual = quarter.get("earnings_per_share", 0)
            estimate = quarter.get("earnings_per_share_estimate", 0)
            
            if estimate != 0:
                surprise = (actual - estimate) / abs(estimate)
                surprises.append(surprise)
                
                if surprise > 0:
                    beats += 1
                else:
                    misses += 1
    
    if not surprises:
        return {"error": "No surprise data available"}
    
    avg_surprise = sum(surprises) / len(surprises)
    surprise_volatility = calculate_volatility(surprises)
    beat_rate = beats / len(surprises) if surprises else 0
    
    # Risk assessment based on surprise patterns
    if beat_rate >= 0.7 and surprise_volatility < 0.1:
        surprise_risk = "Low"
    elif beat_rate >= 0.5 and surprise_volatility < 0.2:
        surprise_risk = "Medium"
    else:
        surprise_risk = "High"
    
    return {
        "avg_surprise": avg_surprise,
        "surprise_volatility": surprise_volatility,
        "beat_rate": beat_rate,
        "beats": beats,
        "misses": misses,
        "risk_level": surprise_risk,
        "quarters_analyzed": len(surprises)
    }

def analyze_revenue_growth(earnings_data: List[Dict]) -> Dict[str, any]:
    """Analyze revenue growth patterns and sustainability"""
    if not earnings_data or "error" in earnings_data:
        return {"error": "No revenue data available"}
    
    revenues = []
    revenue_growth = []
    
    for quarter in earnings_data[:8]:
        if "revenue" in quarter:
            revenue = quarter.get("revenue", 0)
            revenues.append(revenue)
    
    # Calculate quarter-over-quarter growth
    for i in range(1, len(revenues)):
        if revenues[i-1] != 0:
            growth = (revenues[i] - revenues[i-1]) / revenues[i-1]
            revenue_growth.append(growth)
    
    if not revenue_growth:
        return {"error": "No revenue growth data available"}
    
    avg_growth = sum(revenue_growth) / len(revenue_growth)
    growth_volatility = calculate_volatility(revenue_growth)
    
    # Assess revenue sustainability
    if avg_growth > 0.1 and growth_volatility < 0.2:
        revenue_risk = "Low"
    elif avg_growth > 0.05 and growth_volatility < 0.3:
        revenue_risk = "Medium"
    else:
        revenue_risk = "High"
    
    return {
        "avg_growth": avg_growth,
        "growth_volatility": growth_volatility,
        "risk_level": revenue_risk,
        "quarters_analyzed": len(revenue_growth),
        "recent_growth": revenue_growth[-1] if revenue_growth else 0
    }

def analyze_profitability_trends(earnings_data: List[Dict]) -> Dict[str, any]:
    """Analyze profit margins and profitability trends"""
    if not earnings_data or "error" in earnings_data:
        return {"error": "No profitability data available"}
    
    margins = []
    
    for quarter in earnings_data[:8]:
        revenue = quarter.get("revenue", 0)
        net_income = quarter.get("net_income", 0)
        
        if revenue != 0:
            margin = net_income / revenue
            margins.append(margin)
    
    if not margins:
        return {"error": "No margin data available"}
    
    avg_margin = sum(margins) / len(margins)
    margin_volatility = calculate_volatility(margins)
    
    # Trend analysis
    if len(margins) >= 4:
        first_half = sum(margins[:len(margins)//2]) / (len(margins)//2)
        second_half = sum(margins[len(margins)//2:]) / (len(margins) - len(margins)//2)
        margin_trend = second_half - first_half
    else:
        margin_trend = 0
    
    # Assess profitability risk
    if avg_margin > 0.15 and margin_volatility < 0.1 and margin_trend >= 0:
        profitability_risk = "Low"
    elif avg_margin > 0.1 and margin_volatility < 0.2:
        profitability_risk = "Medium"
    else:
        profitability_risk = "High"
    
    return {
        "avg_margin": avg_margin,
        "margin_volatility": margin_volatility,
        "margin_trend": margin_trend,
        "risk_level": profitability_risk,
        "quarters_analyzed": len(margins),
        "recent_margin": margins[-1] if margins else 0
    }

def analyze_guidance_reliability(symbol: str) -> Dict[str, any]:
    """Analyze management guidance reliability and accuracy"""
    # This would typically require historical guidance data
    # For now, we'll simulate based on company characteristics
    
    # Large cap companies tend to have more reliable guidance
    large_caps = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "NVDA"]
    
    if symbol.upper() in large_caps:
        guidance_accuracy = 0.75  # 75% accuracy
        guidance_risk = "Low"
    else:
        guidance_accuracy = 0.60  # 60% accuracy
        guidance_risk = "Medium"
    
    return {
        "guidance_accuracy": guidance_accuracy,
        "risk_level": guidance_risk,
        "company_size": "Large Cap" if symbol.upper() in large_caps else "Mid/Small Cap"
    }

def calculate_volatility(values: List[float]) -> float:
    """Calculate volatility (standard deviation) of a list of values"""
    if len(values) < 2:
        return 0.0
    
    mean = sum(values) / len(values)
    variance = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
    return variance ** 0.5

def calculate_forward_pe_risk(symbol: str, current_price: float) -> Dict[str, any]:
    """Calculate forward P/E risk based on growth expectations"""
    # This would typically use analyst estimates
    # For now, we'll use historical patterns
    
    # Simulate forward P/E based on company characteristics
    if symbol.upper() in ["AAPL", "MSFT"]:
        forward_pe = 25.0
        growth_expectation = 0.08
    elif symbol.upper() in ["TSLA", "NVDA"]:
        forward_pe = 45.0
        growth_expectation = 0.15
    else:
        forward_pe = 20.0
        growth_expectation = 0.05
    
    # Calculate PEG ratio (P/E to Growth)
    peg_ratio = forward_pe / (growth_expectation * 100) if growth_expectation > 0 else 999
    
    # Assess valuation risk
    if peg_ratio < 1.5:
        valuation_risk = "Low"
    elif peg_ratio < 2.5:
        valuation_risk = "Medium"
    else:
        valuation_risk = "High"
    
    return {
        "forward_pe": forward_pe,
        "growth_expectation": growth_expectation,
        "peg_ratio": peg_ratio,
        "risk_level": valuation_risk
    }

def generate_earnings_risk_report(symbol: str, current_price: float = 100.0) -> Dict[str, any]:
    """Generate comprehensive earnings-based risk analysis"""
    
    # Fetch earnings data
    earnings_data = fetch_earnings_data(symbol)
    
    # Analyze different aspects
    surprise_analysis = analyze_earnings_surprise(earnings_data)
    revenue_analysis = analyze_revenue_growth(earnings_data)
    profitability_analysis = analyze_profitability_trends(earnings_data)
    guidance_analysis = analyze_guidance_reliability(symbol)
    valuation_analysis = calculate_forward_pe_risk(symbol, current_price)
    
    # Calculate overall earnings risk score
    risk_factors = []
    
    if surprise_analysis.get("risk_level") == "High":
        risk_factors.append(30)
    elif surprise_analysis.get("risk_level") == "Medium":
        risk_factors.append(15)
    else:
        risk_factors.append(5)
    
    if revenue_analysis.get("risk_level") == "High":
        risk_factors.append(25)
    elif revenue_analysis.get("risk_level") == "Medium":
        risk_factors.append(12)
    else:
        risk_factors.append(5)
    
    if profitability_analysis.get("risk_level") == "High":
        risk_factors.append(20)
    elif profitability_analysis.get("risk_level") == "Medium":
        risk_factors.append(10)
    else:
        risk_factors.append(5)
    
    if guidance_analysis.get("risk_level") == "High":
        risk_factors.append(15)
    elif guidance_analysis.get("risk_level") == "Medium":
        risk_factors.append(8)
    else:
        risk_factors.append(3)
    
    if valuation_analysis.get("risk_level") == "High":
        risk_factors.append(10)
    elif valuation_analysis.get("risk_level") == "Medium":
        risk_factors.append(5)
    else:
        risk_factors.append(2)
    
    earnings_risk_score = sum(risk_factors)
    
    # Determine overall risk level
    if earnings_risk_score <= 20:
        overall_risk = "Low"
    elif earnings_risk_score <= 40:
        overall_risk = "Medium"
    else:
        overall_risk = "High"
    
    return {
        "symbol": symbol,
        "earnings_risk_score": earnings_risk_score,
        "overall_risk_level": overall_risk,
        "surprise_analysis": surprise_analysis,
        "revenue_analysis": revenue_analysis,
        "profitability_analysis": profitability_analysis,
        "guidance_analysis": guidance_analysis,
        "valuation_analysis": valuation_analysis,
        "earnings_data_available": "error" not in earnings_data,
        "last_updated": datetime.now().isoformat()
    }
