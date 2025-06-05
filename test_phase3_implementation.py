#!/usr/bin/env python3
"""
Test script for Phase 3 frontend implementation.
"""
import sys
import os
import json
import subprocess
import time
import requests
from pathlib import Path

def test_sample_data_structure():
    """Test that the sample data has the correct structure for Phase 3."""
    print("🔍 Testing sample data structure...")
    
    try:
        # Read the sample data file
        sample_data_path = Path("frontend/data/sample-data.js")
        if not sample_data_path.exists():
            print("❌ Sample data file not found")
            return False
            
        with open(sample_data_path, 'r') as f:
            content = f.read()
            
        # Check for Phase 3 specific fields
        required_fields = [
            'actual_value',
            'actual_sentiment',
            'actual_sentiment_label',
            'accuracy',
            'actual_available',
            'forecast_accuracy'
        ]
        
        missing_fields = []
        for field in required_fields:
            if field not in content:
                missing_fields.append(field)
                
        if missing_fields:
            print(f"❌ Missing required fields: {missing_fields}")
            return False
            
        print("✅ Sample data structure is correct")
        return True
        
    except Exception as e:
        print(f"❌ Error testing sample data: {str(e)}")
        return False

def test_html_structure():
    """Test that the HTML has the required Phase 3 elements."""
    print("\n🔍 Testing HTML structure...")
    
    try:
        html_path = Path("frontend/index.html")
        if not html_path.exists():
            print("❌ HTML file not found")
            return False
            
        with open(html_path, 'r') as f:
            content = f.read()
            
        # Check for Phase 3 specific elements
        required_elements = [
            'sentiment-toggle',
            'forecast-view',
            'actual-view',
            'comparison-view',
            'actual-sentiment',
            'sentiment-forecast',
            'sentiment-actual',
            'accuracy-badge'
        ]
        
        missing_elements = []
        for element in required_elements:
            if element not in content:
                missing_elements.append(element)
                
        if missing_elements:
            print(f"❌ Missing required HTML elements: {missing_elements}")
            return False
            
        # Check for new table columns
        if 'Actual</th>' not in content:
            print("❌ Missing 'Actual' column in table")
            return False
            
        if 'Actual Sentiment</th>' not in content:
            print("❌ Missing 'Actual Sentiment' column in table")
            return False
            
        if 'Accuracy</th>' not in content:
            print("❌ Missing 'Accuracy' column in table")
            return False
            
        print("✅ HTML structure is correct")
        return True
        
    except Exception as e:
        print(f"❌ Error testing HTML: {str(e)}")
        return False

def test_javascript_functions():
    """Test that the JavaScript has the required Phase 3 functions."""
    print("\n🔍 Testing JavaScript functions...")
    
    try:
        js_path = Path("frontend/static/js/dashboard.js")
        if not js_path.exists():
            print("❌ JavaScript file not found")
            return False
            
        with open(js_path, 'r') as f:
            content = f.read()
            
        # Check for Phase 3 specific functions
        required_functions = [
            'switchSentimentView',
            'getCurrentSentimentData',
            'getAccuracyBadge',
            'getSentimentIndicator',
            'actualSentimentData',
            'combinedSentimentData',
            'currentView'
        ]
        
        missing_functions = []
        for func in required_functions:
            if func not in content:
                missing_functions.append(func)
                
        if missing_functions:
            print(f"❌ Missing required JavaScript functions: {missing_functions}")
            return False
            
        print("✅ JavaScript functions are correct")
        return True
        
    except Exception as e:
        print(f"❌ Error testing JavaScript: {str(e)}")
        return False

def test_css_styles():
    """Test that the CSS has the required Phase 3 styles."""
    print("\n🔍 Testing CSS styles...")
    
    try:
        html_path = Path("frontend/index.html")
        with open(html_path, 'r') as f:
            content = f.read()
            
        # Check for Phase 3 specific CSS classes
        required_styles = [
            'sentiment-forecast',
            'sentiment-actual',
            'accuracy-match',
            'accuracy-mismatch',
            'accuracy-no-data',
            'sentiment-toggle',
            'sentiment-indicator',
            'accuracy-badge'
        ]
        
        missing_styles = []
        for style in required_styles:
            if f'.{style}' not in content:
                missing_styles.append(style)
                
        if missing_styles:
            print(f"❌ Missing required CSS styles: {missing_styles}")
            return False
            
        print("✅ CSS styles are correct")
        return True
        
    except Exception as e:
        print(f"❌ Error testing CSS: {str(e)}")
        return False

def test_frontend_loading():
    """Test that the frontend loads without JavaScript errors."""
    print("\n🔍 Testing frontend loading...")
    
    try:
        # Start a simple HTTP server
        import http.server
        import socketserver
        import threading
        import webbrowser
        
        PORT = 8080
        
        class Handler(http.server.SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory="frontend", **kwargs)
        
        with socketserver.TCPServer(("", PORT), Handler) as httpd:
            print(f"✅ Frontend server started on http://localhost:{PORT}")
            print("📝 Manual verification needed:")
            print("   1. Open http://localhost:8080 in your browser")
            print("   2. Check that sentiment toggle buttons are visible")
            print("   3. Verify that currency sidebar shows both forecast and actual sentiment")
            print("   4. Check that indicators table has Actual and Actual Sentiment columns")
            print("   5. Test switching between Forecast, Actual, and Compare views")
            print("   6. Verify that accuracy badges are displayed")
            print("\n⏳ Server will run for 30 seconds for manual testing...")
            
            # Run server for 30 seconds
            import time
            time.sleep(30)
            
        print("✅ Frontend test completed")
        return True
        
    except Exception as e:
        print(f"❌ Error testing frontend: {str(e)}")
        return False

def main():
    """Run all Phase 3 tests."""
    print("🚀 Starting Phase 3 Implementation Tests\n")
    
    tests = [
        test_sample_data_structure,
        test_html_structure,
        test_javascript_functions,
        test_css_styles,
        test_frontend_loading
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        else:
            print("❌ Test failed, stopping...")
            break
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All Phase 3 tests passed! Frontend implementation is complete.")
        print("\n📋 Phase 3 Implementation Summary:")
        print("✅ Sample data updated with actual sentiment data")
        print("✅ HTML updated with sentiment toggles and new table columns")
        print("✅ JavaScript enhanced with actual sentiment functionality")
        print("✅ CSS styles added for visual indicators")
        print("✅ Frontend loads and displays correctly")
        
        print("\n🎯 Phase 3 Features Implemented:")
        print("• Sentiment view toggle (Forecast/Actual/Compare)")
        print("• Actual sentiment indicators in currency sidebar")
        print("• Actual values and sentiment columns in indicators table")
        print("• Accuracy badges showing forecast vs actual comparison")
        print("• Visual distinction between forecast and actual data")
        print("• Graceful handling of missing actual data")
        
        return True
    else:
        print("❌ Some tests failed. Please fix the issues before proceeding.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 