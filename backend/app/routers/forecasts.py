from fastapi import APIRouter
from sqlmodel import Session
from app.db import engine
from app.services.forecast import monthly_cashflow_forecast
from pydantic import BaseModel
from typing import Optional
from datetime import date

router = APIRouter(tags=["forecasts"])

class ForecastRequest(BaseModel):
    portfolio_id: int
    months: int = 12
    assume_reinvest: bool = True
    recurring_deposit: float = 0.0
    deposit_freq: str = "monthly"
    start_date: Optional[date] = None
    growth_scenario: str = "moderate"  # conservative, moderate, optimistic, pessimistic

@router.post("/monthly")
def forecast(req: ForecastRequest):
    with Session(engine) as session:
        return monthly_cashflow_forecast(session, **req.dict())
