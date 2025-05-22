#!/usr/bin/env python3
"""
Script for running the tests.
"""
import os
import sys
import argparse
import unittest
import coverage

def parse_args():
    """
    Parse command-line arguments.
    
    Returns:
        argparse.Namespace: Parsed arguments.
    """
    parser = argparse.ArgumentParser(description="Run tests for Forex Factory Sentiment Analyzer")
    
    parser.add_argument("--with-coverage", action="store_true", help="Run tests with coverage")
    parser.add_argument("--html-report", action="store_true", help="Generate HTML coverage report")
    parser.add_argument("--module", help="Run tests for a specific module (e.g., scraper, utils)")
    
    return parser.parse_args()

def run_tests(module=None):
    """
    Run the tests.
    
    Args:
        module (str, optional): Run tests for a specific module.
        
    Returns:
        bool: True if all tests pass, False otherwise.
    """
    test_loader = unittest.TestLoader()
    
    if module:
        test_suite = test_loader.discover(f"tests/{module}", pattern="test_*.py")
    else:
        test_suite = test_loader.discover("tests", pattern="test_*.py")
    
    test_runner = unittest.TextTestRunner(verbosity=2)
    result = test_runner.run(test_suite)
    
    return result.wasSuccessful()

def run_tests_with_coverage(module=None, html_report=False):
    """
    Run the tests with coverage.
    
    Args:
        module (str, optional): Run tests for a specific module.
        html_report (bool): Generate HTML coverage report.
        
    Returns:
        bool: True if all tests pass, False otherwise.
    """
    cov = coverage.Coverage(
        source=["src"],
        omit=["*/test*", "*/venv/*", "setup.py"]
    )
    
    cov.start()
    success = run_tests(module)
    cov.stop()
    cov.save()
    
    print("\nCoverage report:")
    cov.report()
    
    if html_report:
        cov.html_report(directory="htmlcov")
        print(f"\nHTML coverage report generated in 'htmlcov' directory")
    
    return success

def main():
    """
    Main entry point.
    
    Returns:
        int: Exit code (0 for success, 1 for failure).
    """
    args = parse_args()
    
    if args.with_coverage:
        success = run_tests_with_coverage(args.module, args.html_report)
    else:
        success = run_tests(args.module)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main()) 