# backend/app/services/symbols.py
import os, requests
from typing import List, Dict

POLYGON_API_KEY = os.getenv("POLYGON_API_KEY")
ALPHA_KEY = os.getenv("ALPHAVANTAGE_API_KEY")

def _polygon_search(query: str, limit: int) -> List[Dict]:
    if not POLYGON_API_KEY or not query.strip():
        return []
    url = "https://api.polygon.io/v3/reference/tickers"
    params = {"search": query.strip(), "active":"true", "market":"stocks", "limit":limit, "apiKey": POLYGON_API_KEY}
    r = requests.get(url, params=params, timeout=6)
    if not r.ok:
        return []
    data = r.json()
    results = data.get("results") or []
    out = []
    for x in results:
        out.append({
            "symbol": x.get("ticker"),
            "name": x.get("name"),
            "primary_exchange": x.get("primary_exchange"),
            "locale": x.get("locale"),
            "source": "polygon"
        })
    return out

def _alpha_search(query: str, limit: int) -> List[Dict]:
    if not ALPHA_KEY or not query.strip():
        return []
    url = "https://www.alphavantage.co/query"
    r = requests.get(url, params={"function":"SYMBOL_SEARCH","keywords":query.strip(),"apikey":ALPHA_KEY}, timeout=8)
    if not r.ok:
        return []
    data = r.json() or {}
    matches = data.get("bestMatches") or []
    out = []
    for m in matches[:limit]:
        out.append({
            "symbol": m.get("1. symbol"),
            "name": m.get("2. name"),
            "primary_exchange": m.get("4. region"),  # AV doesn't give exchange cleanly; region is still helpful
            "locale": m.get("4. region"),
            "source": "alphavantage"
        })
    return out

def search_symbols_polygon(query: str, limit: int = 15) -> List[Dict]:
    # Try Polygon, then Alpha Vantage
    res = _polygon_search(query, limit)
    if res:
        return res
    return _alpha_search(query, limit)
