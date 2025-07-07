#!/usr/bin/env python3
"""
Simple startup test script for CFC RAG Service
This script tests basic Django functionality without starting the full server
"""

import os
import sys
import django
from pathlib import Path

def test_django_setup():
    """Test basic Django setup."""
    print("🔧 Testing Django setup...")
    
    # Add the project directory to Python path
    project_dir = Path(__file__).parent
    sys.path.insert(0, str(project_dir))
    
    # Set Django settings
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sermon_rag.settings')
    
    try:
        django.setup()
        print("✅ Django setup successful")
        return True
    except Exception as e:
        print(f"❌ Django setup failed: {e}")
        return False

def test_database():
    """Test database connectivity."""
    print("📊 Testing database...")
    
    try:
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        print("✅ Database connection successful")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def test_settings():
    """Test Django settings."""
    print("⚙️ Testing Django settings...")
    
    try:
        from django.conf import settings
        
        # Check required settings
        required_settings = [
            'SECRET_KEY',
            'DATABASES',
            'INSTALLED_APPS',
            'MIDDLEWARE',
        ]
        
        for setting in required_settings:
            if not hasattr(settings, setting):
                print(f"❌ Missing setting: {setting}")
                return False
        
        print("✅ Django settings are valid")
        return True
    except Exception as e:
        print(f"❌ Settings test failed: {e}")
        return False

def test_rag_service():
    """Test RAG service initialization."""
    print("🤖 Testing RAG service...")
    
    try:
        from rag.services import get_rag_service
        
        # Get service instance (this will trigger lazy initialization)
        rag_service = get_rag_service()
        print("✅ RAG service instance created")
        
        # Check if it's ready (this will try to initialize components)
        is_ready = rag_service.is_ready()
        print(f"📊 RAG service ready: {is_ready}")
        
        return True
    except Exception as e:
        print(f"❌ RAG service test failed: {e}")
        return False

def test_health_endpoints():
    """Test health endpoint views."""
    print("🏥 Testing health endpoints...")
    
    try:
        from django.test import RequestFactory
        from rag.views import health_check, health_check_detailed
        
        factory = RequestFactory()
        
        # Test basic health check
        request = factory.get('/health/')
        response = health_check(request)
        print(f"✅ Basic health check: {response.status_code}")
        
        # Test detailed health check
        request = factory.get('/health/detailed/')
        response = health_check_detailed(request)
        print(f"✅ Detailed health check: {response.status_code}")
        
        return True
    except Exception as e:
        print(f"❌ Health endpoint test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🚀 Starting CFC RAG Service startup tests...")
    print("=" * 50)
    
    tests = [
        ("Django Setup", test_django_setup),
        ("Django Settings", test_settings),
        ("Database", test_database),
        ("Health Endpoints", test_health_endpoints),
        ("RAG Service", test_rag_service),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n📋 Running {test_name} test...")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    print("=" * 50)
    
    all_passed = True
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
        if not result:
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 All tests passed! Application should start successfully.")
        return 0
    else:
        print("⚠️ Some tests failed. Check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 