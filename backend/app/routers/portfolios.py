from fastapi import APIRouter, Depends
from sqlmodel import Session, select
from ..core.security import get_current_user_id
from ..db import engine
from ..models import Portfolio

router = APIRouter(prefix="/portfolios", tags=["portfolios"])

@router.get("")
def list_my_portfolios(user_id: str = Depends(get_current_user_id)):
    with Session(engine) as session:
        rows = session.exec(select(Portfolio).where(Portfolio.user_id == user_id)).all()
        return rows

@router.post("")
def create_portfolio(name: str = "Default", user_id: str = Depends(get_current_user_id)):
    with Session(engine) as session:
        p = Portfolio(user_id=user_id, name=name)
        session.add(p); session.commit(); session.refresh(p)
        return p
