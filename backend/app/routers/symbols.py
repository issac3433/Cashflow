# backend/app/routers/symbols.py
from fastapi import APIRouter, Query
from ..services.symbols import search_symbols_polygon  # already tries Polygon then Alpha Vantage
from ..services.prices import batch_fetch_latest_prices

router = APIRouter(prefix="/symbols", tags=["symbols"])

@router.get("/search")
def search(q: str = Query(..., min_length=1), limit: int = 15):
    return {"query": q, "results": search_symbols_polygon(q, limit)}

@router.get("/suggest")
def suggest(q: str = Query(..., min_length=1), limit: int = 10):
    # 1) search by name/ticker
    results = search_symbols_polygon(q, limit)
    syms = [r["symbol"] for r in results]
    # 2) batch fetch latest prices
    prices = batch_fetch_latest_prices(syms) if syms else {}
    # 3) merge & shape
    out = []
    for r in results:
        sym = r["symbol"].upper()
        out.append({
            "symbol": sym,
            "name": r.get("name"),
            "primary_exchange": r.get("primary_exchange"),
            "price": prices.get(sym),
        })
    return {"query": q, "results": out}
