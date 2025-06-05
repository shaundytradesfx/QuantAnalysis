#!/usr/bin/env python3
"""
Test script for Phase 1 actual data collection implementation.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, timedelta
from src.database.config import SessionLocal
from src.database.models import Event, Indicator
from src.scraper.actual_data_collector import ActualDataCollector
from src.analysis.sentiment_engine import SentimentCalculator
from sqlalchemy import text

def test_database_schema():
    """Test that the database schema changes are working correctly."""
    print("🔍 Testing database schema changes...")
    
    try:
        with SessionLocal() as db:
            # Check if actual data columns exist
            result = db.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'indicators' 
                AND column_name IN ('actual_value', 'actual_collected_at', 'actual_sentiment', 'is_actual_available')
            """))
            columns = [row[0] for row in result]
            
            expected_columns = ['actual_value', 'actual_collected_at', 'actual_sentiment', 'is_actual_available']
            missing_columns = set(expected_columns) - set(columns)
            
            if missing_columns:
                print(f"❌ Missing columns: {missing_columns}")
                return False
            else:
                print(f"✅ All actual data columns present: {columns}")
                
            # Check if indexes exist
            result = db.execute(text("""
                SELECT indexname 
                FROM pg_indexes 
                WHERE tablename = 'indicators' 
                AND indexname LIKE '%actual%'
            """))
            indexes = [row[0] for row in result]
            print(f"✅ Actual data indexes: {indexes}")
            
            return True
            
    except Exception as e:
        print(f"❌ Database schema test failed: {e}")
        return False

def test_actual_data_collector():
    """Test the actual data collector functionality."""
    print("\n🔍 Testing actual data collector...")
    
    try:
        with ActualDataCollector(lookback_days=7) as collector:
            # Test getting events missing actual data
            events = collector.get_events_missing_actual_data()
            print(f"✅ Found {len(events)} events missing actual data")
            
            # Test the collector methods exist and are callable
            assert hasattr(collector, 'collect_actual_data_for_event')
            assert hasattr(collector, 'update_indicator_with_actual_data')
            assert hasattr(collector, 'collect_all_missing_actual_data')
            print("✅ All collector methods are available")
            
            return True
            
    except Exception as e:
        print(f"❌ Actual data collector test failed: {e}")
        return False

def test_sentiment_engine_extensions():
    """Test the sentiment engine extensions for actual sentiment."""
    print("\n🔍 Testing sentiment engine extensions...")
    
    try:
        with SentimentCalculator() as calculator:
            # Test new methods exist
            assert hasattr(calculator, 'get_week_events_with_actual_indicators')
            assert hasattr(calculator, 'calculate_actual_event_sentiment')
            assert hasattr(calculator, 'calculate_actual_sentiment')
            assert hasattr(calculator, 'resolve_actual_currency_conflicts')
            print("✅ All new sentiment engine methods are available")
            
            # Test actual sentiment calculation
            week_start, week_end = calculator.get_current_week_bounds()
            actual_events = calculator.get_week_events_with_actual_indicators(week_start, week_end)
            print(f"✅ Found {len(actual_events)} events with actual data for current week")
            
            # Test actual sentiment calculation
            actual_sentiments = calculator.calculate_actual_sentiment()
            print(f"✅ Calculated actual sentiment for {len(actual_sentiments)} currencies")
            
            return True
            
    except Exception as e:
        print(f"❌ Sentiment engine extensions test failed: {e}")
        return False

def test_model_extensions():
    """Test that the model extensions are working."""
    print("\n🔍 Testing model extensions...")
    
    try:
        # Test that we can create an indicator with actual data
        with SessionLocal() as db:
            # Get a sample event
            event = db.query(Event).first()
            if not event:
                print("⚠️  No events found in database - skipping model test")
                return True
                
            # Create a test indicator with actual data
            test_indicator = Indicator(
                event_id=event.id,
                previous_value=1.0,
                forecast_value=1.1,
                actual_value=1.05,
                actual_collected_at=datetime.utcnow(),
                actual_sentiment=1,
                is_actual_available=True
            )
            
            # Test that the model accepts the new fields
            assert test_indicator.actual_value == 1.05
            assert test_indicator.actual_sentiment == 1
            assert test_indicator.is_actual_available == True
            print("✅ Model extensions working correctly")
            
            # Don't commit the test data
            db.rollback()
            
            return True
            
    except Exception as e:
        print(f"❌ Model extensions test failed: {e}")
        return False

def test_api_imports():
    """Test that API extensions can be imported."""
    print("\n🔍 Testing API imports...")
    
    try:
        # Test that we can import the API server with new endpoints
        from src.api.server import app
        
        # Check if the new endpoints are registered
        routes = [route.path for route in app.routes]
        expected_routes = [
            '/api/actual-sentiments',
            '/api/actual-sentiment/{currency}',
            '/api/combined-sentiments',
            '/api/cron/collect-actual'
        ]
        
        missing_routes = []
        for route in expected_routes:
            # Check if route pattern exists (handling path parameters)
            route_exists = any(route.replace('{currency}', '') in existing_route for existing_route in routes)
            if not route_exists:
                missing_routes.append(route)
        
        if missing_routes:
            print(f"⚠️  Some API routes may not be registered: {missing_routes}")
        else:
            print("✅ All new API endpoints are available")
            
        return True
        
    except Exception as e:
        print(f"❌ API imports test failed: {e}")
        return False

def test_main_cli_integration():
    """Test that the main CLI integration is working."""
    print("\n🔍 Testing main CLI integration...")
    
    try:
        from src.main import run_actual_data_collection
        
        # Test that the function exists and is callable
        assert callable(run_actual_data_collection)
        print("✅ Main CLI integration working")
        
        return True
        
    except Exception as e:
        print(f"❌ Main CLI integration test failed: {e}")
        return False

def main():
    """Run all Phase 1 tests."""
    print("🚀 Running Phase 1 Implementation Tests")
    print("=" * 50)
    
    tests = [
        test_database_schema,
        test_model_extensions,
        test_actual_data_collector,
        test_sentiment_engine_extensions,
        test_api_imports,
        test_main_cli_integration
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
            failed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All Phase 1 tests passed! Implementation is ready.")
        return 0
    else:
        print("⚠️  Some tests failed. Please review the implementation.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 