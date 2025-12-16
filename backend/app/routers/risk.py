# backend/app/routers/risk.py
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from app.db import get_session
from app.services.risk_analysis import generate_risk_report
from typing import Dict, Any

router = APIRouter(tags=["risk"])

@router.get("/analysis/{portfolio_id}")
def get_risk_analysis(portfolio_id: int, session: Session = Depends(get_session)) -> Dict[str, Any]:
    """Get comprehensive risk analysis for a portfolio"""
    try:
        risk_report = generate_risk_report(session, portfolio_id)
        
        if "error" in risk_report:
            # Return empty/error response instead of raising exception
            return {
                "error": risk_report["error"],
                "portfolio_id": portfolio_id,
                "has_holdings": False
            }
        
        # Ensure has_holdings is set for mobile app
        risk_report["has_holdings"] = True
        return risk_report
    
    except Exception as e:
        # Log error but return graceful response
        import traceback
        print(f"Error in risk analysis: {e}")
        print(traceback.format_exc())
        return {
            "error": "Unable to generate risk analysis",
            "portfolio_id": portfolio_id,
            "has_holdings": False
        }

@router.get("/metrics/{portfolio_id}")
def get_risk_metrics(portfolio_id: int, session: Session = Depends(get_session)) -> Dict[str, Any]:
    """Get basic risk metrics for a portfolio"""
    try:
        risk_report = generate_risk_report(session, portfolio_id)
        
        if "error" in risk_report:
            # Return empty/error response instead of raising exception
            return {
                "error": risk_report["error"],
                "portfolio_id": portfolio_id,
                "has_holdings": False
            }
        
        # Return only the key metrics
        return {
            "portfolio_id": portfolio_id,
            "has_holdings": True,  # Important: mobile app checks this!
            "risk_score": risk_report["risk_score"],
            "overall_risk_level": risk_report["overall_risk_level"],
            "volatility": risk_report["volatility"],
            "beta": risk_report["beta"],
            "sharpe_ratio": risk_report["sharpe_ratio"],
            "max_drawdown": risk_report["max_drawdown"],
            "var_95": risk_report["var_95"],
            "concentration_risk": risk_report["concentration"]["max_weight"],
            "concentration": risk_report["concentration"]  # Include full concentration data for top holdings
        }
    
    except Exception as e:
        # Log error but return graceful response
        import traceback
        print(f"Error in risk metrics: {e}")
        print(traceback.format_exc())
        return {
            "error": "Unable to generate risk metrics",
            "portfolio_id": portfolio_id,
            "has_holdings": False
        }
