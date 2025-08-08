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

from models.debug_logger import get_debugger, is_claude_debug_enabled

def test_debug_logging():
    """Test basic debug logging functionality"""
    print("🧪 Testing Debug System")
    print("=" * 50)
    
    # Check Claude debug mode
    claude_debug = is_claude_debug_enabled()
    print(f"Claude Debug Mode: {'ENABLED' if claude_debug else 'DISABLED'}")
    
    if claude_debug:
        print("📁 Log file: /tmp/exploregpt_logs/exploregpt_debug.log")
        print("🖥️  Console logging: ENABLED")
    else:
        print("💡 To enable Claude debug mode: export CLAUDE_DEBUG=1")
    
    print()
    
    # Initialize debugger
    session_id = "test_session_123"
    debugger = get_debugger(session_id)
    
    # Test different types of logging
    print("🔄 Testing logging capabilities...")
    
    # User action
    debugger.log_user_action("test_action", {
        "test_parameter": "test_value",
        "timestamp": "test_time"
    })
    
    # API call simulation
    start_time = time.time()
    time.sleep(0.1)  # Simulate API call
    debugger.log_api_call(
        provider="openai",
        model="gpt-3.5-turbo",
        message_length=100,
        start_time=start_time,
        success=True,
        response_data={"tokens": {"input": 50, "output": 30}}
    )
    
    # Search activity simulation
    debugger.log_search_activity(
        query="test search",
        provider="DuckDuckGoProvider",
        results_count=5,
        duration_ms=250.5,
        success=True
    )
    
    # Error logging
    debugger.log_error(
        error_type="test_error",
        error_message="This is a test error for debugging",
        context={"test_context": "example"}
    )
    
    # Streaming event
    debugger.log_streaming_event("start", "openai")
    debugger.log_streaming_event("chunk", "openai", chunk_size=25)
    debugger.log_streaming_event("end", "openai", total_chunks=10)
    
    print("✅ Logged various event types")
    
    # Generate session summary
    summary = debugger.get_session_summary()
    print(f"📊 Session Duration: {summary['duration_seconds']:.2f} seconds")
    
    # Create debug snapshot
    snapshot = debugger.create_debug_snapshot()
    print(f"📸 Debug snapshot created with {len(snapshot)} keys")
    
    print()
    print("=" * 50)
    print("✨ Debug system test complete!")
    
    if claude_debug:
        print("📂 Check log file at: /tmp/exploregpt_logs/exploregpt_debug.log")
        print("🌐 When running the app, visit: http://localhost:5001/settings")
        print("   Look for the '🐛 Debug Information' section")
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
        
        result = is_claude_debug_enabled()
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