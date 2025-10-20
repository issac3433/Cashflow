# backend/app/services/symbols.py
import os, requests, time
from typing import List, Dict
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

POLYGON_API_KEY = os.getenv("POLYGON_API_KEY")
ALPHA_KEY = os.getenv("ALPHAVANTAGE_API_KEY")

# Enhanced cache with longer TTL for free tier (5 calls/minute limit)
_search_cache: Dict[str, tuple[float, List[Dict]]] = {}
CACHE_TTL = 3600  # 1 hour cache for very limited free tier (5 calls/minute)

# API call tracking for rate limit monitoring
_api_call_tracker: List[float] = []  # Timestamps of API calls
MAX_CALLS_PER_MINUTE = 5

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

def _track_api_call() -> None:
    """Track an API call for rate limit monitoring."""
    now = time.time()
    _api_call_tracker.append(now)
    
    # Remove calls older than 1 minute
    cutoff = now - 60
    _api_call_tracker[:] = [call_time for call_time in _api_call_tracker if call_time > cutoff]

def _get_api_call_status() -> Dict[str, any]:
    """Get current API call status and rate limit info."""
    now = time.time()
    recent_calls = [call_time for call_time in _api_call_tracker if call_time > now - 60]
    
    calls_used = len(recent_calls)
    calls_remaining = max(0, MAX_CALLS_PER_MINUTE - calls_used)
    
    # Calculate time until next call is available
    time_until_reset = 0
    if calls_used >= MAX_CALLS_PER_MINUTE:
        oldest_call = min(recent_calls)
        time_until_reset = 60 - (now - oldest_call)
    
    return {
        "calls_used": calls_used,
        "calls_remaining": calls_remaining,
        "max_calls": MAX_CALLS_PER_MINUTE,
        "time_until_reset": max(0, time_until_reset),
        "is_rate_limited": calls_used >= MAX_CALLS_PER_MINUTE
    }

def _polygon_search(query: str, limit: int) -> List[Dict]:
    if not POLYGON_API_KEY or not query.strip():
        return []
    
    # Check if we're rate limited
    status = _get_api_call_status()
    if status["is_rate_limited"]:
        print(f"[Polygon] Rate limit reached ({status['calls_used']}/{status['max_calls']} calls used). Wait {status['time_until_reset']:.0f}s")
        return []
    
    url = "https://api.polygon.io/v3/reference/tickers"
    params = {"search": query.strip(), "active":"true", "market":"stocks", "limit":limit, "apiKey": POLYGON_API_KEY}
    try:
        r = requests.get(url, params=params, timeout=6)
        
        # Track the API call
        _track_api_call()
        
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

def _get_fallback_results(query: str, limit: int) -> List[Dict]:
    """Get fallback results for common stocks to save API calls."""
    fallback_symbols = {
        # Tech Giants
        "AAPL": "Apple Inc.",
        "MSFT": "Microsoft Corporation", 
        "GOOGL": "Alphabet Inc.",
        "AMZN": "Amazon.com Inc.",
        "META": "Meta Platforms Inc.",
        "TSLA": "Tesla Inc.",
        "NVDA": "NVIDIA Corporation",
        "NFLX": "Netflix Inc.",
        "AMD": "Advanced Micro Devices Inc.",
        "INTC": "Intel Corporation",
        "CRM": "Salesforce Inc.",
        "ADBE": "Adobe Inc.",
        "ORCL": "Oracle Corporation",
        "CSCO": "Cisco Systems Inc.",
        "IBM": "International Business Machines Corp.",
        
        # Finance
        "JPM": "JPMorgan Chase & Co.",
        "BAC": "Bank of America Corp.",
        "WFC": "Wells Fargo & Co.",
        "GS": "Goldman Sachs Group Inc.",
        "V": "Visa Inc.",
        "MA": "Mastercard Inc.",
        "PYPL": "PayPal Holdings Inc.",
        
        # Healthcare
        "JNJ": "Johnson & Johnson",
        "UNH": "UnitedHealth Group Inc.",
        "PFE": "Pfizer Inc.",
        "ABBV": "AbbVie Inc.",
        "MRK": "Merck & Co. Inc.",
        
        # Consumer
        "PG": "Procter & Gamble Co.",
        "KO": "Coca-Cola Co.",
        "PEP": "PepsiCo Inc.",
        "WMT": "Walmart Inc.",
        "HD": "Home Depot Inc.",
        "MCD": "McDonald's Corp.",
        "NKE": "Nike Inc.",
        "SBUX": "Starbucks Corp.",
        
        # Energy & Industrial
        "XOM": "Exxon Mobil Corp.",
        "CVX": "Chevron Corp.",
        "BA": "Boeing Co.",
        "CAT": "Caterpillar Inc.",
        "GE": "General Electric Co.",
        
        # ETFs
        "SPY": "SPDR S&P 500 ETF Trust",
        "QQQ": "Invesco QQQ Trust",
        "VTI": "Vanguard Total Stock Market ETF",
        "VOO": "Vanguard S&P 500 ETF"
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
    
    return matches[:limit]

def search_symbols_polygon(query: str, limit: int = 15) -> List[Dict]:
    # Check cache first
    cached = _get_cached_search(query)
    if cached is not None:
        return cached[:limit]
    
    # For very common stocks, try fallback first to save API calls
    common_stocks = ['apple', 'tesla', 'microsoft', 'google', 'amazon', 'meta', 'nvidia', 'jpm', 'spy', 'aapl', 'tsla', 'msft', 'googl', 'amzn', 'nvda']
    query_lower = query.lower().strip()
    
    if query_lower in common_stocks:
        # Try fallback first for common stocks to save API calls
        fallback_results = _get_fallback_results(query, limit)
        if fallback_results:
            _set_cached_search(query, fallback_results)
            return fallback_results
    
    # Try Polygon API for less common searches
    res = _polygon_search(query, limit)
    if res:
        _set_cached_search(query, res)
        return res
    
    # Try Alpha Vantage as backup (but it's rate limited)
    res = _alpha_search(query, limit)
    if res:
        _set_cached_search(query, res)
        return res
    
    # Final fallback: always provide results for better user experience
    fallback_results = _get_fallback_results(query, limit)
    if fallback_results:
        _set_cached_search(query, fallback_results)
        return fallback_results
    
    return []
