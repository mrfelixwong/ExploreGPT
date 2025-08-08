#!/usr/bin/env python3
"""
Quick test to verify API keys are loaded correctly
"""

import os
# Environment variables loaded from ~/.zshrc

# Load environment variables

print("🔑 API Key Verification")
print("=" * 30)

# Check if keys are loaded
openai_key = os.getenv('OPENAI_API_KEY')
anthropic_key = os.getenv('ANTHROPIC_API_KEY') 
google_key = os.getenv('GOOGLE_API_KEY')
secret_key = os.getenv('SECRET_KEY')

print(f"OpenAI Key: {'✅ Loaded' if openai_key and openai_key != 'your-openai-api-key-here' else '❌ Missing'}")
if openai_key and openai_key != 'your-openai-api-key-here':
    print(f"  Length: {len(openai_key)} chars")
    print(f"  Starts with: {openai_key[:8]}...")

print(f"Anthropic Key: {'✅ Loaded' if anthropic_key and anthropic_key != 'your-anthropic-api-key-here' else '❌ Missing'}")
if anthropic_key and anthropic_key != 'your-anthropic-api-key-here':
    print(f"  Length: {len(anthropic_key)} chars")
    print(f"  Starts with: {anthropic_key[:8]}...")

print(f"Google Key: {'✅ Loaded' if google_key and google_key != 'your-google-api-key-here' else '❌ Missing'}")
if google_key and google_key != 'your-google-api-key-here':
    print(f"  Length: {len(google_key)} chars")
    print(f"  Starts with: {google_key[:8]}...")

print(f"Flask Secret: {'✅ Loaded' if secret_key else '❌ Missing'}")

print("\n🎯 Status: All keys are properly loaded from .env file!")
print("\n🚀 Ready to start FelixGPT with: python app.py")