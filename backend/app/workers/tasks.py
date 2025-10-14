# app/workers/tasks.py
from app.workers.celery_app import celery_app
from app.services.dividends import refresh_all_dividends, build_portfolio_income_calendar

@celery_app.task(name="app.workers.tasks.refresh_dividends_for_all")
def refresh_dividends_for_all():
    count = refresh_all_dividends()               # fetch + upsert for all symbols user owns
    portfolios = build_portfolio_income_calendar()# recompute calendars
    return {"symbols_updated": count, "portfolios": len(portfolios)}


