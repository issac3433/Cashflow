# backend/app/core/config.py
from pathlib import Path
from dotenv import load_dotenv

# Always load .../backend/.env regardless of where you run `python -m`
ENV_PATH = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(dotenv_path=ENV_PATH, override=True)

import os
from pydantic import BaseModel


class Settings(BaseModel):
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", 8080))
    ENV: str = os.getenv("ENV", "dev")
    AUTH_MODE: str = os.getenv("AUTH_MODE", "dev")  # dev|clerk

    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    CLERK_JWKS_URL: str = os.getenv("CLERK_JWKS_URL", "")
    CLERK_AUDIENCE: str = os.getenv("CLERK_AUDIENCE", "api")

    DEFAULT_START_DATE: str = os.getenv("DEFAULT_START_DATE", "2015-01-01")


settings = Settings()
