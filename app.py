from flask import Flask, render_template, request, redirect, url_for, jsonify, session
from models.settings import settings_manager
from models.llm_clients import LLMOrchestrator
from models.cost_tracker import cost_tracker
import sqlite3
import json
from datetime import datetime
import os
# Environment variables are loaded from ~/.zshrc

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')

# Add custom template filter for JSON parsing
@app.template_filter('from_json')
def from_json_filter(value):
    """Parse JSON string in templates"""
    try:
        return json.loads(value) if value else {}
    except (json.JSONDecodeError, TypeError):
        return {}

# Initialize memory database
def init_db():
    conn = sqlite3.connect('memory.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            user_message TEXT NOT NULL,
            responses TEXT NOT NULL,
            context TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_facts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fact_type TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            relevance_score REAL DEFAULT 1.0
        )
    ''')
    conn.commit()
    conn.close()

# Initialize database on startup
init_db()

# Load settings
current_settings = settings_manager.load_settings()
orchestrator = LLMOrchestrator(current_settings)

@app.route('/')
def index():
    ui_classes = settings_manager.get_ui_classes(current_settings)
    return render_template('index.html', settings=current_settings, ui_classes=ui_classes)

@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.form.get('message', '').strip()
    if not user_message:
        return redirect(url_for('index'))
    
    # Get relevant context from memory
    context = get_relevant_context(user_message)
    
    # Send to LLMs
    responses = orchestrator.chat_with_all(user_message, context)
    
    # Store conversation
    store_conversation(user_message, responses, context)
    
    # Extract and store user facts
    extract_user_facts(user_message, responses)
    
    ui_classes = settings_manager.get_ui_classes(current_settings)
    return render_template('chat_response.html', 
                         user_message=user_message, 
                         responses=responses,
                         settings=current_settings,
                         ui_classes=ui_classes)

@app.route('/settings')
def settings_page():
    cost_summary = cost_tracker.get_cost_summary()
    ui_classes = settings_manager.get_ui_classes(current_settings)
    return render_template('settings.html', 
                         settings=current_settings,
                         cost_summary=cost_summary,
                         ui_classes=ui_classes)

@app.route('/settings', methods=['POST'])
def update_settings():
    global current_settings, orchestrator
    
    # Get form data and convert to settings structure
    new_settings = {}
    
    # Model settings
    new_settings['models'] = {
        'openai': request.form.get('openai_model', 'gpt-4'),
        'anthropic': request.form.get('anthropic_model', 'claude-3-sonnet-20240229'),
        'google': request.form.get('google_model', 'gemini-pro')
    }
    
    # Provider settings
    new_settings['provider_settings'] = {
        'openai': {
            'enabled': 'openai_enabled' in request.form,
            'priority': int(request.form.get('openai_priority', 1)),
            'fallback': 'openai_fallback' in request.form
        },
        'anthropic': {
            'enabled': 'anthropic_enabled' in request.form,
            'priority': int(request.form.get('anthropic_priority', 2)),
            'fallback': 'anthropic_fallback' in request.form
        },
        'google': {
            'enabled': 'google_enabled' in request.form,
            'priority': int(request.form.get('google_priority', 3)),
            'fallback': 'google_fallback' in request.form
        }
    }
    
    # Response settings
    new_settings['response_settings'] = {
        'max_tokens': int(request.form.get('max_tokens', 1000)),
        'timeout': int(request.form.get('timeout', 30)),
        'temperature': float(request.form.get('temperature', 0.7)),
        'parallel_requests': 'parallel_requests' in request.form,
        'show_metadata': 'show_metadata' in request.form
    }
    
    # Memory settings
    new_settings['memory_settings'] = {
        'context_count': int(request.form.get('context_count', 5)),
        'auto_learning': 'auto_learning' in request.form,
        'retention_days': int(request.form.get('retention_days', 30)),
        'memory_types': {
            'personal_facts': 'memory_personal_facts' in request.form,
            'preferences': 'memory_preferences' in request.form,
            'context': 'memory_context' in request.form,
            'work_info': 'memory_work_info' in request.form
        }
    }
    
    # Cost management
    new_settings['cost_management'] = {
        'track_costs': 'track_costs' in request.form,
        'daily_budget': float(request.form.get('daily_budget', 5.0)),
        'monthly_budget': float(request.form.get('monthly_budget', 50.0)),
        'show_cost_estimates': 'show_cost_estimates' in request.form,
        'smart_routing': 'smart_routing' in request.form
    }
    
    # UI settings
    new_settings['ui_settings'] = {
        'theme': request.form.get('theme', 'light'),
        'layout': request.form.get('layout', 'grid'),
        'font_size': request.form.get('font_size', 'medium'),
        'auto_scroll': 'auto_scroll' in request.form,
        'show_timestamps': 'show_timestamps' in request.form
    }
    
    # Save settings
    if settings_manager.save_settings(new_settings):
        current_settings = settings_manager.load_settings()
        orchestrator.update_settings(current_settings)
        session['message'] = 'Settings saved successfully!'
    else:
        session['message'] = 'Failed to save settings.'
    
    return redirect(url_for('settings_page'))

@app.route('/memory')
def memory_page():
    conn = sqlite3.connect('memory.db')
    cursor = conn.cursor()
    
    # Get recent conversations
    cursor.execute('''
        SELECT timestamp, user_message, responses 
        FROM conversations 
        ORDER BY timestamp DESC 
        LIMIT 20
    ''')
    conversations = cursor.fetchall()
    
    # Get user facts
    cursor.execute('''
        SELECT fact_type, content, timestamp, relevance_score
        FROM user_facts 
        ORDER BY relevance_score DESC, timestamp DESC
        LIMIT 50
    ''')
    facts = cursor.fetchall()
    
    conn.close()
    
    ui_classes = settings_manager.get_ui_classes(current_settings)
    return render_template('memory.html', 
                         conversations=conversations,
                         facts=facts,
                         settings=current_settings,
                         ui_classes=ui_classes)

def get_relevant_context(message, limit=5):
    """Get relevant context from memory for the message"""
    if not current_settings.get('memory_settings', {}).get('auto_learning', False):
        return []
    
    conn = sqlite3.connect('memory.db')
    cursor = conn.cursor()
    
    # Simple keyword-based context retrieval
    words = message.lower().split()
    context = []
    
    # Get relevant user facts
    for word in words[:5]:  # Use first 5 words for context
        cursor.execute('''
            SELECT content FROM user_facts 
            WHERE content LIKE ? 
            ORDER BY relevance_score DESC 
            LIMIT ?
        ''', (f'%{word}%', limit))
        
        facts = cursor.fetchall()
        context.extend([fact[0] for fact in facts])
    
    conn.close()
    return list(set(context))[:limit]  # Remove duplicates and limit

def store_conversation(user_message, responses, context):
    """Store conversation in memory"""
    conn = sqlite3.connect('memory.db')
    cursor = conn.cursor()
    
    timestamp = datetime.now().isoformat()
    responses_json = json.dumps(responses)
    context_json = json.dumps(context) if context else None
    
    cursor.execute('''
        INSERT INTO conversations (timestamp, user_message, responses, context)
        VALUES (?, ?, ?, ?)
    ''', (timestamp, user_message, responses_json, context_json))
    
    conn.commit()
    conn.close()

def extract_user_facts(user_message, responses):
    """Extract and store user facts from the conversation"""
    if not current_settings.get('memory_settings', {}).get('auto_learning', False):
        return
    
    # Simple fact extraction - look for patterns like "I am...", "I like...", "I work..."
    message_lower = user_message.lower()
    facts = []
    
    if "i am " in message_lower:
        facts.append(("personal", user_message))
    elif "i like " in message_lower or "i love " in message_lower:
        facts.append(("preferences", user_message))
    elif "i work " in message_lower or "my job " in message_lower:
        facts.append(("work_info", user_message))
    elif any(word in message_lower for word in ["my name", "called", "prefer"]):
        facts.append(("personal_facts", user_message))
    
    if facts:
        conn = sqlite3.connect('memory.db')
        cursor = conn.cursor()
        timestamp = datetime.now().isoformat()
        
        for fact_type, content in facts:
            cursor.execute('''
                INSERT INTO user_facts (fact_type, content, timestamp)
                VALUES (?, ?, ?)
            ''', (fact_type, content, timestamp))
        
        conn.commit()
        conn.close()

if __name__ == '__main__':
    print("🚀 Starting FelixGPT...")
    print("✅ OpenAI API: Ready")
    print("✅ Google API: Ready") 
    print("⚠️  Anthropic API: Disabled (library issue)")
    print()
    print("🌐 Open your browser to: http://localhost:5001")
    print("🛑 Press Ctrl+C to stop the server")
    print()
    app.run(debug=True, port=5001, host='127.0.0.1')