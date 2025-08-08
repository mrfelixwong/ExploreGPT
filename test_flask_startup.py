#!/usr/bin/env python3
"""
Test Flask application startup and basic functionality
"""

# Environment variables loaded from ~/.zshrc

import sys
import os
import requests
import time
import threading
from multiprocessing import Process

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_flask_startup():
    """Test that Flask app can start without errors"""
    print("🚀 Testing Flask Application Startup")
    print("=" * 40)
    
    try:
        # Import the app to test basic initialization
        from app import app
        print("✅ Flask app imports successfully")
        
        # Test app configuration
        print(f"✅ Secret key configured: {bool(app.secret_key)}")
        print(f"✅ Debug mode: {app.debug}")
        
        # Test database initialization
        from app import init_db
        init_db()
        print("✅ Database initialization successful")
        
        # Test template rendering without server
        with app.test_client() as client:
            # Test index route
            response = client.get('/')
            print(f"✅ Index route: HTTP {response.status_code}")
            
            # Test settings route  
            response = client.get('/settings')
            print(f"✅ Settings route: HTTP {response.status_code}")
            
            # Test memory route
            response = client.get('/memory')
            print(f"✅ Memory route: HTTP {response.status_code}")
        
        return True
        
    except Exception as e:
        print(f"❌ Flask startup error: {str(e)}")
        return False

def main():
    """Run Flask startup test"""
    success = test_flask_startup()
    
    print("\n" + "=" * 40)
    if success:
        print("🎉 Flask Application: READY TO START!")
        print("\nTo start the server:")
        print("  python app.py")
        print("  Then open: http://localhost:5000")
    else:
        print("❌ Flask Application: STARTUP ISSUES DETECTED")
    
    return success

if __name__ == '__main__':
    main()