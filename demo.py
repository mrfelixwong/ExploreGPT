#!/usr/bin/env python3
"""
FelixGPT Demo Script
Demonstrates the key components working without requiring API keys
"""

import os
import sys
import json
import tempfile
import shutil

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from models.settings import SettingsManager
from models.cost_tracker import CostTracker

def demo_settings_management():
    """Demonstrate Settings Management functionality"""
    print("\n" + "="*60)
    print("🔧 SETTINGS MANAGEMENT DEMO")
    print("="*60)
    
    # Create temporary settings file
    temp_dir = tempfile.mkdtemp()
    settings_file = os.path.join(temp_dir, 'demo_settings.json')
    
    try:
        # Initialize settings manager
        settings_manager = SettingsManager(settings_file)
        
        # 1. Load default settings
        print("1. Loading default settings...")
        default_settings = settings_manager.load_settings()
        print(f"   ✓ Loaded {len(default_settings)} setting categories")
        print(f"   ✓ Default models: {default_settings['models']}")
        
        # 2. Modify and save settings
        print("\n2. Modifying settings...")
        custom_settings = {
            'models': {
                'openai': 'gpt-3.5-turbo',  # Change from default gpt-4
                'anthropic': 'claude-3-haiku-20240307'  # Change to faster model
            },
            'cost_management': {
                'daily_budget': 10.0,  # Increase budget
                'track_costs': True
            },
            'provider_settings': {
                'google': {'enabled': False, 'priority': 3, 'fallback': False}  # Disable Google
            }
        }
        
        success = settings_manager.save_settings(custom_settings)
        print(f"   ✓ Settings saved: {success}")
        
        # 3. Load merged settings
        print("\n3. Loading merged settings...")
        merged_settings = settings_manager.load_settings()
        print(f"   ✓ OpenAI model: {merged_settings['models']['openai']}")
        print(f"   ✓ Daily budget: ${merged_settings['cost_management']['daily_budget']}")
        print(f"   ✓ Google enabled: {merged_settings['provider_settings']['google']['enabled']}")
        
        # 4. Test provider prioritization
        print("\n4. Testing provider prioritization...")
        enabled_providers = settings_manager.get_enabled_providers(merged_settings)
        print(f"   ✓ Enabled providers in order: {enabled_providers}")
        
        # 5. Test UI class generation
        print("\n5. Testing UI customization...")
        ui_classes = settings_manager.get_ui_classes(merged_settings)
        print(f"   ✓ UI classes: {ui_classes}")
        
        print("   ✅ Settings Management Demo: SUCCESS")
        
    finally:
        # Cleanup
        shutil.rmtree(temp_dir)

def demo_cost_tracking():
    """Demonstrate Cost Tracking functionality"""
    print("\n" + "="*60)
    print("💰 COST TRACKING DEMO")
    print("="*60)
    
    # Create temporary cost file
    temp_dir = tempfile.mkdtemp()
    cost_file = os.path.join(temp_dir, 'demo_costs.json')
    
    try:
        # Initialize cost tracker
        cost_tracker = CostTracker(cost_file)
        
        # 1. Test cost estimation
        print("1. Testing cost estimation...")
        gpt4_cost = cost_tracker.estimate_cost('openai', 'gpt-4', 1000, 500)
        claude_cost = cost_tracker.estimate_cost('anthropic', 'claude-3-sonnet-20240229', 1500, 300)
        gemini_cost = cost_tracker.estimate_cost('google', 'gemini-pro', 800, 200)
        
        print(f"   ✓ GPT-4 (1000 in, 500 out): ${gpt4_cost:.4f}")
        print(f"   ✓ Claude Sonnet (1500 in, 300 out): ${claude_cost:.4f}")
        print(f"   ✓ Gemini Pro (800 in, 200 out): ${gemini_cost:.4f}")
        
        # 2. Test token estimation
        print("\n2. Testing token estimation...")
        message = "Hello, this is a test message for token estimation!"
        tokens = cost_tracker.estimate_message_tokens(message)
        print(f"   ✓ Message: '{message}'")
        print(f"   ✓ Estimated tokens: {tokens}")
        
        # 3. Record some costs
        print("\n3. Recording usage costs...")
        cost_tracker.record_cost('openai', 'gpt-4', 0.12)
        cost_tracker.record_cost('openai', 'gpt-4', 0.08) 
        cost_tracker.record_cost('anthropic', 'claude-3-sonnet', 0.05)
        cost_tracker.record_cost('google', 'gemini-pro', 0.02)
        
        print("   ✓ Recorded multiple API usage costs")
        
        # 4. Generate cost summary
        print("\n4. Generating cost summary...")
        summary = cost_tracker.get_cost_summary()
        
        print(f"   ✓ Today's total: ${summary['today']['total']:.4f}")
        print(f"   ✓ Today by provider:")
        for provider, cost in summary['today']['by_provider'].items():
            print(f"     - {provider.title()}: ${cost:.4f}")
        
        print(f"   ✓ All-time total: ${summary['all_time']['total']:.4f}")
        
        # 5. Test budget checking
        print("\n5. Testing budget validation...")
        within_budget = cost_tracker.is_over_budget(daily_budget=1.0, monthly_budget=10.0)
        print(f"   ✓ Over daily budget ($1.00): {within_budget['daily']}")
        print(f"   ✓ Over monthly budget ($10.00): {within_budget['monthly']}")
        
        print("   ✅ Cost Tracking Demo: SUCCESS")
        
    finally:
        # Cleanup
        shutil.rmtree(temp_dir)

def demo_integration():
    """Demonstrate integration between components"""
    print("\n" + "="*60)
    print("🔗 INTEGRATION DEMO")
    print("="*60)
    
    # Create temporary files
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Initialize both components
        settings_manager = SettingsManager(os.path.join(temp_dir, 'settings.json'))
        cost_tracker = CostTracker(os.path.join(temp_dir, 'costs.json'))
        
        # 1. Configure settings for cost tracking
        print("1. Configuring cost-aware settings...")
        settings = {
            'cost_management': {
                'track_costs': True,
                'daily_budget': 5.0,
                'monthly_budget': 50.0,
                'show_cost_estimates': True
            },
            'provider_settings': {
                'openai': {'enabled': True, 'priority': 1},
                'anthropic': {'enabled': True, 'priority': 2},
                'google': {'enabled': False, 'priority': 3}  # Disabled to save costs
            }
        }
        
        settings_manager.save_settings(settings)
        loaded_settings = settings_manager.load_settings()
        
        # 2. Simulate API usage with cost tracking
        print("2. Simulating API usage...")
        enabled_providers = settings_manager.get_enabled_providers(loaded_settings)
        print(f"   ✓ Enabled providers: {enabled_providers}")
        
        # Simulate requests
        message = "What is the meaning of life, the universe, and everything?"
        estimated_tokens = cost_tracker.estimate_message_tokens(message)
        
        total_estimated_cost = 0
        for provider in enabled_providers:
            model = loaded_settings['models'][provider]
            estimated_cost = cost_tracker.estimate_cost(provider, model, estimated_tokens, 100)
            total_estimated_cost += estimated_cost
            
            print(f"   ✓ {provider.title()} ({model}): ${estimated_cost:.4f}")
            
            # Record the cost
            cost_tracker.record_cost(provider, model, estimated_cost)
        
        print(f"   ✓ Total estimated cost: ${total_estimated_cost:.4f}")
        
        # 3. Check budget compliance
        print("\n3. Checking budget compliance...")
        daily_budget = loaded_settings['cost_management']['daily_budget']
        budget_status = cost_tracker.is_over_budget(daily_budget, 50.0)
        
        within_budget = settings_manager.is_within_budget(loaded_settings, total_estimated_cost)
        
        print(f"   ✓ Daily budget: ${daily_budget}")
        print(f"   ✓ Current spending within budget: {not budget_status['daily']}")
        print(f"   ✓ Request within limits: {within_budget}")
        
        # 4. Generate usage report
        print("\n4. Generating usage report...")
        cost_summary = cost_tracker.get_cost_summary()
        ui_settings = loaded_settings.get('ui_settings', {})
        
        print(f"   ✓ Theme: {ui_settings.get('theme', 'light')}")
        print(f"   ✓ Show cost estimates: {loaded_settings['cost_management']['show_cost_estimates']}")
        print(f"   ✓ Daily spending: ${cost_summary['today']['total']:.4f}")
        
        print("   ✅ Integration Demo: SUCCESS")
        
    finally:
        # Cleanup
        shutil.rmtree(temp_dir)

def demo_file_operations():
    """Demonstrate file handling and persistence"""
    print("\n" + "="*60)
    print("📁 FILE OPERATIONS DEMO")
    print("="*60)
    
    temp_dir = tempfile.mkdtemp()
    
    try:
        # 1. Test settings persistence across sessions
        print("1. Testing settings persistence...")
        settings_file = os.path.join(temp_dir, 'persistent_settings.json')
        
        # Session 1: Create and save settings
        manager1 = SettingsManager(settings_file)
        custom_settings = {'models': {'openai': 'gpt-3.5-turbo'}}
        manager1.save_settings(custom_settings)
        print("   ✓ Settings saved in session 1")
        
        # Session 2: Load settings in new instance
        manager2 = SettingsManager(settings_file)
        loaded_settings = manager2.load_settings()
        print(f"   ✓ Settings loaded in session 2: {loaded_settings['models']['openai']}")
        
        # 2. Test cost tracking persistence
        print("\n2. Testing cost tracking persistence...")
        cost_file = os.path.join(temp_dir, 'persistent_costs.json')
        
        # Session 1: Record costs
        tracker1 = CostTracker(cost_file)
        tracker1.record_cost('openai', 'gpt-4', 0.25)
        print("   ✓ Costs recorded in session 1")
        
        # Session 2: Load costs
        tracker2 = CostTracker(cost_file)
        total_spending = tracker2.get_total_spending()
        print(f"   ✓ Total spending loaded in session 2: ${total_spending:.4f}")
        
        # 3. Test error handling
        print("\n3. Testing error handling...")
        
        # Corrupted JSON file
        corrupted_file = os.path.join(temp_dir, 'corrupted.json')
        with open(corrupted_file, 'w') as f:
            f.write('{"invalid": json syntax')
        
        manager3 = SettingsManager(corrupted_file)
        fallback_settings = manager3.load_settings()
        print("   ✓ Gracefully handled corrupted settings file")
        
        tracker3 = CostTracker(corrupted_file)
        fallback_total = tracker3.get_total_spending()
        print("   ✓ Gracefully handled corrupted cost file")
        
        print("   ✅ File Operations Demo: SUCCESS")
        
    finally:
        # Cleanup
        shutil.rmtree(temp_dir)

def main():
    """Run all demonstrations"""
    print("🚀 FelixGPT Component Demonstration")
    print("This demo shows all core components working without requiring API keys.")
    
    try:
        demo_settings_management()
        demo_cost_tracking()
        demo_integration()
        demo_file_operations()
        
        print("\n" + "="*60)
        print("🎉 ALL DEMONSTRATIONS COMPLETED SUCCESSFULLY!")
        print("="*60)
        print("\nThe FelixGPT system is working correctly!")
        print("Key features demonstrated:")
        print("  ✅ Settings management with persistence")
        print("  ✅ Cost tracking and budget management")
        print("  ✅ Component integration")
        print("  ✅ Error handling and file operations")
        print("  ✅ Provider prioritization and configuration")
        print("\nTo run the full web application:")
        print("  1. Set your API keys: OPENAI_API_KEY, ANTHROPIC_API_KEY, GOOGLE_API_KEY")
        print("  2. Run: python app.py")
        print("  3. Open: http://localhost:5000")
        
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()