from typing import Iterable, List
import yfinance as yf
from ..models import DividendEvent

def fetch_dividends_yf(symbol: str, start: str = "2015-01-01") -> List[DividendEvent]:
    t = yf.Ticker(symbol)
    df = t.dividends
    if df is None or df.empty:
        return []
    df = df[df.index >= start]
    out: List[DividendEvent] = []
    for dt, amt in df.items():
        out.append(DividendEvent(symbol=symbol, ex_date=dt.date(), amount=float(amt)))
    return out
