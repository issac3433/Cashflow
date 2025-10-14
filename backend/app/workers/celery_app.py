import os
from celery import Celery

broker = os.getenv("CELERY_BROKER_URL", os.getenv("REDIS_URL", "redis://localhost:6379/0"))
backend = os.getenv("CELERY_RESULT_BACKEND", broker)

celery_app = Celery("cashflow", broker=broker, backend=backend)
celery_app.conf.timezone = "UTC"

# Beat schedule: run nightly at 03:10 UTC
celery_app.conf.beat_schedule = {
    "sync-dividends-nightly": {
        "task": "app.workers.tasks.sync_all_dividends",
        "schedule": 24 * 60 * 60,  # every 24h
        "options": {"expires": 60 * 60},
    }
}
