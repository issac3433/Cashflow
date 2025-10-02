from fastapi import APIRouter
from sqlmodel import Session
from ..db import engine
from ..services.dividends import fetch_dividends_yf
from ..models import DividendEvent

router = APIRouter(prefix="/dividends", tags=["dividends"])

@router.post("/refresh/{symbol}")
def refresh_symbol(symbol: str):
    events = list(fetch_dividends_yf(symbol))
    with Session(engine) as session:
        for e in events:
            session.add(e)
        session.commit()
    return {"inserted": len(events)}
