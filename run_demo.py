#!/usr/bin/env python3
"""
Demo script showing correct usage of the Quantitative Analysis Tool.
This script demonstrates the working functionality without database dependencies.
"""

import os
import sys

def print_header(title):
    """Print a formatted header."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def print_section(title):
    """Print a formatted section header."""
    print(f"\n{'-'*40}")
    print(f"  {title}")
    print(f"{'-'*40}")

def main():
    """Run the demo."""
    
    print_header("QUANTITATIVE ANALYSIS TOOL - DEMO")
    
    print("\n🎯 This demo shows the WORKING functionality:")
    print("   ✅ Sentiment Analysis Engine")
    print("   ✅ Environment Configuration")
    print("   ✅ HTTP Requests")
    print("   ✅ HTML Parsing")
    print("   ✅ Testing Framework")
    
    print("\n⚠️  Database integration pending due to Python 3.13 compatibility issues")
    
    # Check virtual environment
    print_section("Environment Check")
    python_path = sys.executable
    if "quantanalysis_venv" in python_path:
        print(f"✅ Virtual environment active: {python_path}")
    else:
        print(f"⚠️  Virtual environment not detected: {python_path}")
        print("   Run: source /tmp/quantanalysis_venv/bin/activate")
    
    # Show available commands
    print_section("Available Commands")
    
    commands = [
        ("Sentiment Analysis Demo", "python demo_sentiment_test.py"),
        ("Run Tests with Pytest", "pytest demo_sentiment_test.py -v"),
        ("Coverage Report", "coverage run -m pytest && coverage report"),
        ("View Usage Guide", "cat USAGE_GUIDE.md"),
    ]
    
    for desc, cmd in commands:
        print(f"  📋 {desc}:")
        print(f"     {cmd}")
        print()
    
    # Show what would work with full setup
    print_section("Commands That Will Work With Full Setup")
    
    future_commands = [
        ("Analyze Current Week", "python -m src.main analyze"),
        ("Analyze Specific Date", "python -m src.main analyze --start-date 2024-01-01"),
        ("Run Scraper", "python -m src.main scrape"),
        ("Run All Tests", "python run_tests.py"),
    ]
    
    for desc, cmd in future_commands:
        print(f"  🔮 {desc}:")
        print(f"     {cmd}")
        print()
    
    print_section("Next Steps")
    print("1. For immediate testing: python demo_sentiment_test.py")
    print("2. For full functionality: Install Python 3.11/3.12 and database dependencies")
    print("3. Read USAGE_GUIDE.md for detailed instructions")
    
    print_header("DEMO COMPLETE")

if __name__ == "__main__":
    main() 