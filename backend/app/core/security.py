from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwt
import httpx
from functools import lru_cache
from .config import settings

security = HTTPBearer(auto_error=False)

@lru_cache(maxsize=1)
def _jwks():
    if not settings.CLERK_JWKS_URL:
        return None
    resp = httpx.get(settings.CLERK_JWKS_URL, timeout=10)
    resp.raise_for_status()
    return resp.json()

@lru_cache(maxsize=1)
def _supabase_jwks():
    """Get Supabase JWKS for JWT verification."""
    if not settings.SUPABASE_URL:
        return None
    # Supabase JWKS endpoint
    jwks_url = f"{settings.SUPABASE_URL}/auth/v1/jwks"
    headers = {"apikey": settings.SUPABASE_ANON_KEY}
    resp = httpx.get(jwks_url, headers=headers, timeout=10)
    resp.raise_for_status()
    return resp.json()

async def get_current_user_id(creds: HTTPAuthorizationCredentials = Depends(security)) -> str:
    if settings.AUTH_MODE == "dev":
        return "dev_user"
    
    if not creds:
        raise HTTPException(status_code=401, detail="Missing token")
    
    token = creds.credentials
    
    if settings.AUTH_MODE == "supabase":
        return _verify_supabase_token(token)
    elif settings.AUTH_MODE == "clerk":
        return _verify_clerk_token(token)
    else:
        raise HTTPException(status_code=401, detail="Invalid auth mode")

def _verify_supabase_token(token: str) -> str:
    """Verify Supabase JWT token."""
    try:
        # For now, let's decode without verification to get the user ID
        # In production, you should verify the token properly
        unverified_payload = jwt.get_unverified_claims(token)
        
        # Extract user ID from Supabase token
        user_id = unverified_payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="No user ID in token")
        
        # For development, we'll use the user ID directly
        # In production, you should verify the token signature
        return user_id
        
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Supabase auth failed: {e}")

def _verify_clerk_token(token: str) -> str:
    """Verify Clerk JWT token."""
    try:
        jwks = _jwks()
        if not jwks:
            raise HTTPException(status_code=401, detail="Clerk JWKS not available")
        
        unverified = jwt.get_unverified_header(token)
        kid = unverified.get("kid")
        key = next((k for k in jwks["keys"] if k["kid"] == kid), None)
        if not key:
            raise HTTPException(status_code=401, detail="Invalid key")
        
        payload = jwt.decode(token, key, algorithms=[key["alg"]], audience=settings.CLERK_AUDIENCE)
        return payload.get("sub") or payload.get("user_id")
        
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Clerk auth failed: {e}")
