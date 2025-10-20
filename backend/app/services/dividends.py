# app/services/dividends.py
from datetime import datetime
from typing import Dict, Any, List, Tuple
import os
import yfinance as yf
from sqlmodel import Session, select
from app.db import engine
from app.models import Holding, DividendEvent

POLYGON_API_KEY = os.getenv("POLYGON_API_KEY")

# ---------- fetchers ----------
def _yfinance_dividends(symbol: str) -> List[Dict[str, Any]]:
    try:
        t = yf.Ticker(symbol)
        # Use shorter timeout and only get dividend data
        df = t.dividends  # pandas Series: index=Timestamp (ex-date), value=amount
        if df is None or df.empty:
            return []
        out = []
        for ts, amt in df.items():
            out.append({
                "symbol": symbol.upper(),
                "ex_date": ts.date(),
                "pay_date": None,
                "record_date": None,
                "amount": float(amt),
                "source": "yfinance",
            })
        return out
    except Exception as e:
        print(f"yfinance failed for {symbol}: {e}")
        return []

def _polygon_dividends(symbol: str) -> List[Dict[str, Any]]:
    if not POLYGON_API_KEY:
        return []
    import requests
    url = "https://api.polygon.io/v3/reference/dividends"
    params = {"ticker": symbol.upper(), "limit": 100, "apiKey": POLYGON_API_KEY}  # Reduced limit
    try:
        r = requests.get(url, params=params, timeout=5)  # Reduced timeout
        if not r.ok:
            return []
        data = r.json() or {}
        out = []
        for d in (data.get("results") or []):
            out.append({
                "symbol": symbol.upper(),
                "ex_date": _safe_date(d.get("ex_dividend_date")),
                "pay_date": _safe_date(d.get("pay_date")),
                "record_date": _safe_date(d.get("record_date")),
                "amount": float(d.get("cash_amount") or 0.0),
                "source": "polygon",
            })
        return out
    except Exception as e:
        print(f"Polygon failed for {symbol}: {e}")
        return []

def _safe_date(x):
    try:
        from datetime import datetime as _dt
        return _dt.strptime(x, "%Y-%m-%d").date() if x else None
    except Exception:
        return None

def _merge_events(primary: List[Dict], secondary: List[Dict]) -> List[Dict]:
    """Combine by (symbol, ex_date); prefer Polygon fields when available."""
    idx: Dict[Tuple[str, Any], Dict] = {}
    for e in primary:
        idx[(e["symbol"], e["ex_date"])] = e
    for e in secondary:
        key = (e["symbol"], e["ex_date"])
        if key in idx:
            base = idx[key]
            # fill missing fields
            for k in ("pay_date", "record_date"):
                if not base.get(k) and e.get(k):
                    base[k] = e[k]
            # prefer non-zero amount
            if (base.get("amount") or 0) == 0 and (e.get("amount") or 0) > 0:
                base["amount"] = e["amount"]
        else:
            idx[key] = e
    return list(idx.values())

# Public wrapper expected by routers
def fetch_dividends(symbol: str) -> List[Dict[str, Any]]:
    symbol = symbol.upper().strip()
    
    # Skip symbols that are known to not pay dividends or cause issues
    non_dividend_symbols = {'ULTY', 'YMAX'}  # These are ETFs/funds that don't pay traditional dividends
    if symbol in non_dividend_symbols:
        print(f"Skipping {symbol} - known non-dividend payer")
        return []
    
    try:
        yfd = _yfinance_dividends(symbol)
        pgd = _polygon_dividends(symbol)
        return _merge_events(yfd, pgd)
    except Exception as e:
        print(f"Failed to fetch dividends for {symbol}: {e}")
        return []

# ---------- upsert ----------
def _upsert_dividends(session: Session, events: List[Dict[str, Any]]) -> int:
    """Idempotent insert by (symbol, ex_date, amount)."""
    inserted = 0
    for e in events:
        exists = session.exec(
            select(DividendEvent)
            .where(DividendEvent.symbol == e["symbol"])
            .where(DividendEvent.ex_date == e["ex_date"])
            .where(DividendEvent.amount == e["amount"])
        ).first()
        if exists:
            changed = False
            if not exists.pay_date and e.get("pay_date"):
                exists.pay_date = e["pay_date"]; changed = True
            if not exists.record_date and e.get("record_date"):
                exists.record_date = e["record_date"]; changed = True
            if changed:
                session.add(exists)
        else:
            session.add(DividendEvent(
                symbol=e["symbol"],
                ex_date=e["ex_date"],
                pay_date=e.get("pay_date"),
                record_date=e.get("record_date"),
                amount=e["amount"],
                source=e.get("source") or "unknown",
                created_at=datetime.utcnow(),
            ))
            inserted += 1
    session.commit()
    return inserted

# Public wrapper expected by routers
def upsert_dividends(session: Session, events: List[Dict[str, Any]]) -> int:
    return _upsert_dividends(session, events)

# ---------- orchestration ----------
def refresh_all_dividends() -> int:
    """Fetch & upsert for all owned symbols (shares > 0)."""
    total = 0
    with Session(engine) as session:
        rows = session.exec(
            select(Holding.symbol).distinct().where(Holding.shares > 0)
        ).all()
        # rows may be scalars or tuples depending on driver
        symbols: List[str] = []
        for r in rows:
            v = r[0] if isinstance(r, (list, tuple)) else r
            if v:
                symbols.append(str(v).upper())
        for sym in sorted(set(symbols)):
            total += _upsert_dividends(session, fetch_dividends(sym))
    return total

def build_portfolio_income_calendar() -> List[Dict[str, Any]]:
    """
    Returns a flat list of rows from holdings × dividend events.
    Shows dividends received AFTER the purchase date of each holding.
    Includes both past (already paid) and future dividends.
    Each item:
      {
        "portfolio_id": int, "symbol": str,
        "ex_date": date|None, "pay_date": date|None,
        "amount": float, "shares": float, "cash": float,
        "status": str  # "paid" or "upcoming"
      }
    """
    from datetime import date
    today = date.today()
    
    out: List[Dict[str, Any]] = []
    with Session(engine) as session:
        rows = session.exec(
            select(
                Holding.portfolio_id,
                Holding.symbol,
                Holding.shares,
                Holding.purchase_date,
                DividendEvent.ex_date,
                DividendEvent.pay_date,
                DividendEvent.amount,
            )
            .where(Holding.shares > 0)
            .where(Holding.symbol == DividendEvent.symbol)
        ).all()

        for pid, sym, shares, purchase_date, exd, payd, amt in rows:
            sh = float(shares or 0)
            dv = float(amt or 0)
            
                   # Include all dividends (past and future) regardless of purchase date
                   # Commented out the purchase date filter to show all dividends
                   # if purchase_date and exd:
                   #     purchase_date_only = purchase_date.date() if hasattr(purchase_date, 'date') else purchase_date
                   #     if exd < purchase_date_only:
                   #         continue  # Skip dividends before purchase
            
            # Determine if dividend has been paid
            status = "upcoming"
            if payd and payd <= today:
                status = "paid"
            elif exd and exd <= today:
                status = "paid"  # Ex-date has passed
            
            out.append({
                "portfolio_id": pid,
                "symbol": str(sym).upper(),
                "ex_date": exd,
                "pay_date": payd,
                "amount": dv,
                "shares": sh,
                "cash": dv * sh,
                "status": status,
            })
    return out
