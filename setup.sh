#!/bin/bash

# SmartResume AI Setup Script
# This script automates the initial setup process

echo "🚀 Setting up SmartResume AI..."

# Check if Python is installed
if ! command -v python &> /dev/null; then
    echo "❌ Python is not installed. Please install Python 3.8+ first."
    exit 1
fi

# Check Python version
python_version=$(python -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo "✅ Python $python_version detected"

# Create virtual environment if it doesn't exist
if [ ! -d "smartresume_env" ]; then
    echo "📦 Creating virtual environment..."
    python -m venv smartresume_env
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source smartresume_env/bin/activate  # For Unix/macOS
# For Windows: smartresume_env\Scripts\activate

# Install requirements
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Download spaCy model
echo "🧠 Downloading NLP model..."
python -m spacy download en_core_web_sm

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "⚙️ Creating environment configuration..."
    cp .env.example .env
    echo "Please edit .env file and add your OpenAI API key"
fi

# Create necessary directories
mkdir -p uploads outputs

echo "✅ Setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Edit .env file and add your OpenAI API key"
echo "2. Run: python backend/app.py (to start API)"
echo "3. Run: streamlit run frontend/streamlit_app.py (to start web interface)"
echo ""
echo "🔗 Get OpenAI API key: https://platform.openai.com/api-keys"