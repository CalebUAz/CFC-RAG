#!/usr/bin/env python3
"""
Health Check Script for Sermon RAG Application
This script checks if the application is running correctly and all services are healthy.
"""

import requests
import sys
import time
import json
from urllib.parse import urljoin

def check_health(url, timeout=30):
    """Check the health endpoint of the application."""
    try:
        response = requests.get(urljoin(url, '/health/'), timeout=timeout)
        if response.status_code == 200:
            return True, response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
        else:
            return False, f"Health check failed with status code: {response.status_code}"
    except requests.exceptions.RequestException as e:
        return False, f"Health check failed: {str(e)}"

def check_query(url, timeout=60):
    """Test a simple query to ensure the RAG system is working."""
    try:
        test_question = "What does the Bible teach about love?"
        response = requests.post(
            urljoin(url, '/api/query/'),
            json={'question': test_question},
            timeout=timeout,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            data = response.json()
            if 'answer' in data and data['answer']:
                return True, "Query test successful"
            else:
                return False, "Query returned empty answer"
        else:
            return False, f"Query test failed with status code: {response.status_code}"
    except requests.exceptions.RequestException as e:
        return False, f"Query test failed: {str(e)}"

def check_static_files(url, timeout=10):
    """Check if static files are being served correctly."""
    try:
        # Check if the main page loads (which includes static files)
        response = requests.get(url, timeout=timeout)
        if response.status_code == 200:
            return True, "Static files are being served correctly"
        else:
            return False, f"Main page failed to load with status code: {response.status_code}"
    except requests.exceptions.RequestException as e:
        return False, f"Static files check failed: {str(e)}"

def main():
    """Main health check function."""
    if len(sys.argv) < 2:
        print("Usage: python health_check.py <app_url>")
        print("Example: python health_check.py https://sermon-rag.fly.dev")
        sys.exit(1)
    
    app_url = sys.argv[1].rstrip('/')
    
    print(f"🔍 Running health checks for: {app_url}")
    print("=" * 50)
    
    checks = [
        ("Health Endpoint", lambda: check_health(app_url)),
        ("Static Files", lambda: check_static_files(app_url)),
        ("RAG Query System", lambda: check_query(app_url)),
    ]
    
    all_passed = True
    
    for check_name, check_func in checks:
        print(f"\n📋 Testing: {check_name}")
        try:
            passed, message = check_func()
            if passed:
                print(f"✅ {check_name}: PASSED")
                print(f"   {message}")
            else:
                print(f"❌ {check_name}: FAILED")
                print(f"   {message}")
                all_passed = False
        except Exception as e:
            print(f"❌ {check_name}: ERROR")
            print(f"   Unexpected error: {str(e)}")
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 All health checks passed! Your application is running correctly.")
        sys.exit(0)
    else:
        print("⚠️  Some health checks failed. Please check your application configuration.")
        sys.exit(1)

if __name__ == "__main__":
    main() 