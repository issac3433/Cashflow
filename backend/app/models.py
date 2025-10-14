# app/models.py
from __future__ import annotations
from typing import Optional
from datetime import date, datetime
from sqlmodel import SQLModel, Field, Column, String  # ← remove Relationship
from sqlalchemy import UniqueConstraint

class DividendEvent(SQLModel, table=True):
    __tablename__ = "dividend_events"
    id: Optional[int] = Field(default=None, primary_key=True)
    symbol: str = Field(sa_column=Column(String, index=True))
    ex_date: Optional[date] = Field(default=None, index=True)
    pay_date: Optional[date] = None
    record_date: Optional[date] = None
    amount: float = 0.0
    source: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    __table_args__ = (
        UniqueConstraint("symbol", "ex_date", "amount", name="uq_div_symbol_ex_amount"),
    )

class User(SQLModel, table=True):
    id: str = Field(primary_key=True)
    email: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    # portfolios: list["Portfolio"] = Relationship(back_populates="user")  # ← remove

class Portfolio(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str = Field(foreign_key="user.id")
    name: str = Field(default="Default")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    # user: Optional[User] = Relationship(back_populates="portfolios")      # ← remove
    # holdings: list["Holding"] = Relationship(back_populates="portfolio")  # ← remove

class Holding(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    portfolio_id: int = Field(foreign_key="portfolio.id")
    symbol: str
    shares: float
    avg_price: float = 0.0
    reinvest_dividends: bool = True
    # portfolio: Optional[Portfolio] = Relationship(back_populates="holdings")  # ← remove

class UserProfile(SQLModel, table=True):
    __tablename__ = "user_profiles"
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str = Field(foreign_key="user.id", unique=True)
    cash_balance: float = Field(default=0.0)
    total_dividends_received: float = Field(default=0.0)
    last_updated: datetime = Field(default_factory=datetime.utcnow)

class DividendPayment(SQLModel, table=True):
    __tablename__ = "dividend_payments"
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str = Field(foreign_key="user.id")
    portfolio_id: int = Field(foreign_key="portfolio.id")
    symbol: str
    ex_date: date
    pay_date: Optional[date] = None
    amount_per_share: float
    shares_owned: float
    total_amount: float
    reinvested: bool = Field(default=False)
    processed_at: datetime = Field(default_factory=datetime.utcnow)
    __table_args__ = (
        UniqueConstraint("user_id", "symbol", "ex_date", name="uq_div_payment_user_symbol_ex"),
    )
