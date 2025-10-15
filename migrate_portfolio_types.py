# migrate_portfolio_types.py
import os
from sqlmodel import create_engine, Session, text

# Database connection
DATABASE_URL = "postgresql://neondb_owner:npg_9kS0bADjnNHC@ep-empty-shape-adbw9vzz-pooler.c-2.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"

def migrate_portfolio_types():
    """Add portfolio_type column to existing portfolios."""
    engine = create_engine(DATABASE_URL)
    
    with Session(engine) as session:
        print("🔄 Adding portfolio_type column to portfolios table...")
        
        # Add the column if it doesn't exist
        try:
            session.execute(text("ALTER TABLE portfolio ADD COLUMN IF NOT EXISTS portfolio_type VARCHAR DEFAULT 'individual'"))
            session.commit()
            print("✅ Added portfolio_type column")
        except Exception as e:
            print(f"⚠️ Column might already exist: {e}")
        
        # Update existing portfolios to have 'individual' type
        try:
            result = session.execute(text("UPDATE portfolio SET portfolio_type = 'individual' WHERE portfolio_type IS NULL"))
            session.commit()
            print(f"✅ Updated {result.rowcount} portfolios to 'individual' type")
        except Exception as e:
            print(f"⚠️ Update might not be needed: {e}")
        
        # Show current portfolios
        result = session.execute(text("SELECT id, name, portfolio_type FROM portfolio"))
        portfolios = result.fetchall()
        
        print("\n📊 Current portfolios:")
        for portfolio in portfolios:
            print(f"  ID: {portfolio[0]}, Name: {portfolio[1]}, Type: {portfolio[2]}")
        
        print("\n🎉 Migration complete!")

if __name__ == "__main__":
    migrate_portfolio_types()
