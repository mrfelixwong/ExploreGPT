#!/usr/bin/env python3
"""
FelixGPT Mock Web Demo
Shows the Flask interface working with mock responses (no API keys needed)
"""

from flask import Flask, render_template, request, redirect, url_for, session
from models.settings import settings_manager
from models.cost_tracker import cost_tracker
import json
import random
import time

app = Flask(__name__)
app.secret_key = 'demo-secret-key'

# Mock responses for demonstration
MOCK_RESPONSES = {
    'openai': [
        "Hello! I'm GPT-4. I can help you with a wide variety of tasks including writing, analysis, coding, math, and creative projects.",
        "As an AI assistant created by OpenAI, I'm designed to be helpful, harmless, and honest. What can I help you with today?",
        "I'm here to assist you with questions, creative writing, problem-solving, and more. How may I help you?"
    ],
    'anthropic': [
        "Hi there! I'm Claude, an AI assistant created by Anthropic. I'm happy to help with analysis, writing, math, coding, and conversation.",
        "Hello! I'm Claude. I aim to be helpful, harmless, and honest. I can assist with a wide range of tasks - what would you like to work on?",
        "I'm Claude, an AI assistant. I can help with research, writing, problem-solving, creative projects, and thoughtful conversation."
    ],
    'google': [
        "Hello! I'm Gemini, Google's AI model. I can help with information, creative tasks, coding, analysis, and more.",
        "Hi! I'm Gemini Pro. I can assist you with questions, creative writing, analysis, and problem-solving. What can I help you with?",
        "I'm Gemini, and I'm here to help! I can handle text generation, analysis, coding assistance, and creative tasks."
    ]
}

def get_mock_response(provider, message):
    """Generate a mock response for demonstration"""
    # Simulate API call delay
    delay = random.uniform(0.1, 0.3)
    time.sleep(delay)
    
    # Select random response
    response_text = random.choice(MOCK_RESPONSES[provider])
    
    # Add context-aware elements
    if "hello" in message.lower() or "hi" in message.lower():
        response_text = f"Hello! {response_text}"
    elif "?" in message:
        response_text = f"Great question! {response_text}"
    
    # Create realistic response structure
    latency_ms = int(delay * 1000 + random.randint(50, 200))
    tokens = {
        'input': len(message) // 4,
        'output': len(response_text) // 4,
        'total': (len(message) + len(response_text)) // 4
    }
    
    return {
        'response': response_text,
        'success': True,
        'latency': latency_ms,
        'model': {
            'openai': 'gpt-4',
            'anthropic': 'claude-3-sonnet-20240229',
            'google': 'gemini-pro'
        }[provider],
        'tokens': tokens,
        'estimated_cost': cost_tracker.estimate_cost(
            provider, 
            {'openai': 'gpt-4', 'anthropic': 'claude-3-sonnet-20240229', 'google': 'gemini-pro'}[provider],
            tokens['input'],
            tokens['output']
        )
    }

# Load settings
current_settings = settings_manager.load_settings()

@app.route('/')
def index():
    return render_template('index.html', settings=current_settings)

@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.form.get('message', '').strip()
    if not user_message:
        return redirect(url_for('index'))
    
    # Get enabled providers
    enabled_providers = []
    for provider in ['openai', 'anthropic', 'google']:
        if current_settings['provider_settings'][provider]['enabled']:
            enabled_providers.append(provider)
    
    # Generate mock responses
    responses = {}
    for provider in enabled_providers:
        try:
            response = get_mock_response(provider, user_message)
            responses[provider] = response
            
            # Record cost if tracking enabled
            if current_settings['cost_management']['track_costs']:
                cost_tracker.record_cost(provider, response['model'], response['estimated_cost'])
                
        except Exception as e:
            responses[provider] = {
                'response': f'Mock error: {str(e)}',
                'success': False,
                'latency': 0
            }
    
    return render_template('chat_response.html', 
                         user_message=user_message, 
                         responses=responses,
                         settings=current_settings)

@app.route('/settings')
def settings_page():
    cost_summary = cost_tracker.get_cost_summary()
    return render_template('settings.html', 
                         settings=current_settings,
                         cost_summary=cost_summary)

@app.route('/settings', methods=['POST'])
def update_settings():
    global current_settings
    
    # Simplified settings update for demo
    new_settings = current_settings.copy()
    
    # Update provider settings
    for provider in ['openai', 'anthropic', 'google']:
        enabled_key = f'{provider}_enabled'
        if enabled_key in request.form:
            new_settings['provider_settings'][provider]['enabled'] = True
        else:
            new_settings['provider_settings'][provider]['enabled'] = False
    
    # Update cost tracking
    new_settings['cost_management']['track_costs'] = 'track_costs' in request.form
    
    # Save settings
    if settings_manager.save_settings(new_settings):
        current_settings = settings_manager.load_settings()
        session['message'] = 'Settings updated successfully! (Demo mode)'
    else:
        session['message'] = 'Failed to update settings.'
    
    return redirect(url_for('settings_page'))

@app.route('/memory')
def memory_page():
    # Mock memory data for demo
    mock_conversations = [
        ('2024-01-20 10:30:00', 'Hello, can you help me with Python?', 
         json.dumps({'openai': {'response': 'Sure! I can help with Python programming.'}})),
        ('2024-01-20 10:25:00', 'What is machine learning?', 
         json.dumps({'anthropic': {'response': 'Machine learning is a subset of AI...'}})),
    ]
    
    mock_facts = [
        ('preferences', 'I like Python programming', '2024-01-20 10:30:00', 0.9),
        ('work_info', 'I work as a software developer', '2024-01-20 10:28:00', 0.8),
    ]
    
    return render_template('memory.html', 
                         conversations=mock_conversations,
                         facts=mock_facts)

if __name__ == '__main__':
    print("🚀 Starting FelixGPT Mock Demo Server...")
    print("   Demo Features:")
    print("   ✅ Mock LLM responses (no API keys needed)")
    print("   ✅ Settings management")
    print("   ✅ Cost tracking simulation")
    print("   ✅ Full web interface")
    print("   ✅ Memory system preview")
    print(f"\n   🌐 Open your browser to: http://localhost:5001")
    print("   📝 Try different messages to see varied responses")
    print("   ⚙️  Modify settings to see real-time changes")
    
    app.run(debug=True, port=5001)