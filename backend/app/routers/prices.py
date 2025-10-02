from fastapi import APIRouter
from ..services.prices import fetch_latest_price

router = APIRouter(prefix="/prices", tags=["prices"])

@router.get("/quote/{symbol}")
def quote(symbol: str):
    px = fetch_latest_price(symbol)
    return {
        "symbol": symbol.upper(),
        "price": px,
        "source": "polygon_prev_close" if px else "fallback",
        "ok": px is not None
    }
