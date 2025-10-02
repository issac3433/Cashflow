from datetime import date, datetime
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship

class User(SQLModel, table=True):
    id: str = Field(primary_key=True)
    email: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    portfolios: List["Portfolio"] = Relationship(back_populates="user")

class Portfolio(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str = Field(foreign_key="user.id")
    name: str = Field(default="Default")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    user: Optional[User] = Relationship(back_populates="portfolios")
    holdings: List["Holding"] = Relationship(back_populates="portfolio")

class Holding(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    portfolio_id: int = Field(foreign_key="portfolio.id")
    symbol: str
    shares: float
    avg_price: float = 0.0
    reinvest_dividends: bool = True
    portfolio: Optional[Portfolio] = Relationship(back_populates="holdings")

class DividendEvent(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    symbol: str
    ex_date: date
    pay_date: Optional[date] = None
    amount: float

class Price(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    symbol: str
    date: date
    close: float
