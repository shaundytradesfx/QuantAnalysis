#!/usr/bin/env python3
"""
Test database connection directly.
"""
import psycopg2
import os

def test_db_connection():
    """Test PostgreSQL connection."""
    try:
        # Try connecting with current user
        conn = psycopg2.connect(
            host='localhost',
            port='5432',
            database='forex_sentiment',
            user='shaun'
        )
        print('✅ Database connection successful!')
        
        # Test basic query
        cursor = conn.cursor()
        cursor.execute('SELECT version();')
        version = cursor.fetchone()
        print(f'📊 PostgreSQL version: {version[0]}')
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f'❌ Database connection failed: {e}')
        return False

if __name__ == "__main__":
    test_db_connection() 