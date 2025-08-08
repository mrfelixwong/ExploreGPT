#!/usr/bin/env python3
"""
Test just Anthropic API with different approaches
"""

import os
# Environment variables loaded from ~/.zshrc


def test_anthropic_v1():
    """Test with newer API"""
    print("🧠 Testing Anthropic API v1 (newer)...")
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
        response = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=10,
            messages=[{"role": "user", "content": "Say 'Hello from Anthropic!'"}]
        )
        print(f"✅ Anthropic v1: {response.content[0].text.strip()}")
        return True
    except Exception as e:
        print(f"❌ Anthropic v1 Error: {str(e)}")
        return False

def test_anthropic_v0():
    """Test with older API"""
    print("🧠 Testing Anthropic API v0 (older)...")
    try:
        import anthropic
        client = anthropic.Client(api_key=os.getenv('ANTHROPIC_API_KEY'))
        response = client.completions.create(
            model="claude-instant-1",
            prompt="Human: Say 'Hello from Anthropic!'\n\nAssistant:",
            max_tokens_to_sample=10
        )
        print(f"✅ Anthropic v0: {response.completion.strip()}")
        return True
    except Exception as e:
        print(f"❌ Anthropic v0 Error: {str(e)}")
        return False

def test_anthropic_simple():
    """Test with simplest possible approach"""
    print("🧠 Testing Anthropic API (simple)...")
    try:
        import anthropic
        # Try to just initialize the client
        client = anthropic.Client(api_key=os.getenv('ANTHROPIC_API_KEY'))
        print("✅ Anthropic client initialized successfully")
        return True
    except Exception as e:
        print(f"❌ Anthropic simple Error: {str(e)}")
        return False

def main():
    print("🔑 Testing Anthropic API with multiple approaches")
    print("=" * 50)
    
    # Test different approaches
    results = []
    results.append(("Simple Init", test_anthropic_simple()))
    results.append(("V0 API", test_anthropic_v0()))
    results.append(("V1 API", test_anthropic_v1()))
    
    print("\n" + "=" * 50)
    print("📊 Results:")
    for name, result in results:
        status = "✅" if result else "❌"
        print(f"  {status} {name}: {'Working' if result else 'Failed'}")
    
    working_count = sum(result for _, result in results)
    if working_count > 0:
        print(f"\n🎉 Found {working_count} working approach(es)!")
    else:
        print(f"\n❌ No working approaches found")

if __name__ == '__main__':
    main()