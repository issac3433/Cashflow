# app/routers/users.py
from fastapi import APIRouter, Depends
from sqlmodel import Session, select
from datetime import datetime

from app.db import get_session
from app.models import User, Portfolio

router = APIRouter(tags=["users"])

@router.post("/me/init")
def init_dev_user(session: Session = Depends(get_session)):
    """
    Dev initializer:
    - ensures a demo user exists
    - ensures a default portfolio exists
    - returns user + default portfolio id
    """
    # 1) ensure user
    user = session.get(User, "demo")
    if not user:
        user = User(id="demo", email="demo@example.com", created_at=datetime.utcnow())
        session.add(user)
        session.commit()

    # 2) ensure a default portfolio
    port = session.exec(
        select(Portfolio).where(Portfolio.user_id == user.id)
    ).first()
    if not port:
        port = Portfolio(user_id=user.id, name="Default", created_at=datetime.utcnow())
        session.add(port)
        session.commit()
        session.refresh(port)

    return {"id": user.id, "portfolio_id": port.id, "email": user.email}
