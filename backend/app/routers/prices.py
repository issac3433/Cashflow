from fastapi import APIRouter, Query
from typing import List, Dict, Optional
from app.services.prices import fetch_latest_price, batch_fetch_latest_prices

router = APIRouter(tags=["prices"])

@router.get("/latest/{symbol}")
def latest_price(symbol: str) -> Dict[str, Optional[float]]:
    px = fetch_latest_price(symbol)
    return {"symbol": symbol.upper(), "price": px}

@router.get("/latest")
def latest_prices(symbols: List[str] = Query(..., description="Repeat ?symbols=AAPL&symbols=MSFT")):
    return batch_fetch_latest_prices(symbols)
