#!/usr/bin/env python3
"""
Comprehensive verification script to ensure database implementation matches PRD requirements.
"""
import sys
import os
from datetime import datetime
import psycopg2

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.database.models import Event, Indicator, Sentiment, Config, AuditFailure
from src.database.config import engine
from sqlalchemy import inspect, text

def verify_database_implementation():
    """Verify that the database implementation matches PRD requirements."""
    print("🔍 Verifying Database Implementation Against PRD Requirements")
    print("=" * 70)
    
    verification_results = []
    
    # Connect to database
    try:
        conn = psycopg2.connect(
            host='localhost',
            port='5432',
            database='forex_sentiment',
            user='shaun'
        )
        cursor = conn.cursor()
        print("✅ Database connection successful")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False
    
    # 1. Verify all required tables exist
    print("\n📋 Checking Required Tables...")
    required_tables = ['events', 'indicators', 'sentiments', 'config', 'audit_failures']
    
    cursor.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public';")
    existing_tables = [row[0] for row in cursor.fetchall()]
    
    for table in required_tables:
        if table in existing_tables:
            print(f"  ✅ {table} table exists")
            verification_results.append(f"✅ {table} table")
        else:
            print(f"  ❌ {table} table missing")
            verification_results.append(f"❌ {table} table")
    
    # 2. Verify events table structure
    print("\n📊 Verifying Events Table Structure...")
    cursor.execute("""
        SELECT column_name, data_type, is_nullable 
        FROM information_schema.columns 
        WHERE table_name = 'events' 
        ORDER BY ordinal_position;
    """)
    events_columns = cursor.fetchall()
    
    required_events_columns = {
        'id': 'integer',
        'currency': 'character varying',
        'event_name': 'text',
        'scheduled_datetime': 'timestamp with time zone',
        'impact_level': 'character varying',
        'created_at': 'timestamp with time zone',
        'updated_at': 'timestamp with time zone'
    }
    
    for col_name, col_type, nullable in events_columns:
        if col_name in required_events_columns:
            expected_type = required_events_columns[col_name]
            if expected_type in col_type:
                print(f"  ✅ {col_name}: {col_type}")
                verification_results.append(f"✅ events.{col_name}")
            else:
                print(f"  ❌ {col_name}: expected {expected_type}, got {col_type}")
                verification_results.append(f"❌ events.{col_name}")
    
    # 3. Verify indicators table structure
    print("\n📈 Verifying Indicators Table Structure...")
    cursor.execute("""
        SELECT column_name, data_type, is_nullable 
        FROM information_schema.columns 
        WHERE table_name = 'indicators' 
        ORDER BY ordinal_position;
    """)
    indicators_columns = cursor.fetchall()
    
    required_indicators_columns = {
        'id': 'integer',
        'event_id': 'integer',
        'previous_value': 'double precision',
        'forecast_value': 'double precision',
        'timestamp_collected': 'timestamp with time zone'
    }
    
    for col_name, col_type, nullable in indicators_columns:
        if col_name in required_indicators_columns:
            expected_type = required_indicators_columns[col_name]
            if expected_type in col_type:
                print(f"  ✅ {col_name}: {col_type}")
                verification_results.append(f"✅ indicators.{col_name}")
            else:
                print(f"  ❌ {col_name}: expected {expected_type}, got {col_type}")
                verification_results.append(f"❌ indicators.{col_name}")
    
    # 4. Verify required indexes
    print("\n🔍 Verifying Required Indexes...")
    
    # Check composite index on events (currency, scheduled_datetime)
    cursor.execute("""
        SELECT indexname, indexdef 
        FROM pg_indexes 
        WHERE tablename = 'events' AND indexname = 'ix_events_currency_scheduled_datetime';
    """)
    events_composite_index = cursor.fetchall()
    
    if events_composite_index:
        print("  ✅ Events composite index (currency, scheduled_datetime) exists")
        verification_results.append("✅ Events composite index")
    else:
        print("  ❌ Events composite index (currency, scheduled_datetime) missing")
        verification_results.append("❌ Events composite index")
    
    # Check indicators index with DESC
    cursor.execute("""
        SELECT indexname, indexdef 
        FROM pg_indexes 
        WHERE tablename = 'indicators' AND indexname = 'ix_indicators_event_id_timestamp_desc';
    """)
    indicators_desc_index = cursor.fetchall()
    
    if indicators_desc_index:
        print("  ✅ Indicators index (event_id, timestamp_collected DESC) exists")
        verification_results.append("✅ Indicators DESC index")
    else:
        print("  ❌ Indicators index (event_id, timestamp_collected DESC) missing")
        verification_results.append("❌ Indicators DESC index")
    
    # 5. Verify audit table structure
    print("\n🔍 Verifying Audit Failures Table Structure...")
    cursor.execute("""
        SELECT column_name, data_type, is_nullable 
        FROM information_schema.columns 
        WHERE table_name = 'audit_failures' 
        ORDER BY ordinal_position;
    """)
    audit_columns = cursor.fetchall()
    
    required_audit_columns = {
        'id': 'integer',
        'url': 'text',
        'error_type': 'character varying',
        'error_message': 'text',
        'html_snippet': 'text',
        'timestamp': 'timestamp with time zone',
        'retry_count': 'integer',
        'resolved': 'boolean'
    }
    
    for col_name, col_type, nullable in audit_columns:
        if col_name in required_audit_columns:
            expected_type = required_audit_columns[col_name]
            if expected_type in col_type:
                print(f"  ✅ {col_name}: {col_type}")
                verification_results.append(f"✅ audit_failures.{col_name}")
            else:
                print(f"  ❌ {col_name}: expected {expected_type}, got {col_type}")
                verification_results.append(f"❌ audit_failures.{col_name}")
    
    # 6. Verify foreign key constraints
    print("\n🔗 Verifying Foreign Key Constraints...")
    cursor.execute("""
        SELECT tc.constraint_name, tc.table_name, kcu.column_name, 
               ccu.table_name AS foreign_table_name, ccu.column_name AS foreign_column_name 
        FROM information_schema.table_constraints AS tc 
        JOIN information_schema.key_column_usage AS kcu
          ON tc.constraint_name = kcu.constraint_name
        JOIN information_schema.constraint_column_usage AS ccu
          ON ccu.constraint_name = tc.constraint_name
        WHERE constraint_type = 'FOREIGN KEY' AND tc.table_name = 'indicators';
    """)
    foreign_keys = cursor.fetchall()
    
    if foreign_keys:
        for fk in foreign_keys:
            print(f"  ✅ Foreign key: {fk[1]}.{fk[2]} -> {fk[3]}.{fk[4]}")
            verification_results.append("✅ Foreign key constraint")
    else:
        print("  ❌ No foreign key constraints found")
        verification_results.append("❌ Foreign key constraint")
    
    # 7. Test basic CRUD operations
    print("\n🧪 Testing Basic Database Operations...")
    try:
        # Test insert
        cursor.execute("""
            INSERT INTO events (currency, event_name, scheduled_datetime, impact_level) 
            VALUES ('USD', 'Test Event', NOW(), 'High') RETURNING id;
        """)
        event_id = cursor.fetchone()[0]
        print("  ✅ Insert operation successful")
        verification_results.append("✅ Insert operation")
        
        # Test select
        cursor.execute("SELECT * FROM events WHERE id = %s;", (event_id,))
        result = cursor.fetchone()
        if result:
            print("  ✅ Select operation successful")
            verification_results.append("✅ Select operation")
        
        # Test cleanup
        cursor.execute("DELETE FROM events WHERE id = %s;", (event_id,))
        print("  ✅ Delete operation successful")
        verification_results.append("✅ Delete operation")
        
        conn.commit()
        
    except Exception as e:
        print(f"  ❌ Database operations failed: {e}")
        verification_results.append("❌ Database operations")
        conn.rollback()
    
    # Close connection
    cursor.close()
    conn.close()
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 VERIFICATION SUMMARY")
    print("=" * 70)
    
    passed = len([r for r in verification_results if r.startswith("✅")])
    total = len(verification_results)
    
    print(f"✅ Passed: {passed}/{total} checks")
    
    if passed == total:
        print("🎉 DATABASE IMPLEMENTATION FULLY COMPLIANT WITH PRD!")
        return True
    else:
        failed = total - passed
        print(f"❌ Failed: {failed}/{total} checks")
        print("⚠️  Database implementation needs attention")
        return False

if __name__ == "__main__":
    success = verify_database_implementation()
    sys.exit(0 if success else 1) 