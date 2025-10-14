# app/routers/dividends.py
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List, Dict, Any

from app.db import get_session
from app.models import DividendEvent, Holding
from app.services.dividends import (   # <-- absolute
    fetch_dividends,
    upsert_dividends,
    build_portfolio_income_calendar,
)

# Optional Celery trigger
try:
    from app.workers.tasks import refresh_dividends_for_all  # <-- absolute
    HAVE_CELERY = True
except Exception:
    HAVE_CELERY = False

router = APIRouter(tags=["dividends"])

# app/routers/dividends.py (add near top, after router=...)
def _to_symbol_list(rows):
    out = []
    for r in rows:
        v = r[0] if isinstance(r, (list, tuple)) else r
        if v:
            out.append(str(v).upper().strip())
    return sorted(set(out))

@router.post("/sync/all")
def sync_all_symbols(session: Session = Depends(get_session)):
    rows = session.exec(
        select(Holding.symbol).where(Holding.shares > 0)
    ).all()
    syms = _to_symbol_list(rows)
    totals = 0
    per_symbol = {}
    for s in syms:
        n = upsert_dividends(session, fetch_dividends(s) or [])
        totals += n
        per_symbol[s] = n
    return {"symbols": syms, "inserted": totals, "per_symbol": per_symbol}

@router.post("/sync/portfolio/{portfolio_id}")
def sync_portfolio(portfolio_id: int, session: Session = Depends(get_session)):
    rows = session.exec(
        select(Holding.symbol)
        .where(Holding.portfolio_id == portfolio_id)
        .where(Holding.shares > 0)
    ).all()
    syms = _to_symbol_list(rows)
    if not syms:
        raise HTTPException(status_code=404, detail="No symbols found for this portfolio.")
    totals = 0
    per_symbol = {}
    for s in syms:
        n = upsert_dividends(session, fetch_dividends(s) or [])
        totals += n
        per_symbol[s] = n
    return {"portfolio_id": portfolio_id, "symbols": syms, "inserted": totals, "per_symbol": per_symbol}

@router.post("/sync/all")
def sync_all_symbols(session: Session = Depends(get_session)):
    rows = session.exec(
       select(Holding.symbol).where(Holding.shares > 0)
    ).all()
    syms = _to_symbol_list(rows)
    totals = 0
    per_symbol: Dict[str, int] = {}
    for s in syms:
        n = upsert_dividends(session, fetch_dividends(s) or [])
        totals += n
        per_symbol[s] = n
    return {"symbols": syms, "inserted": totals, "per_symbol": per_symbol}

@router.get("/calendar")
def calendar():
    """Precomputed on sync; or build on the fly if your service does it ad-hoc."""
    return {"events": build_portfolio_income_calendar()}

# optional: enqueue the full refresh via Celery
@router.post("/sync/enqueue-nightly")
def enqueue_nightly():
    if not HAVE_CELERY:
        raise HTTPException(501, detail="Celery not configured.")
    res = refresh_dividends_for_all.delay()
    return {"task_id": res.id, "status": "queued"}
