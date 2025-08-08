# 🔐 API Keys Setup

## 🏆 Current Setup: Environment Variables (Most Secure)

**API keys are stored in your `~/.zshrc` file** - this is the most secure approach!

## ✅ Already Configured

Your API keys are set up in environment variables:
- ✅ `OPENAI_API_KEY` - OpenAI API access
- ✅ `ANTHROPIC_API_KEY` - Anthropic Claude API access  
- ✅ `GOOGLE_API_KEY` - Google AI API access
- ✅ `SECRET_KEY` - Flask session security

## 🔒 Maximum Security Features

- 🔒 **Keys never stored in files** - no risk of accidental commits
- 🔒 **Environment-level security** - keys exist only in memory when running
- 🔒 **No dependency on external files** - works across all environments  
- 🔒 **Standard Unix security** - protected by OS user permissions

## 🔄 How It Works

Your `~/.zshrc` contains:
```bash
export OPENAI_API_KEY="sk-proj-..."
export ANTHROPIC_API_KEY="sk-ant-..."  
export GOOGLE_API_KEY="..."
export SECRET_KEY="..."
```

When you start FelixGPT, it automatically reads these environment variables.

## ⚠️ Important Notes

- **Never commit actual API keys to git**
- **Keep `.env` file secure** (don't share/copy to public places)  
- **Regenerate keys** if you suspect they're compromised
- **Use `.env.example`** to share setup instructions with others

## 🧪 Testing Your Setup

```bash
# Verify keys are loaded
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print('✅ Keys loaded!' if os.getenv('OPENAI_API_KEY') else '❌ Keys missing')"

# Test API connections  
python test_working_apis.py
```