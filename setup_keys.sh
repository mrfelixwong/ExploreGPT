#!/bin/bash
# FelixGPT Setup Script
# This script helps you set up API keys and run FelixGPT

echo "🚀 FelixGPT Setup"
echo "================"

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found!"
    echo "Please run this script from the FelixGPT directory."
    exit 1
fi

echo "📋 Current configuration status:"
python config.py

echo ""
echo "🔧 To update your OpenAI API key, run:"
echo "   python config.py"
echo ""
echo "🚀 To start FelixGPT, run:"
echo "   python app.py"
echo ""
echo "📁 Configuration files:"
echo "   📄 .env - Contains your API keys (keep secret!)"
echo "   ⚙️  user_settings.json - Your app preferences"
echo "   💰 cost_tracking.json - Your usage costs"
echo "   🧠 memory.db - Your conversation memory"