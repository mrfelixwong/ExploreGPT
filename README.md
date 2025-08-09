# ExploreGPT - Simplified AI Chat Application

A streamlined Flask web application for chatting with AI providers (OpenAI and Google Gemini) with built-in web search and conversation memory.

## ✨ Features

- **🤖 Dual Provider Support**: OpenAI GPT models and Google Gemini
- **🔍 Smart Web Search**: Automatic web search integration when needed
- **💬 Streaming Responses**: Real-time chat with server-sent events
- **💾 Conversation Memory**: SQLite-based conversation history
- **💰 Basic Cost Tracking**: Rough API cost estimates
- **🌙 Dark/Light Themes**: Clean, responsive interface
- **🐛 Debug Integration**: Built-in logging for Claude Code debugging

## 🚀 Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set up API keys in ~/.zshrc
export OPENAI_API_KEY="your-key-here"
export GOOGLE_API_KEY="your-key-here"
export BRAVE_API_KEY="your-key-here"  # Optional for web search

# 3. Start the application
python app.py
```

Then open http://localhost:5001 in your browser.

## 🏗️ Architecture

**Simplified single-file design:**

```
exploregpt/
├── app.py              # Main Flask application (368 lines)
├── models/
│   ├── llm_clients.py  # OpenAI + Google integration (289 lines)
│   ├── settings.py     # SQLite-based settings (99 lines)  
│   ├── cost_tracker.py # Basic cost estimation (89 lines)
│   ├── web_search.py   # Brave + DuckDuckGo search (184 lines)
│   └── debug_logger.py # Claude Code debug integration
├── templates/          # Simple HTML templates
└── memory.db          # SQLite database (conversations, settings, costs)
```

**Total: 1,029 lines** (31.5% reduction from previous version)

## 🎯 Supported Features

- ✅ **OpenAI API**: GPT-4, GPT-3.5-turbo with streaming
- ✅ **Google Gemini**: All models with fallback to non-streaming  
- ✅ **Web Search**: Brave API with DuckDuckGo fallback
- ✅ **SQLite Storage**: All data in single database file
- ✅ **Session Management**: UUID-based conversation tracking
- ✅ **Debug Logging**: Structured logs for Claude Code integration

## 🧪 Testing

```bash
# Test core functionality
python -c "from app import init_db; init_db(); print('✅ Database ready')"

# Test API connections
python test_working_apis.py

# Run unit tests
python run_tests.py
```

## 💾 Data Storage

All data is stored in a single SQLite database (`memory.db`):

- **conversations**: Chat history with session tracking
- **settings**: User preferences and configuration  
- **cost_tracking**: Daily API cost estimates

No JSON files - everything consolidated in SQLite for simplicity.

## 🔒 Security

- API keys stored as environment variables (never in code)
- All database operations use parameterized queries
- No sensitive data logged or committed to git

## 🐛 Claude Code Integration

Set `CLAUDE_DEBUG=1` to enable structured logging to `/tmp/exploregpt_logs/exploregpt_debug.log` for optimal Claude Code debugging experience.

## 📝 License

Open source - use and modify as needed!