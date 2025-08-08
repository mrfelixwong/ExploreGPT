# FelixGPT - Multi-LLM Chat Application

A simple Flask web application that allows you to chat with multiple LLM providers (OpenAI, Anthropic, Google) simultaneously.

## Features

- **Multi-LLM Chat**: Send messages to OpenAI, Anthropic, and Google simultaneously
- **Custom Memory System**: Learns about you from conversations
- **Cost Tracking**: Monitor API usage and costs
- **Comprehensive Settings**: Configure models, providers, and behavior
- **Server-side Rendering**: Simple HTML interface, no JavaScript required

## Setup

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure API Keys**:
   ```bash
   python config.py
   ```
   This will prompt you to enter your OpenAI API key and save it securely.

3. **Run the Application**:
   ```bash
   python app.py
   ```

4. **Open Browser**: Go to http://localhost:5000

### Alternative Setup Methods

**Quick Setup Script**:
```bash
./setup_keys.sh
```

**Manual .env File Setup**:
Edit the `.env` file and replace `your-openai-api-key-here` with your actual API key from https://platform.openai.com/api-keys

## Usage

1. **Chat**: Send messages on the home page to all enabled LLM providers
2. **Settings**: Configure models, providers, memory, and cost settings
3. **Memory**: View stored conversations and learned user facts

## File Structure

```
felixgpt/
├── app.py                 # Main Flask application
├── models/
│   ├── settings.py        # Settings management
│   ├── cost_tracker.py    # API cost tracking
│   └── llm_clients.py     # LLM orchestration
├── templates/             # HTML templates
└── requirements.txt       # Python dependencies
```

## Configuration

The application creates several files for persistence:
- `user_settings.json`: User preferences and settings
- `cost_tracking.json`: API cost data
- `memory.db`: SQLite database for conversations and user facts