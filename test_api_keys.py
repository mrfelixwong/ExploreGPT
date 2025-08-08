#!/usr/bin/env python3
"""
Test all API keys with actual API calls
"""

import os
# Environment variables loaded from ~/.zshrc
import openai
import anthropic
import google.generativeai as genai

# Load environment variables

def test_openai():
    """Test OpenAI API key"""
    print("🤖 Testing OpenAI API...")
    try:
        client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Say 'Hello from OpenAI!'"}],
            max_tokens=10
        )
        print(f"✅ OpenAI: {response.choices[0].message.content.strip()}")
        return True
    except Exception as e:
        print(f"❌ OpenAI Error: {str(e)}")
        return False

def test_anthropic():
    """Test Anthropic API key"""
    print("🧠 Testing Anthropic API...")
    try:
        client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
        response = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=10,
            messages=[{"role": "user", "content": "Say 'Hello from Anthropic!'"}]
        )
        print(f"✅ Anthropic: {response.content[0].text.strip()}")
        return True
    except Exception as e:
        print(f"❌ Anthropic Error: {str(e)}")
        return False

def test_google():
    """Test Google API key"""
    print("🔍 Testing Google API...")
    try:
        genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))
        # Try gemini-1.5-flash instead of gemini-pro
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content("Say 'Hello from Google!'")
        print(f"✅ Google: {response.text.strip()}")
        return True
    except Exception as e:
        print(f"❌ Google Error: {str(e)}")
        # Try listing available models
        try:
            print("  📋 Available models:")
            for m in genai.list_models():
                if 'generateContent' in m.supported_generation_methods:
                    print(f"    - {m.name}")
                    break
        except:
            pass
        return False

def main():
    print("🔑 Testing All API Keys with Real API Calls")
    print("=" * 50)
    
    results = {
        'openai': test_openai(),
        'anthropic': test_anthropic(), 
        'google': test_google()
    }
    
    print("\n" + "=" * 50)
    print("📊 API Test Results:")
    
    working_count = sum(results.values())
    total_count = len(results)
    
    for provider, status in results.items():
        status_icon = "✅" if status else "❌"
        print(f"  {status_icon} {provider.title()}: {'Working' if status else 'Failed'}")
    
    print(f"\n🎯 Overall Status: {working_count}/{total_count} APIs working")
    
    if working_count == total_count:
        print("🎉 All API keys are working perfectly!")
        print("🚀 Ready to start FelixGPT with: python app.py")
    elif working_count > 0:
        print(f"⚠️  {working_count} API(s) working, {total_count - working_count} need attention")
        print("🚀 You can still run FelixGPT with the working APIs")
    else:
        print("❌ No APIs are working. Please check your API keys.")
    
    return working_count > 0

if __name__ == '__main__':
    main()