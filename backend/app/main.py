import uvicorn
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from .core.config import settings
from .db import init_db
from .core.security import get_current_user_id
from .routers import users, portfolios, holdings, dividends, forecasts, prices, symbols
from .routers import holdings_quotes


app = FastAPI(title="Cashflow API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"ok": True}

@app.get("/auth/debug")
def auth_debug(user_id: str = Depends(get_current_user_id)):
    return {"user_id": user_id}

app.include_router(users.router)
app.include_router(portfolios.router)
app.include_router(holdings.router)
app.include_router(dividends.router)
app.include_router(forecasts.router)
app.include_router(prices.router)  
app.include_router(symbols.router)
app.include_router(holdings_quotes.router)

def start():
    init_db()
    uvicorn.run("app.main:app", host=settings.API_HOST, port=settings.API_PORT, reload=True)

if __name__ == "__main__":
    start()
