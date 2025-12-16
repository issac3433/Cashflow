# app/services/dividends.py
from datetime import datetime
from typing import Dict, Any, List, Tuple, Optional
import os
import yfinance as yf
from sqlmodel import Session, select
from app.db import engine
from app.models import Holding, DividendEvent, Portfolio

POLYGON_API_KEY = os.getenv("POLYGON_API_KEY")

# ---------- fetchers ----------
def _yfinance_dividends(symbol: str) -> List[Dict[str, Any]]:
    try:
        t = yf.Ticker(symbol)
        out = []
        
        # Try dividends first (works for most stocks)
        try:
            df = t.dividends  # pandas Series: index=Timestamp (ex-date), value=amount
            if df is not None and not df.empty:
                for ts, amt in df.items():
                    out.append({
                        "symbol": symbol.upper(),
                        "ex_date": ts.date() if hasattr(ts, 'date') else ts,
                        "pay_date": None,
                        "record_date": None,
                        "amount": float(amt),
                        "source": "yfinance",
                    })
                print(f"[Dividends] yfinance: Found {len(out)} dividend events from dividends field for {symbol}")
        except Exception as e:
            print(f"[Dividends] yfinance dividends field failed for {symbol}: {e}")
        
        # For ETFs and some stocks, dividends might be in actions (capital gains + dividends)
        if not out:
            try:
                actions = t.actions  # DataFrame with Dividends and Capital Gains
                if actions is not None and not actions.empty and 'Dividends' in actions.columns:
                    for idx, row in actions.iterrows():
                        div_amt = row.get('Dividends', 0)
                        if div_amt and div_amt > 0:
                            out.append({
                                "symbol": symbol.upper(),
                                "ex_date": idx.date() if hasattr(idx, 'date') else idx,
                                "pay_date": None,
                                "record_date": None,
                                "amount": float(div_amt),
                                "source": "yfinance_actions",
                            })
                    print(f"[Dividends] yfinance: Found {len(out)} dividend events from actions field for {symbol}")
            except Exception as e:
                print(f"[Dividends] yfinance actions field failed for {symbol}: {e}")
        
        # Also try stock_splits and other fields that might contain dividend info
        if not out:
            try:
                # Some ETFs report dividends differently - try info
                info = t.info
                if info and 'dividendRate' in info and info.get('dividendRate', 0) > 0:
                    # If we have dividend rate but no historical data, create a placeholder
                    print(f"[Dividends] yfinance: {symbol} has dividend rate {info.get('dividendRate')} but no historical data")
            except Exception as e:
                print(f"[Dividends] yfinance info check failed for {symbol}: {e}")
        
        if not out:
            print(f"[Dividends] yfinance: No dividend data found for {symbol} (tried dividends, actions, info)")
        
        return out
    except Exception as e:
        print(f"[Dividends] yfinance exception for {symbol}: {e}")
        import traceback
        traceback.print_exc()
        return []

def _polygon_dividends(symbol: str) -> List[Dict[str, Any]]:
    if not POLYGON_API_KEY:
        print(f"[Dividends] Polygon API key not configured - check your .env file")
        return []
    
    import requests
    url = "https://api.polygon.io/v3/reference/dividends"
    params = {"ticker": symbol.upper(), "limit": 100, "apiKey": POLYGON_API_KEY}
    
    print(f"[Dividends] Calling Polygon API for {symbol}...")
    try:
        r = requests.get(url, params=params, timeout=10)
        print(f"[Dividends] Polygon API response status: {r.status_code}")
        
        if not r.ok:
            print(f"[Dividends] Polygon API error for {symbol}: HTTP {r.status_code}")
            print(f"[Dividends] Response: {r.text[:200]}")
            if r.status_code == 429:
                print(f"[Dividends] Polygon rate limit exceeded")
            elif r.status_code == 401:
                print(f"[Dividends] Polygon authentication failed - check API key")
            return []
        
        data = r.json() or {}
        results = data.get("results") or []
        print(f"[Dividends] Polygon returned {len(results)} raw results for {symbol}")
        
        out = []
        for d in results:
            cash_amount = d.get("cash_amount") or 0.0
            if cash_amount > 0:  # Only include events with actual dividend amounts
                out.append({
                    "symbol": symbol.upper(),
                    "ex_date": _safe_date(d.get("ex_dividend_date")),
                    "pay_date": _safe_date(d.get("pay_date")),
                    "record_date": _safe_date(d.get("record_date")),
                    "amount": float(cash_amount),
                    "source": "polygon",
                })
        
        print(f"[Dividends] Polygon processed {len(results)} results, {len(out)} valid events for {symbol}")
        if len(out) == 0 and len(results) > 0:
            print(f"[Dividends] Warning: Polygon returned results but all had $0 amounts")
        
        return out
    except Exception as e:
        print(f"[Dividends] Polygon exception for {symbol}: {e}")
        import traceback
        traceback.print_exc()
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
        print(f"[Dividends] Skipping {symbol} - known non-dividend payer")
        return []
    
    pgd = []
    yfd = []
    
    # Try both APIs - Polygon for better structured data, yfinance as fallback
    # For ETFs and niche stocks, yfinance is often more reliable
    import concurrent.futures
    
    # Try both in parallel for faster results
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        polygon_future = executor.submit(_polygon_dividends, symbol)
        yfinance_future = executor.submit(_yfinance_dividends, symbol)
        
        # Wait for both with timeout
        try:
            pgd = polygon_future.result(timeout=8)
            print(f"[Dividends] Polygon found {len(pgd)} events for {symbol}")
        except Exception as e:
            print(f"[Dividends] Polygon failed for {symbol}: {e}")
            pgd = []
        
        try:
            yfd = yfinance_future.result(timeout=8)
            print(f"[Dividends] yfinance found {len(yfd)} events for {symbol}")
        except Exception as e:
            print(f"[Dividends] yfinance failed for {symbol}: {e}")
            yfd = []
    
    # Prefer Polygon if it has results (better data quality with pay dates)
    if pgd:
        print(f"[Dividends] Using Polygon data for {symbol}: {len(pgd)} events")
        return pgd
    
    # Use yfinance if Polygon had nothing
    if yfd:
        print(f"[Dividends] Using yfinance data for {symbol}: {len(yfd)} events")
        return yfd
    
    # Neither API found data
    print(f"[Dividends] No dividend data found for {symbol} from any API")
    return []

# ---------- upsert ----------
def _upsert_dividends(session: Session, events: List[Dict[str, Any]], commit: bool = True) -> int:
    """Idempotent insert by (symbol, ex_date, amount)."""
    inserted = 0
    for e in events:
        # Ensure symbol is uppercase for consistency
        symbol_upper = str(e["symbol"]).upper().strip() if e.get("symbol") else None
        if not symbol_upper:
            print(f"[Dividends] Skipping event with no symbol: {e}")
            continue
            
        exists = session.exec(
            select(DividendEvent)
            .where(DividendEvent.symbol == symbol_upper)
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
                symbol=symbol_upper,
                ex_date=e["ex_date"],
                pay_date=e.get("pay_date"),
                record_date=e.get("record_date"),
                amount=e["amount"],
                source=e.get("source") or "unknown",
                created_at=datetime.utcnow(),
            ))
            inserted += 1
    if commit:
        session.commit()
    return inserted

# Public wrapper expected by routers
def upsert_dividends(session: Session, events: List[Dict[str, Any]], commit: bool = True) -> int:
    return _upsert_dividends(session, events, commit=commit)

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
            total += _upsert_dividends(session, fetch_dividends(sym), commit=True)
    return total

def build_portfolio_income_calendar(user_id: Optional[str] = None, session: Optional[Session] = None) -> List[Dict[str, Any]]:
    """
    Returns a flat list of rows from holdings × dividend events.
    Shows dividends from 6 months before purchase date to future.
    Includes both past (already paid) and future dividends.
    Each item:
      {
        "portfolio_id": int, "symbol": str,
        "ex_date": date|None, "pay_date": date|None,
        "amount": float, "shares": float, "cash": float,
        "status": str  # "paid" or "upcoming"
      }
    
    Args:
        user_id: Filter by user_id. If None, returns all users (for backwards compatibility).
        session: Database session. If None, creates a new session.
    """
    from datetime import date
    today = date.today()
    
    out: List[Dict[str, Any]] = []
    
    # Use provided session or create a new one
    if session is None:
        session_context = Session(engine)
        should_close = True
    else:
        session_context = session
        should_close = False
    
    try:
        # First, get portfolio IDs for this user if filtering by user_id
        portfolio_ids = None
        if user_id:
            try:
                user_portfolios = session_context.exec(
                    select(Portfolio).where(Portfolio.user_id == user_id)
                ).all()
                portfolio_ids = [p.id for p in user_portfolios]
                if not portfolio_ids:
                    # User has no portfolios, return empty list gracefully
                    print(f"[Calendar] User {user_id} has no portfolios")
                    return []
                print(f"[Calendar] Found {len(portfolio_ids)} portfolios for user {user_id}: {portfolio_ids}")
            except Exception as e:
                print(f"Error fetching user portfolios: {e}")
                import traceback
                traceback.print_exc()
                return []
        
        # Build query - join holdings with dividend events by symbol
        try:
            # Get all holdings for this user's portfolios first
            holdings_query = select(Holding).where(Holding.shares > 0)
            if portfolio_ids is not None and len(portfolio_ids) > 0:
                holdings_query = holdings_query.where(Holding.portfolio_id.in_(portfolio_ids))
            
            holdings = session_context.exec(holdings_query).all()
            
            if not holdings:
                # No holdings, return empty list
                return []
            
            # Get unique symbols from holdings
            symbols = list(set([h.symbol.upper() for h in holdings if h.symbol]))
            
            print(f"[Calendar] Found {len(holdings)} holdings with {len(symbols)} unique symbols: {symbols}")
            
            if not symbols:
                # No symbols, return empty list
                print("[Calendar] No symbols found in holdings")
                return []
            
            # Get dividend events for these symbols from the database
            # Query using uppercase symbols to match how they're stored
            # Ensure all symbols are uppercase for the query
            symbols_upper = [s.upper() if s else s for s in symbols]
            dividend_events = session_context.exec(
                select(DividendEvent).where(DividendEvent.symbol.in_(symbols_upper))
            ).all()
            
            # Debug: Also check what symbols are actually in the database
            all_db_symbols = session_context.exec(
                select(DividendEvent.symbol).distinct()
            ).all()
            db_symbols_set = set([s.upper() for s in all_db_symbols if s])
            print(f"[Calendar] Symbols in dividend_events table: {db_symbols_set}")
            print(f"[Calendar] Looking for symbols: {symbols_upper}")
            print(f"[Calendar] Matching symbols: {db_symbols_set.intersection(set(symbols_upper))}")
            
            print(f"[Calendar] Found {len(dividend_events)} dividend events in database for symbols: {symbols_upper}")
            
            # Log events by symbol for debugging
            events_by_symbol_count = {}
            for event in dividend_events:
                sym = event.symbol.upper()
                events_by_symbol_count[sym] = events_by_symbol_count.get(sym, 0) + 1
            print(f"[Calendar] Dividend events by symbol: {events_by_symbol_count}")
            
            # Create a map of symbol -> dividend events
            events_by_symbol = {}
            for event in dividend_events:
                sym = event.symbol.upper()
                if sym not in events_by_symbol:
                    events_by_symbol[sym] = []
                events_by_symbol[sym].append(event)
            
            # Build result by combining holdings with their dividend events
            from datetime import timedelta
            total_events_added = 0
            for holding in holdings:
                try:
                    sym = holding.symbol.upper()
                    events = events_by_symbol.get(sym, [])
                    print(f"[Calendar] Processing {sym}: {len(events)} events found")
                    
                    # Calculate 6 months before purchase date
                    purchase_date = holding.purchase_date
                    six_months_prior = None
                    
                    if purchase_date:
                        try:
                            # Convert to date if it's a datetime
                            if hasattr(purchase_date, 'date'):
                                purchase_date_only = purchase_date.date()
                            elif isinstance(purchase_date, str):
                                # Handle string dates
                                from datetime import datetime as dt
                                purchase_date_only = dt.fromisoformat(purchase_date.replace('Z', '+00:00')).date()
                            else:
                                purchase_date_only = purchase_date
                            
                            # Calculate 6 months prior (approximately 180 days)
                            six_months_prior = purchase_date_only - timedelta(days=180)
                        except Exception as e:
                            print(f"[Dividends] Error processing purchase_date for {sym}: {e}")
                            # If we can't parse purchase date, show all dividends
                            six_months_prior = None
                    
                    for event in events:
                        try:
                            sh = float(holding.shares or 0)
                            dv = float(event.amount or 0)
                            
                            if dv <= 0:
                                continue
                            
                            # Filter: Show dividends from 6 months before purchase to future
                            # Only filter if we have both dates
                            if six_months_prior is not None and event.ex_date is not None:
                                try:
                                    # Only show if ex_date is within our range (6 months prior to purchase, or after purchase)
                                    if event.ex_date < six_months_prior:
                                        continue  # Skip dividends too far in the past
                                except (TypeError, AttributeError) as e:
                                    # If date comparison fails, include the event anyway
                                    print(f"[Dividends] Date comparison error for {sym}: {e}")
                                    pass
                            
                            # Determine if dividend has been paid
                            status = "upcoming"
                            if event.pay_date and event.pay_date <= today:
                                status = "paid"
                            elif event.ex_date and event.ex_date <= today:
                                status = "paid"
                            
                            out.append({
                                "portfolio_id": holding.portfolio_id,
                                "symbol": sym,
                                "ex_date": event.ex_date.isoformat() if event.ex_date else None,
                                "pay_date": event.pay_date.isoformat() if event.pay_date else None,
                                "amount": dv,
                                "shares": sh,
                                "cash": dv * sh,
                                "status": status,
                            })
                            total_events_added += 1
                        except Exception as e:
                            print(f"[Dividends] Error processing event for {sym}: {e}")
                            import traceback
                            traceback.print_exc()
                            continue  # Skip this event and continue
                            
                except Exception as e:
                    print(f"[Dividends] Error processing holding {holding.symbol}: {e}")
                    import traceback
                    traceback.print_exc()
                    continue  # Skip this holding and continue
            
            print(f"[Calendar] Total events added to calendar: {total_events_added}")
            
            rows = []  # Not used anymore, but keeping for compatibility
        except Exception as e:
            print(f"Error executing dividend calendar query: {e}")
            # Return empty list if query fails
            return []

        # Process rows
        for row in rows:
            try:
                pid, sym, shares, purchase_date, exd, payd, amt = row
                sh = float(shares or 0)
                dv = float(amt or 0)
                
                # Skip if no dividend amount
                if dv <= 0:
                    continue
                
                # Determine if dividend has been paid
                status = "upcoming"
                if payd and payd <= today:
                    status = "paid"
                elif exd and exd <= today:
                    status = "paid"  # Ex-date has passed
                
                out.append({
                    "portfolio_id": pid,
                    "symbol": str(sym).upper() if sym else "",
                    "ex_date": exd.isoformat() if exd else None,
                    "pay_date": payd.isoformat() if payd else None,
                    "amount": dv,
                    "shares": sh,
                    "cash": dv * sh,
                    "status": status,
                })
            except Exception as e:
                print(f"Error processing dividend row: {e}")
                continue  # Skip this row and continue
                
    except Exception as e:
        print(f"Error in build_portfolio_income_calendar: {e}")
        import traceback
        print(traceback.format_exc())
        # Return empty list on any error
        return []
    finally:
        if should_close:
            session_context.close()
    
    return out
