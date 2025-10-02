# backend/app/routers/holdings_quotes.py
from fastapi import APIRouter, Query
from sqlmodel import Session, select
from ..db import engine
from ..models import Holding
from ..services.prices import batch_fetch_latest_prices

router = APIRouter(prefix="/holdings", tags=["holdings"])

@router.get("/with-quotes")
def list_with_quotes(portfolio_id: int = Query(...)):
    with Session(engine) as session:
        rows = session.exec(select(Holding).where(Holding.portfolio_id == portfolio_id)).all()
        syms = [r.symbol for r in rows]
        quotes = batch_fetch_latest_prices(syms) if syms else {}
        # shape rows enriched with latest_price
        out = []
        for r in rows:
            sym = (r.symbol or "").upper()
            out.append({
                "id": r.id,
                "portfolio_id": r.portfolio_id,
                "symbol": sym,
                "shares": r.shares,
                "avg_price": r.avg_price,
                "reinvest_dividends": r.reinvest_dividends,
                "latest_price": quotes.get(sym),
                "market_value": (quotes.get(sym) or 0.0) * r.shares,
            })
        return out
