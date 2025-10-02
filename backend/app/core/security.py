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

async def get_current_user_id(creds: HTTPAuthorizationCredentials = Depends(security)) -> str:
    if settings.AUTH_MODE == "dev":
        return "dev_user"
    if not creds:
        raise HTTPException(status_code=401, detail="Missing token")
    token = creds.credentials
    jwks = _jwks()
    try:
        unverified = jwt.get_unverified_header(token)
        kid = unverified.get("kid")
        key = next((k for k in jwks["keys"] if k["kid"] == kid), None)
        if not key:
            raise HTTPException(status_code=401, detail="Invalid key")
        payload = jwt.decode(token, key, algorithms=[key["alg"]], audience=settings.CLERK_AUDIENCE)
        return payload.get("sub") or payload.get("user_id")
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Auth failed: {e}")
