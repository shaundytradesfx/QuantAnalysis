#!/usr/bin/env python3
"""
Test script to verify database connection with psycopg3.
"""

import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

def test_database_connection():
    """Test database connection and psycopg3 compatibility."""
    
    print("🧪 Testing Database Connection with Psycopg3")
    print("=" * 50)
    
    # Load environment variables
    load_dotenv()
    
    # Database connection details
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "5432")
    DB_NAME = os.getenv("DB_NAME", "forex_sentiment")
    DB_USER = os.getenv("DB_USER", "postgres")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    
    # SQLAlchemy connection string - explicitly use psycopg3 driver
    DATABASE_URL = f"postgresql+psycopg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    
    print(f"Database URL: {DATABASE_URL.replace(DB_PASSWORD, '***')}")
    
    try:
        # Create engine
        engine = create_engine(DATABASE_URL)
        
        # Test connection
        with engine.connect() as conn:
            # Test basic query
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print(f"✅ PostgreSQL Version: {version}")
            
            # Test psycopg3 driver
            print(f"✅ SQLAlchemy Engine: {engine.name}")
            print(f"✅ Driver: {engine.driver}")
            
            # Test if we can query system tables
            result = conn.execute(text("SELECT 1 as test_value"))
            test_value = result.fetchone()[0]
            print(f"✅ Test Query Result: {test_value}")
            
            # Check if our tables exist (if migrations were run)
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """))
            
            tables = [row[0] for row in result.fetchall()]
            print(f"✅ Existing Tables: {tables}")
            
        print("\n🎉 Database connection test PASSED!")
        return True
        
    except Exception as e:
        print(f"\n❌ Database connection test FAILED: {e}")
        print("   Note: This might be expected if PostgreSQL server is not running")
        print("   or if database doesn't exist yet.")
        return False

if __name__ == "__main__":
    test_database_connection() 