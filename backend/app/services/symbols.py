# backend/app/services/symbols.py
import os, requests, time
from typing import List, Dict

POLYGON_API_KEY = os.getenv("POLYGON_API_KEY")
ALPHA_KEY = os.getenv("ALPHAVANTAGE_API_KEY")

# Enhanced cache with longer TTL for free tier
_search_cache: Dict[str, tuple[float, List[Dict]]] = {}
CACHE_TTL = 1800  # 30 minutes cache for free tier (reduce API calls)

def _get_cached_search(query: str) -> List[Dict]:
    now = time.time()
    cache_key = f"{query.lower()}"
    hit = _search_cache.get(cache_key)
    if hit and (now - hit[0]) < CACHE_TTL:
        return hit[1]
    return None

def _set_cached_search(query: str, results: List[Dict]) -> None:
    cache_key = f"{query.lower()}"
    _search_cache[cache_key] = (time.time(), results)

def _polygon_search(query: str, limit: int) -> List[Dict]:
    if not POLYGON_API_KEY or not query.strip():
        return []
    url = "https://api.polygon.io/v3/reference/tickers"
    params = {"search": query.strip(), "active":"true", "market":"stocks", "limit":limit, "apiKey": POLYGON_API_KEY}
    try:
        r = requests.get(url, params=params, timeout=6)
        if not r.ok:
            if r.status_code == 429:
                print(f"[Polygon] Rate limit exceeded (429) for query: {query}")
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
    except Exception as e:
        print(f"[Polygon] Error for query '{query}': {e}")
        return []

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
    # Check cache first
    cached = _get_cached_search(query)
    if cached is not None:
        return cached[:limit]
    
    # Try Alpha Vantage FIRST (more generous free tier), then Polygon
    res = _alpha_search(query, limit)
    if res:
        _set_cached_search(query, res)
        return res
    
    # Only try Polygon if Alpha Vantage fails
    res = _polygon_search(query, limit)
    if res:
        _set_cached_search(query, res)
        return res
    
    # Fallback: if no API keys, rate limits hit, or both fail, return some basic matches
    if not POLYGON_API_KEY and not ALPHA_KEY:
        # Basic fallback with common stocks
        fallback_symbols = {
            "AAPL": "Apple Inc.",
            "MSFT": "Microsoft Corporation", 
            "GOOGL": "Alphabet Inc.",
            "TSLA": "Tesla Inc.",
            "NVDA": "NVIDIA Corporation",
            "AMZN": "Amazon.com Inc.",
            "META": "Meta Platforms Inc.",
            "NFLX": "Netflix Inc.",
            "AMD": "Advanced Micro Devices Inc.",
            "INTC": "Intel Corporation",
            "JPM": "JPMorgan Chase & Co.",
            "JNJ": "Johnson & Johnson",
            "V": "Visa Inc.",
            "PG": "Procter & Gamble Co.",
            "UNH": "UnitedHealth Group Inc."
        }
        
        query_upper = query.strip().upper()
        matches = []
        
        # First try exact symbol matches
        if query_upper in fallback_symbols:
            matches.append({
                "symbol": query_upper,
                "name": fallback_symbols[query_upper],
                "primary_exchange": "NASDAQ",
                "source": "fallback_exact"
            })
        
        # Then try partial matches
        for symbol, name in fallback_symbols.items():
            if query_upper in symbol or query_upper in name.upper():
                if symbol not in [m["symbol"] for m in matches]:  # Avoid duplicates
                    matches.append({
                        "symbol": symbol,
                        "name": name,
                        "primary_exchange": "NASDAQ",
                        "source": "fallback"
                    })
        
        fallback_results = matches[:limit]
        _set_cached_search(query, fallback_results)
        return fallback_results
    
    return []
