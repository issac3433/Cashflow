#!/usr/bin/env python3
"""
Migration script to transfer data from SQLite to Neon PostgreSQL
"""
import sqlite3
import os
from sqlmodel import create_engine, Session, text

# Database connections
SQLITE_DB = "/Users/nathanielissac/Desktop/Capstone/cashflow/backend/cashflow.db"
NEON_URL = "postgresql://neondb_owner:npg_9kS0bADjnNHC@ep-empty-shape-adbw9vzz-pooler.c-2.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"

def migrate_data():
    print("🔄 Starting data migration from SQLite to Neon...")
    
    # Connect to both databases
    sqlite_conn = sqlite3.connect(SQLITE_DB)
    sqlite_conn.row_factory = sqlite3.Row  # Enable column access by name
    
    neon_engine = create_engine(NEON_URL)
    
    with Session(neon_engine) as neon_session:
        # Migrate users
        print("📊 Migrating users...")
        users = sqlite_conn.execute("SELECT * FROM user").fetchall()
        for user in users:
            neon_session.execute(text("""
                INSERT INTO "user" (id, email, created_at) 
                VALUES (:id, :email, :created_at)
                ON CONFLICT (id) DO NOTHING
            """), {
                "id": user["id"],
                "email": user["email"], 
                "created_at": user["created_at"]
            })
        print(f"✅ Migrated {len(users)} users")
        
        # Migrate portfolios
        print("📊 Migrating portfolios...")
        portfolios = sqlite_conn.execute("SELECT * FROM portfolio").fetchall()
        for portfolio in portfolios:
            neon_session.execute(text("""
                INSERT INTO portfolio (id, user_id, name, created_at) 
                VALUES (:id, :user_id, :name, :created_at)
                ON CONFLICT (id) DO NOTHING
            """), {
                "id": portfolio["id"],
                "user_id": portfolio["user_id"],
                "name": portfolio["name"],
                "created_at": portfolio["created_at"]
            })
        print(f"✅ Migrated {len(portfolios)} portfolios")
        
        # Migrate holdings
        print("📊 Migrating holdings...")
        holdings = sqlite_conn.execute("SELECT * FROM holding").fetchall()
        for holding in holdings:
            neon_session.execute(text("""
                INSERT INTO holding (id, portfolio_id, symbol, shares, avg_price, reinvest_dividends) 
                VALUES (:id, :portfolio_id, :symbol, :shares, :avg_price, :reinvest_dividends)
                ON CONFLICT (id) DO NOTHING
            """), {
                "id": holding["id"],
                "portfolio_id": holding["portfolio_id"],
                "symbol": holding["symbol"],
                "shares": holding["shares"],
                "avg_price": holding["avg_price"],
                "reinvest_dividends": bool(holding["reinvest_dividends"])  # Convert to boolean
            })
        print(f"✅ Migrated {len(holdings)} holdings")
        
        # Migrate user profiles
        print("📊 Migrating user profiles...")
        profiles = sqlite_conn.execute("SELECT * FROM user_profiles").fetchall()
        for profile in profiles:
            neon_session.execute(text("""
                INSERT INTO user_profiles (id, user_id, cash_balance, total_dividends_received, last_updated) 
                VALUES (:id, :user_id, :cash_balance, :total_dividends_received, :last_updated)
                ON CONFLICT (id) DO NOTHING
            """), {
                "id": profile["id"],
                "user_id": profile["user_id"],
                "cash_balance": profile["cash_balance"],
                "total_dividends_received": profile["total_dividends_received"],
                "last_updated": profile["last_updated"]
            })
        print(f"✅ Migrated {len(profiles)} user profiles")
        
        # Migrate dividend events
        print("📊 Migrating dividend events...")
        div_events = sqlite_conn.execute("SELECT * FROM dividend_events").fetchall()
        for event in div_events:
            neon_session.execute(text("""
                INSERT INTO dividend_events (id, symbol, ex_date, pay_date, amount, created_at) 
                VALUES (:id, :symbol, :ex_date, :pay_date, :amount, NOW())
                ON CONFLICT (id) DO NOTHING
            """), {
                "id": event["id"],
                "symbol": event["symbol"],
                "ex_date": event["ex_date"],
                "pay_date": event["pay_date"],
                "amount": event["amount"]
            })
        print(f"✅ Migrated {len(div_events)} dividend events")
        
        # Migrate dividend payments
        print("📊 Migrating dividend payments...")
        div_payments = sqlite_conn.execute("SELECT * FROM dividend_payments").fetchall()
        for payment in div_payments:
            neon_session.execute(text("""
                INSERT INTO dividend_payments (id, user_id, portfolio_id, symbol, ex_date, pay_date, amount_per_share, shares_owned, total_amount, reinvested, processed_at) 
                VALUES (:id, :user_id, :portfolio_id, :symbol, :ex_date, :pay_date, :amount_per_share, :shares_owned, :total_amount, :reinvested, :processed_at)
                ON CONFLICT (id) DO NOTHING
            """), {
                "id": payment["id"],
                "user_id": payment["user_id"],
                "portfolio_id": payment["portfolio_id"],
                "symbol": payment["symbol"],
                "ex_date": payment["ex_date"],
                "pay_date": payment["pay_date"],
                "amount_per_share": payment["amount_per_share"],
                "shares_owned": payment["shares_owned"],
                "total_amount": payment["total_amount"],
                "reinvested": bool(payment["reinvested"]),  # Convert to boolean
                "processed_at": payment["processed_at"]
            })
        print(f"✅ Migrated {len(div_payments)} dividend payments")
        
        # Migrate prices
        print("📊 Migrating prices...")
        prices = sqlite_conn.execute("SELECT * FROM price").fetchall()
        for price in prices:
            neon_session.execute(text("""
                INSERT INTO price (id, symbol, date, open, high, low, close, volume) 
                VALUES (:id, :symbol, :date, :open, :high, :low, :close, :volume)
                ON CONFLICT (id) DO NOTHING
            """), {
                "id": price["id"],
                "symbol": price["symbol"],
                "date": price["date"],
                "open": price["open"],
                "high": price["high"],
                "low": price["low"],
                "close": price["close"],
                "volume": price["volume"]
            })
        print(f"✅ Migrated {len(prices)} prices")
        
        # Commit all changes
        neon_session.commit()
        print("🎉 Data migration completed successfully!")
    
    sqlite_conn.close()

if __name__ == "__main__":
    migrate_data()
