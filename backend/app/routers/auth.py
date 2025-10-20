# app/routers/auth.py
from fastapi import APIRouter, Header, Depends, HTTPException
from sqlmodel import Session
from app.db import get_session
from app.models import User, UserProfile
from app.core.security import get_current_user_id

router = APIRouter(tags=["auth"])

@router.get("/debug")
def auth_debug(authorization: str | None = Header(default=None)):
    """
    Dev-only endpoint so Streamlit can "test token".
    If you pass an Authorization: Bearer <token>, we'll echo a fake user id.
    """
    user_id = "demo"
    if authorization and authorization.startswith("Bearer "):
        # In real life, verify JWT here; for dev we just echo a stub id.
        user_id = "jwt_user"
    return {"user_id": user_id, "ok": True}

@router.post("/me/init-supabase")
def init_supabase_user(
    user_id: str = Depends(get_current_user_id),
    session: Session = Depends(get_session)
):
    """
    Initialize a new Supabase user in the local database.
    Creates User and UserProfile records if they don't exist.
    """
    try:
        # Check if user already exists
        from sqlmodel import select
        existing_user = session.exec(
            select(User).where(User.id == user_id)
        ).first()
        
        if existing_user:
            return {"message": "User already exists", "user_id": user_id}
        
        # Create new user
        user = User(id=user_id)
        session.add(user)
        session.commit()
        
        # Create user profile
        profile = UserProfile(
            user_id=user_id,
            cash_balance=0.0,
            total_dividends_received=0.0
        )
        session.add(profile)
        session.commit()
        
        return {"message": "User initialized successfully", "user_id": user_id}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initialize user: {e}")
