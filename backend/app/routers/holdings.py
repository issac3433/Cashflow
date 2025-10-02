from fastapi import APIRouter, Query
from sqlmodel import Session, select
from pydantic import BaseModel
from ..db import engine
from ..models import Holding, Price
from ..services.prices import fetch_latest_price, batch_fetch_latest_prices
from datetime import date

router = APIRouter(prefix="/holdings", tags=["holdings"])

class HoldingCreate(BaseModel):
    portfolio_id: int
    symbol: str
    shares: float
    avg_price: float | None = None  # None or <=0 ⇒ auto-fill with latest price
    reinvest_dividends: bool = True

@router.get("")
def list_holdings(portfolio_id: int = Query(...)):
    with Session(engine) as session:
        rows = session.exec(select(Holding).where(Holding.portfolio_id == portfolio_id)).all()
        return rows

@router.get("/with-quotes")
def list_with_quotes(portfolio_id: int = Query(...)):
    with Session(engine) as session:
        rows = session.exec(select(Holding).where(Holding.portfolio_id == portfolio_id)).all()
        syms = [r.symbol for r in rows]
        quotes = batch_fetch_latest_prices(syms) if syms else {}
        out = []
        for r in rows:
            sym = (r.symbol or "").upper()
            lp = quotes.get(sym)
            out.append({
                "id": r.id,
                "portfolio_id": r.portfolio_id,
                "symbol": sym,
                "shares": r.shares,
                "avg_price": r.avg_price,
                "reinvest_dividends": r.reinvest_dividends,
                "latest_price": lp,
                "market_value": (lp or 0.0) * r.shares,
            })
        return out

@router.post("")
def add(h: HoldingCreate):
    sym = h.symbol.upper().strip()
    px = h.avg_price
    # If avg_price not provided or invalid → fetch latest
    if px is None or px <= 0:
        latest = fetch_latest_price(sym)
        px = latest if latest is not None else 0.0

    with Session(engine) as session:
        obj = Holding(
            portfolio_id=h.portfolio_id,
            symbol=sym,
            shares=h.shares,
            avg_price=float(px),
            reinvest_dividends=h.reinvest_dividends,
        )
        session.add(obj)
        if px and px > 0:
            session.add(Price(symbol=sym, date=date.today(), close=float(px)))
        session.commit()
        session.refresh(obj)
        return {"holding": obj, "quote_used": float(px)}
