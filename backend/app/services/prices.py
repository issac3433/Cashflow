# backend/app/services/prices.py
import os, time, requests, yfinance as yf
from typing import Optional, Iterable, Dict

POLYGON_API_KEY = os.getenv("POLYGON_API_KEY")
ALPHA_KEY = os.getenv("ALPHAVANTAGE_API_KEY")

# tiny in-process cache to soften free-plan rate limits
_cache: Dict[str, tuple[float, Optional[float]]] = {}
TTL_SECONDS = 60  # 1 minute cache for quotes

def _get_cached(sym: str) -> Optional[float]:
    now = time.time()
    hit = _cache.get(sym)
    if hit and (now - hit[0]) < TTL_SECONDS:
        return hit[1]
    return None

def _set_cached(sym: str, val: Optional[float]) -> None:
    _cache[sym] = (time.time(), val)

def _polygon_prev_close(symbol: str) -> Optional[float]:
    if not POLYGON_API_KEY: return None
    s = symbol.upper().strip().replace("$", "")
    url = f"https://api.polygon.io/v2/aggs/ticker/{s}/prev"
    try:
        r = requests.get(url, params={"adjusted":"true","apiKey":POLYGON_API_KEY}, timeout=6)
        if not r.ok: return None
        data = r.json()
        res = (data.get("results") or [])
        if res: return float(res[0]["c"])
    except Exception as e:
        print(f"[Polygon prev-close] {s}: {e}")
    return None

def _alpha_global_quote(symbol: str) -> Optional[float]:
    """Alpha Vantage GLOBAL_QUOTE — free-plan friendly. Field '05. price' or '08. previous close'."""
    if not ALPHA_KEY: return None
    s = symbol.upper().strip().replace("$", "")
    url = "https://www.alphavantage.co/query"
    try:
        r = requests.get(url, params={"function":"GLOBAL_QUOTE","symbol":s,"apikey":ALPHA_KEY}, timeout=8)
        if not r.ok: return None
        data = r.json() or {}
        gq = data.get("Global Quote") or {}
        px = gq.get("05. price") or gq.get("08. previous close")
        if px:
            v = float(px)
            return v if v > 0 else None
    except Exception as e:
        print(f"[AlphaVantage GLOBAL_QUOTE] {s}: {e}")
    return None

def _yf_close(symbol: str) -> Optional[float]:
    s = symbol.upper().strip().replace("$", "")
    try:
        t = yf.Ticker(s)
        for period in ["1d","5d"]:
            hist = t.history(period=period, interval="1d")
            if hist is not None and not hist.empty:
                v = float(hist["Close"].dropna().iloc[-1])
                return v if v > 0 else None
    except Exception as e:
        print(f"[yfinance] {s}: {e}")
    return None

def fetch_latest_price(symbol: str) -> Optional[float]:
    s = symbol.upper().strip().replace("$","")
    # cache first
    cv = _get_cached(s)
    if cv is not None:
        return cv

    # 1) Polygon prev close
    v = _polygon_prev_close(s)
    if v is not None:
        _set_cached(s, v); return v

    # 2) Alpha Vantage GLOBAL_QUOTE
    v = _alpha_global_quote(s)
    if v is not None:
        _set_cached(s, v); return v

    # 3) yfinance fallback
    v = _yf_close(s)
    _set_cached(s, v)
    return v

def batch_fetch_latest_prices(symbols: Iterable[str]) -> Dict[str, Optional[float]]:
    out: Dict[str, Optional[float]] = {}
    for sym in { (sym or "").upper().strip().replace("$","") for sym in symbols }:
        out[sym] = fetch_latest_price(sym)
    return out
