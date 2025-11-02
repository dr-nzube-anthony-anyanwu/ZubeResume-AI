@echo off
REM SmartResume AI Setup Script for Windows
REM This script automates the initial setup process

echo 🚀 Setting up SmartResume AI...

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed. Please install Python 3.8+ first.
    pause
    exit /b 1
)

echo ✅ Python detected

REM Create virtual environment if it doesn't exist
if not exist "smartresume_env" (
    echo 📦 Creating virtual environment...
    python -m venv smartresume_env
)

REM Activate virtual environment
echo 🔄 Activating virtual environment...
call smartresume_env\Scripts\activate

REM Install requirements
echo 📥 Installing dependencies...
pip install -r requirements.txt

REM Download spaCy model
echo 🧠 Downloading NLP model...
python -m spacy download en_core_web_sm

REM Create .env file if it doesn't exist
if not exist ".env" (
    echo ⚙️ Creating environment configuration...
    copy .env.example .env
    echo Please edit .env file and add your OpenAI API key
)

REM Create necessary directories
mkdir uploads 2>nul
mkdir outputs 2>nul

echo ✅ Setup complete!
echo.
echo 📋 Next steps:
echo 1. Edit .env file and add your OpenAI API key
echo 2. Run: python backend/app.py (to start API)
echo 3. Run: streamlit run frontend/streamlit_app.py (to start web interface)
echo.
echo 🔗 Get OpenAI API key: https://platform.openai.com/api-keys

pause