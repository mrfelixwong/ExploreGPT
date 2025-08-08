#!/usr/bin/env python3
"""
Test the ExploreGPT debug system

Run this script to test the debugging capabilities:
1. Normal mode: python test_debug_system.py
2. Claude debug mode: CLAUDE_DEBUG=1 python test_debug_system.py
"""

import os
import sys
import time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models.debug_logger import debugger, debug_log, debug_api_call, debug_search, debug_error, is_debug_enabled

def test_debug_logging():
    """Test basic debug logging functionality"""
    print("🧪 Testing Debug System")
    print("=" * 50)
    
    # Check debug mode
    debug_enabled = is_debug_enabled()
    print(f"Debug Mode: {'ENABLED' if debug_enabled else 'DISABLED'}")
    
    if debug_enabled:
        print("📁 Log file: /tmp/exploregpt_logs/exploregpt_debug.log")
    else:
        print("💡 To enable debug mode: export CLAUDE_DEBUG=1")
    
    print()
    
    # Test different types of logging
    print("🔄 Testing logging capabilities...")
    
    # Basic logging
    debug_log("test_event", {"test_parameter": "test_value"})
    
    # API call simulation
    time.sleep(0.1)  # Simulate API call
    debug_api_call("openai", True, 123.5, model="gpt-3.5-turbo", tokens={"input": 50, "output": 30})
    debug_api_call("anthropic", False, 245.8, model="claude-3-sonnet", error="Rate limit exceeded")
    
    # Search activity simulation
    debug_search("test search", "DuckDuckGoProvider", 5, True, 250.5)
    debug_search("failed search", "BraveSearchProvider", 0, False, 1200.0, "API key invalid")
    
    # Error logging
    debug_error("test_error", "This is a test error for debugging", {"test_context": "example"})
    
    print("✅ Logged various event types")
    
    print()
    print("=" * 50)
    print("✨ Debug system test complete!")
    
    if debug_enabled:
        print("📂 Check log file at: /tmp/exploregpt_logs/exploregpt_debug.log")
        print("🌐 When running the app, debug info will be in settings")
    else:
        print("💡 To see enhanced debugging:")
        print("   export CLAUDE_DEBUG=1")
        print("   python test_debug_system.py")

def test_environment_detection():
    """Test environment variable detection"""
    print("\n🔍 Environment Detection Test")
    print("-" * 30)
    
    # Test various environment values
    test_values = ['1', 'true', 'True', 'TRUE', 'yes', 'Yes', '0', 'false', 'no', None]
    
    original_value = os.environ.get('CLAUDE_DEBUG')
    
    for value in test_values:
        if value is None:
            if 'CLAUDE_DEBUG' in os.environ:
                del os.environ['CLAUDE_DEBUG']
        else:
            os.environ['CLAUDE_DEBUG'] = value
        
        result = is_debug_enabled()
        expected = value in ('1', 'true', 'True', 'TRUE', 'yes', 'Yes') if value else False
        status = "✅" if result == expected else "❌"
        
        print(f"{status} CLAUDE_DEBUG='{value}' → {result}")
    
    # Restore original value
    if original_value:
        os.environ['CLAUDE_DEBUG'] = original_value
    elif 'CLAUDE_DEBUG' in os.environ:
        del os.environ['CLAUDE_DEBUG']

if __name__ == '__main__':
    test_debug_logging()
    test_environment_detection()