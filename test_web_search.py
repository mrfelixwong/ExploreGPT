#!/usr/bin/env python3
"""
Test web search functionality
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models.web_search import web_search_manager

def test_search_intent_detection():
    """Test search intent detection"""
    print("🔍 Testing Search Intent Detection")
    print("=" * 40)
    
    test_messages = [
        ("search for latest AI news", True),
        ("what's the latest on OpenAI", True),
        ("find information about Python", True),
        ("hello how are you", False),
        ("explain quantum physics", False),
        ("current news about climate change", True),
        ("what happened today", True),
        ("calculate 2+2", False)
    ]
    
    for message, expected in test_messages:
        result = web_search_manager.should_search(message)
        status = "✅" if result == expected else "❌"
        print(f"{status} '{message}' → {result} (expected {expected})")
    
    print()

def test_query_extraction():
    """Test query extraction"""
    print("📝 Testing Query Extraction")
    print("=" * 40)
    
    test_messages = [
        "search for latest AI developments",
        "what is the current weather in Tokyo",
        "find information about machine learning",
        "tell me about recent OpenAI news"
    ]
    
    for message in test_messages:
        extracted = web_search_manager.intent_detector.extract_query(message)
        print(f"'{message}'")
        print(f"   → '{extracted}'")
        print()

def test_duckduckgo_search():
    """Test DuckDuckGo search (free fallback)"""
    print("🦆 Testing DuckDuckGo Search")
    print("=" * 40)
    
    results = web_search_manager.search("OpenAI", count=3)
    
    if results:
        print(f"✅ Found {len(results)} results:")
        for i, result in enumerate(results, 1):
            print(f"{i}. {result.title}")
            print(f"   URL: {result.url}")
            print(f"   Snippet: {result.snippet[:100]}...")
            print()
    else:
        print("⚠️ No results found (this is expected without API keys)")
    
    print()

def main():
    """Run all web search tests"""
    print("🚀 Testing Web Search Integration")
    print("==================================================")
    
    test_search_intent_detection()
    test_query_extraction()
    test_duckduckgo_search()
    
    print("==================================================")
    print("🎉 Web Search Testing Complete!")
    print()
    print("💡 To enable full web search with more results:")
    print("   1. Get a Brave Search API key")
    print("   2. Set it in your environment or settings")
    print("   3. Enjoy unlimited web search capabilities!")

if __name__ == '__main__':
    main()