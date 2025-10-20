# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db import create_db_and_tables
from app.routers import users, portfolios, holdings, dividends, forecasts, prices, symbols, auth, profile, risk

app = FastAPI(title="Cashflow API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

app.include_router(users.router,      prefix="",      tags=["users"])
app.include_router(portfolios.router, prefix="/portfolios", tags=["portfolios"])
app.include_router(holdings.router,   prefix="/holdings",   tags=["holdings"])
app.include_router(prices.router,     prefix="/prices",     tags=["prices"])
app.include_router(dividends.router,  prefix="",  tags=["dividends"])
app.include_router(forecasts.router,  prefix="/forecasts",  tags=["forecasts"])
app.include_router(symbols.router,    prefix="/symbols",    tags=["symbols"])
app.include_router(auth.router,       prefix="",            tags=["auth"])
app.include_router(profile.router,    prefix="",            tags=["profile"])
app.include_router(risk.router,       prefix="/risk",       tags=["risk"])    

@app.get("/health")
def health():
    return {"ok": True}
