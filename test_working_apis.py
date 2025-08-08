#!/usr/bin/env python3
"""
Test the working APIs (OpenAI + Google) with a real message
"""

# Environment variables loaded from ~/.zshrc

from models.settings import settings_manager
from models.llm_clients import LLMOrchestrator

def test_working_apis():
    print("🚀 Testing Working APIs with Real Message")
    print("=" * 50)
    
    # Load settings and create orchestrator
    settings = settings_manager.load_settings()
    orchestrator = LLMOrchestrator(settings)
    
    # Test message
    test_message = "Hello! Please introduce yourself in one sentence."
    print(f"📝 Test message: '{test_message}'")
    print()
    
    # Get responses from working providers only
    enabled_providers = orchestrator._get_enabled_providers()
    print(f"🎯 Enabled providers: {enabled_providers}")
    print()
    
    # Test each provider individually to avoid batch issues
    results = {}
    for provider in enabled_providers:
        if provider in orchestrator.clients:
            print(f"🤖 Testing {provider.title()}...")
            try:
                if provider == 'openai':
                    result = orchestrator._call_openai(test_message)
                elif provider == 'google':
                    result = orchestrator._call_google(test_message)
                else:
                    continue
                    
                if result['success']:
                    print(f"✅ {provider.title()}: {result['response']}")
                    print(f"   ⏱️ Latency: {result['latency']}ms")
                    if 'estimated_cost' in result:
                        print(f"   💰 Cost: ${result['estimated_cost']:.4f}")
                else:
                    print(f"❌ {provider.title()}: {result['response']}")
                    
                results[provider] = result
                print()
                
            except Exception as e:
                print(f"❌ {provider.title()} Error: {str(e)}")
                results[provider] = {'success': False, 'error': str(e)}
                print()
    
    # Summary
    working_count = sum(1 for r in results.values() if r.get('success', False))
    print("=" * 50)
    print(f"📊 Final Results: {working_count}/{len(results)} APIs working")
    
    for provider, result in results.items():
        status = "✅" if result.get('success', False) else "❌"
        print(f"   {status} {provider.title()}")
    
    if working_count >= 2:
        print("\n🎉 Excellent! Multiple APIs working - ready for multi-LLM comparison!")
    elif working_count >= 1:
        print("\n✅ Good! At least one API working - FelixGPT functional!")
    else:
        print("\n❌ No APIs working - check your API keys")
    
    return working_count > 0

if __name__ == '__main__':
    test_working_apis()