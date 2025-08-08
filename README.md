# ExploreGPT - AI Chat Application

A Flask web application that allows you to chat with your choice of AI providers (OpenAI, Google Gemini, Anthropic).

## ✨ Features

- **🤖 Provider Selection**: Choose your preferred AI provider for each conversation
- **🧠 Smart Memory System**: Learns and remembers user preferences
- **💰 Cost Tracking**: Monitor API usage and spending
- **⚙️ Rich Settings**: Configure models, providers, and behavior
- **🌙 Dark Mode**: Beautiful light/dark theme support
- **🔒 Secure**: Environment-based API key management

## 🚀 Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure API keys (see API_KEYS_SETUP.md)

# 3. Start the application
python start.py
```

Then open http://localhost:5001 in your browser.

## 📖 Documentation

- **[API Keys Setup](API_KEYS_SETUP.md)** - How to securely configure your API keys
- **[Testing Guide](TESTING_INSTRUCTIONS.md)** - Complete testing instructions
- **[Known Issues](ANTHROPIC_ISSUE.md)** - Anthropic API library compatibility

## 🎯 Supported Providers

- ✅ **OpenAI** (GPT-4, GPT-3.5)
- ✅ **Google Gemini** (All models)  
- ⚠️ **Anthropic Claude** (Disabled due to library issues)

## 🏗️ Project Structure

```
exploregpt/
├── app.py                 # Main Flask application
├── start.py              # Quick launcher script
├── models/
│   ├── settings.py        # Settings management
│   ├── cost_tracker.py    # Cost tracking
│   └── llm_clients.py     # LLM orchestration
├── templates/             # HTML templates
├── tests/                 # Unit test suite
└── requirements.txt       # Dependencies
```

## 🧪 Testing

```bash
# Quick API test
python test_working_apis.py

# Flask application test  
python test_flask_startup.py

# Full test suite
python run_tests.py
```

## 🛠️ Development

The application creates local data files:
- `user_settings.json`: User preferences
- `cost_tracking.json`: API cost data  
- `memory.db`: Conversation history

These files are gitignored and contain your personal data.

## 🔒 Security

API keys are stored as environment variables in your `~/.zshrc` file - never in the codebase. See `API_KEYS_SETUP.md` for complete security details.

## 📝 License

This project is open source - feel free to use and modify!