import pandas as pd
from datetime import date
from sqlmodel import Session, select
from ..models import Holding, DividendEvent

def monthly_cashflow_forecast(session: Session, portfolio_id: int, months: int = 12,
                               assume_reinvest: bool = True, recurring_deposit: float = 0.0,
                               deposit_freq: str = "monthly", start_date: date | None = None):
    holdings = session.exec(select(Holding).where(Holding.portfolio_id == portfolio_id)).all()
    if not holdings:
        return {"series": [], "total": 0.0}

    symbols = [h.symbol for h in holdings]
    if not symbols:
        return {"series": [], "total": 0.0}

    q = select(DividendEvent).where(DividendEvent.symbol.in_(symbols))
    events = session.exec(q).all()
    if not events:
        return {"series": [], "total": 0.0}

    df = pd.DataFrame([{"symbol": e.symbol, "date": pd.to_datetime(e.ex_date), "amount": e.amount} for e in events])
    last12 = df[df["date"] >= (df["date"].max() - pd.Timedelta(days=365))]
    by_symbol = last12.groupby("symbol")["amount"].sum()

    start = pd.Timestamp.today().normalize().to_period('M').to_timestamp() if not start_date else pd.Timestamp(start_date)
    idx = pd.date_range(start, periods=months, freq='MS')
    cash = pd.Series(0.0, index=idx)

    for h in holdings:
        annual = float(by_symbol.get(h.symbol, 0.0)) * h.shares
        cash += annual / 12.0

    return {"series": [{"month": d.strftime("%Y-%m"), "income": float(cash.loc[d])} for d in cash.index],
            "total": float(cash.sum())}
