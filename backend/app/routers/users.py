from fastapi import APIRouter, Depends
from sqlmodel import Session
from ..core.security import get_current_user_id
from ..db import engine
from ..models import User, Portfolio

router = APIRouter(prefix="/users", tags=["users"])

@router.post("/me/init")
def init_me(user_id: str = Depends(get_current_user_id)):
    with Session(engine) as session:
        u = session.get(User, user_id)
        if not u:
            u = User(id=user_id)
            session.add(u); session.commit()
            session.refresh(u)
            p = Portfolio(user_id=user_id, name="Default")
            session.add(p); session.commit()
        return {"id": u.id, "email": u.email}
