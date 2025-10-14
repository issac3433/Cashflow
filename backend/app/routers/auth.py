# app/routers/auth.py
from fastapi import APIRouter, Header

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
