# app/routers/dividends.py
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List, Dict, Any

from app.core.security import get_current_user_id
from app.db import get_session
from app.models import DividendEvent, Holding, Portfolio
from app.services.dividends import (
    fetch_dividends,
    upsert_dividends,
    build_portfolio_income_calendar,
)

# Optional Celery trigger
try:
    from app.workers.tasks import refresh_dividends_for_all
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
    # Get holdings for this portfolio
    rows = session.exec(
        select(Holding.symbol)
        .where(Holding.portfolio_id == portfolio_id)
        .where(Holding.shares > 0)
    ).all()
    syms = _to_symbol_list(rows)
    
    if not syms:
        # Return empty result - portfolio has no holdings
        return {"portfolio_id": portfolio_id, "symbols": [], "inserted": 0, "per_symbol": {}}
    
    # Sync dividends for each symbol
    totals = 0
    per_symbol = {}
    print(f"[Sync] Starting dividend sync for portfolio {portfolio_id} with symbols: {syms}")
    
    for s in syms:
        try:
            print(f"[Sync] Fetching dividends for {s}...")
            dividend_events = fetch_dividends(s)
            print(f"[Sync] fetch_dividends returned {len(dividend_events)} events for {s}")
            
            if dividend_events:
                print(f"[Sync] Upserting {len(dividend_events)} events for {s}...")
                n = upsert_dividends(session, dividend_events)
                print(f"[Sync] Inserted {n} new events for {s} (some may have been duplicates)")
                totals += n
                per_symbol[s] = n
            else:
                print(f"[Sync] No dividend events found for {s}")
                per_symbol[s] = 0
        except Exception as e:
            # Log error but continue with other symbols
            print(f"[Sync] Exception fetching dividends for {s}: {e}")
            import traceback
            traceback.print_exc()
            per_symbol[s] = 0
    
    print(f"[Sync] Total inserted: {totals} events across {len(syms)} symbols")
    
    # Commit all dividend events
    session.commit()
    
    return {"portfolio_id": portfolio_id, "symbols": syms, "inserted": totals, "per_symbol": per_symbol}


@router.get("/calendar")
def calendar(
    user_id: str = Depends(get_current_user_id),
    session: Session = Depends(get_session)
):
    """Get dividend calendar for the current user's portfolios."""
    try:
        events = build_portfolio_income_calendar(user_id=user_id, session=session)
        return {"events": events}
    except Exception as e:
        # Log the error for debugging
        import traceback
        print(f"Error in calendar endpoint: {e}")
        print(traceback.format_exc())
        # Return empty events instead of crashing
        return {"events": []}

# optional: enqueue the full refresh via Celery
@router.post("/sync/enqueue-nightly")
def enqueue_nightly():
    if not HAVE_CELERY:
        raise HTTPException(501, detail="Celery not configured.")
    res = refresh_dividends_for_all.delay()
    return {"task_id": res.id, "status": "queued"}
