#!/usr/bin/env python3
"""
ExploreGPT - Quick Start Script
Simple launcher that checks environment and starts the application
"""

import os
import sys

def check_environment():
    """Check if API keys are configured"""
    required_keys = ['OPENAI_API_KEY', 'GOOGLE_API_KEY', 'SECRET_KEY']
    missing_keys = [key for key in required_keys if not os.getenv(key)]
    
    if missing_keys:
        print("❌ Missing environment variables:")
        for key in missing_keys:
            print(f"   - {key}")
        print("\n📖 See API_KEYS_SETUP.md for configuration help")
        return False
    
    print("✅ Environment variables configured")
    return True

def main():
    """Main startup function"""
    print("🚀 ExploreGPT - Multi-LLM Chat Application")
    print("=" * 50)
    
    # Check environment
    if not check_environment():
        sys.exit(1)
    
    # Start the application
    print("🌐 Starting server at http://localhost:5001")
    print("🛑 Press Ctrl+C to stop\n")
    
    from app import app
    app.run(debug=True, port=5001, host='127.0.0.1')

if __name__ == '__main__':
    main()