from flask import Flask, render_template, request, redirect, url_for, jsonify, session, Response
from models.settings import settings_manager
from models.llm_clients import LLMOrchestrator
from models.cost_tracker import cost_tracker
from models.debug_logger import debug_log, debug_error, is_debug_enabled
import sqlite3
import json
from datetime import datetime
import os
import uuid
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
    
    # Create conversations table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            user_message TEXT NOT NULL,
            responses TEXT NOT NULL,
            context TEXT,
            session_id TEXT
        )
    ''')
    
    # Check if session_id column exists, add it if not
    cursor.execute("PRAGMA table_info(conversations)")
    columns = [column[1] for column in cursor.fetchall()]
    if 'session_id' not in columns:
        cursor.execute('ALTER TABLE conversations ADD COLUMN session_id TEXT')
    
    # Create settings table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    ''')
    
    # Create cost_tracking table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cost_tracking (
            date TEXT PRIMARY KEY,
            total_cost REAL NOT NULL
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
    # Create or get session ID for conversation tracking
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
    
    # Log page access for debugging
    debug_log("page_load", {
        "page": "index",
        "session_id": session['session_id']
    })
    
    # Load conversation history for this session
    conversation = get_session_conversation(session['session_id'])
    
    ui_classes = settings_manager.get_ui_classes(current_settings)
    return render_template('index.html', 
                         settings=current_settings, 
                         ui_classes=ui_classes,
                         conversation=conversation)

@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.form.get('message', '').strip()
    if not user_message:
        return redirect(url_for('index'))
    
    # Ensure session exists
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
    
    # Get relevant context from memory
    context = get_relevant_context(user_message)
    
    # Send to selected LLM
    response = orchestrator.chat_single(user_message, context)
    
    # Store conversation with session ID
    store_conversation(user_message, response, context, session['session_id'])
    
    # Redirect back to index with updated conversation
    return redirect(url_for('index'))

@app.route('/new-chat')
def new_chat():
    """Start a new chat session"""
    session['session_id'] = str(uuid.uuid4())
    return redirect(url_for('index'))

@app.route('/stream-chat', methods=['POST'])
def stream_chat():
    """Stream chat response using Server-Sent Events"""
    user_message = request.json.get('message', '').strip()
    if not user_message:
        return Response("data: " + json.dumps({'type': 'error', 'message': 'No message provided'}) + "\n\n", mimetype='text/plain')
    
    # Ensure session exists
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
    
    # Capture session_id before generator starts
    session_id = session['session_id']
    
    def generate():
        try:
            # Log streaming chat initiation
            debug_log("streaming_chat", {
                "session_id": session_id,
                "message_length": len(user_message)
            })
            
            # Send typing indicator
            yield "data: " + json.dumps({'type': 'typing', 'message': 'AI is thinking...'}) + "\n\n"
            
            # Get relevant context from memory
            context = get_relevant_context(user_message)
            
            # Stream response from LLM
            full_response_text = ""
            response_metadata = {}
            
            for chunk in orchestrator.chat_single_stream(user_message, context):
                yield "data: " + json.dumps(chunk) + "\n\n"
                
                # Collect full response for storage
                if chunk['type'] == 'content':
                    full_response_text += chunk['text']
                elif chunk['type'] == 'end':
                    response_metadata = chunk
                    
            # Store complete response
            complete_response = {
                'response': full_response_text,
                'success': True,
                'provider': response_metadata.get('provider', 'unknown'),
                'model': response_metadata.get('model', ''),
                'latency': response_metadata.get('latency', 0)
            }
            
            store_conversation(user_message, complete_response, context, session_id)
            
            # Log successful streaming completion
            debug_log("streaming_complete", {
                "session_id": session_id,
                "response_length": len(full_response_text),
                "provider": response_metadata.get('provider'),
                "latency": response_metadata.get('latency', 0)
            })
            
            # Send final complete signal
            yield "data: " + json.dumps({'type': 'complete'}) + "\n\n"
            
        except Exception as e:
            error_msg = str(e)
            # Log streaming error
            debug_error("streaming_error", error_msg, {
                "session_id": session_id,
                "message_length": len(user_message)
            })
            yield "data: " + json.dumps({'type': 'error', 'message': error_msg}) + "\n\n"
    
    return Response(generate(), mimetype='text/plain')

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
        'google': request.form.get('google_model', 'gemini-pro')
    }
    
    # Provider settings removed - now automatic (OpenAI primary, Google fallback)
    
    # Response settings
    new_settings['response_settings'] = {
        'max_tokens': int(request.form.get('max_tokens', 1000)),
        'timeout': int(request.form.get('timeout', 30)),
        'temperature': float(request.form.get('temperature', 0.7)),
        'show_metadata': 'show_metadata' in request.form
    }
    
    # Simplified cost management
    new_settings['cost_management'] = {
        'track_costs': 'track_costs' in request.form
    }
    
    # UI settings
    new_settings['ui_settings'] = {
        'theme': request.form.get('theme', 'light'),
        'selected_provider': request.form.get('selected_provider', 'openai'),
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
    
    conn.close()
    
    ui_classes = settings_manager.get_ui_classes(current_settings)
    return render_template('memory.html', 
                         conversations=conversations,
                         settings=current_settings,
                         ui_classes=ui_classes)

def get_relevant_context(message, limit=3):
    """Get simple conversation context from recent chat history"""
    session_id = session.get('session_id')
    if not session_id:
        return []
    
    # Get last few conversation turns as context
    recent_conversation = get_session_conversation(session_id, limit)
    context = []
    
    for turn in recent_conversation:
        # Add both user message and AI response as context
        context.append(f"User: {turn['user_message']}")
        if turn['response']['response']:
            # Truncate long responses to keep context manageable
            response_text = turn['response']['response'][:200]
            if len(turn['response']['response']) > 200:
                response_text += "..."
            context.append(f"AI: {response_text}")
    
    return context[-6:]  # Last 3 exchanges (up to 6 messages total)

def store_conversation(user_message, response, context, session_id):
    """Store conversation in memory with session tracking"""
    conn = sqlite3.connect('memory.db')
    cursor = conn.cursor()
    
    timestamp = datetime.now().isoformat()
    response_json = json.dumps(response)
    context_json = json.dumps(context) if context else None
    
    cursor.execute('''
        INSERT INTO conversations (timestamp, user_message, responses, context, session_id)
        VALUES (?, ?, ?, ?, ?)
    ''', (timestamp, user_message, response_json, context_json, session_id))
    
    conn.commit()
    conn.close()

def get_session_conversation(session_id, limit=10):
    """Get recent conversation for a session"""
    conn = sqlite3.connect('memory.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT timestamp, user_message, responses 
        FROM conversations 
        WHERE session_id = ?
        ORDER BY timestamp DESC 
        LIMIT ?
    ''', (session_id, limit))
    
    raw_conversation = cursor.fetchall()
    conn.close()
    
    # Format for template: reverse order (oldest first) and parse JSON
    conversation = []
    for timestamp, user_msg, response_json in reversed(raw_conversation):
        try:
            response = json.loads(response_json)
            conversation.append({
                'timestamp': timestamp,
                'user_message': user_msg,
                'response': response
            })
        except json.JSONDecodeError:
            # Handle legacy format if needed
            pass
    
    return conversation

# Removed complex fact extraction - now using simple conversation context instead


if __name__ == '__main__':
    print("🚀 Starting FelixGPT...")
    if is_debug_enabled():
        print("🐛 Claude Debug Mode: ENABLED")
        print("   - Logs to /tmp/exploregpt_logs/exploregpt_debug.log")
    print("✅ OpenAI API: Ready")
    print("✅ Google API: Ready")
    print()
    print("🌐 Open your browser to: http://localhost:5001")
    print("🛑 Press Ctrl+C to stop the server")
    print()
    app.run(debug=True, port=5001, host='127.0.0.1')