# migrate_portfolio_cash_balance.py
import os
import sys
from pathlib import Path
from sqlmodel import create_engine, Session, text
from dotenv import load_dotenv

# Load environment variables
ENV_PATH = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=ENV_PATH, override=True)

# Get database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("❌ ERROR: DATABASE_URL not found in .env file")
    sys.exit(1)

# Ensure we're using psycopg (psycopg3) driver
# Convert postgresql:// to postgresql+psycopg:// if needed
if DATABASE_URL.startswith("postgresql://") and "+psycopg" not in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)

def migrate_portfolio_cash_balance():
    """Add cash_balance column to existing portfolios."""
    print(f"📝 Using database: {DATABASE_URL[:50]}...")
    engine = create_engine(DATABASE_URL, echo=False)
    
    with Session(engine) as session:
        print("🔄 Adding cash_balance column to portfolio table...")
        
        # Add the column if it doesn't exist
        try:
            # Use DOUBLE PRECISION for PostgreSQL (or FLOAT)
            session.execute(text("ALTER TABLE portfolio ADD COLUMN IF NOT EXISTS cash_balance DOUBLE PRECISION DEFAULT 0.0"))
            session.commit()
            print("✅ Added cash_balance column")
        except Exception as e:
            print(f"⚠️ Column might already exist or error: {e}")
            # Try with FLOAT if DOUBLE PRECISION doesn't work
            try:
                session.execute(text("ALTER TABLE portfolio ADD COLUMN IF NOT EXISTS cash_balance FLOAT DEFAULT 0.0"))
                session.commit()
                print("✅ Added cash_balance column (using FLOAT)")
            except Exception as e2:
                print(f"⚠️ Could not add column: {e2}")
        
        # Update existing portfolios to have 0.0 cash balance if NULL
        try:
            result = session.execute(text("UPDATE portfolio SET cash_balance = 0.0 WHERE cash_balance IS NULL"))
            session.commit()
            print(f"✅ Updated {result.rowcount} portfolios to have 0.0 cash balance")
        except Exception as e:
            print(f"⚠️ Update might not be needed: {e}")
        
        # Show current portfolios with cash balances
        try:
            result = session.execute(text("SELECT id, name, cash_balance FROM portfolio"))
            portfolios = result.fetchall()
            
            print("\n📊 Current portfolios:")
            for portfolio in portfolios:
                cash = portfolio[2] if portfolio[2] is not None else 0.0
                print(f"  ID: {portfolio[0]}, Name: {portfolio[1]}, Cash: ${cash:,.2f}")
        except Exception as e:
            print(f"⚠️ Could not query portfolios: {e}")
        
        print("\n🎉 Migration complete!")

if __name__ == "__main__":
    migrate_portfolio_cash_balance()

