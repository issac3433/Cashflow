# backend/app/routers/symbols.py
from fastapi import APIRouter, Query
from app.services.symbols import search_symbols_polygon  # already tries Polygon then Alpha Vantage
from app.services.prices import batch_fetch_latest_prices

router = APIRouter(tags=["symbols"])

@router.get("/search")
def search(q: str = Query(..., min_length=1), limit: int = 15):
    return {"query": q, "results": search_symbols_polygon(q, limit)}

@router.get("/suggest")
def suggest(q: str = Query(..., min_length=1), limit: int = 10):
    try:
        # 1) search by name/ticker
        results = search_symbols_polygon(q, limit)
        if not results:
            return {"query": q, "results": []}
            
        syms = [r.get("symbol") for r in results if r.get("symbol")]
        # 2) batch fetch latest prices
        prices = batch_fetch_latest_prices(syms) if syms else {}
        # 3) merge & shape
        out = []
        for r in results:
            sym = r.get("symbol", "").upper()
            if sym:  # Only process if symbol exists
                out.append({
                    "symbol": sym,
                    "name": r.get("name", ""),
                    "primary_exchange": r.get("primary_exchange", ""),
                    "price": prices.get(sym),
                })
        return {"query": q, "results": out}
    except Exception as e:
        # Return empty results on any error
        return {"query": q, "results": [], "error": str(e)}
