@echo off
echo ========================================
echo    SmartResume AI - Complete Startup
echo ========================================
echo.

echo Starting Backend Server (Port 8000)...
start "SmartResume Backend" cmd /k "cd /d C:\Users\User\Desktop\SmartResume && C:\Users\User\Desktop\SmartResume\smartresume_env\Scripts\python.exe -m uvicorn backend.app:app --host 0.0.0.0 --port 8000 --reload"

echo Waiting 5 seconds for backend to start...
timeout /t 5 /nobreak >nul

echo Starting Frontend Application (Port 8502)...
start "SmartResume Frontend" cmd /k "cd /d C:\Users\User\Desktop\SmartResume && C:\Users\User\Desktop\SmartResume\smartresume_env\Scripts\python.exe -m streamlit run frontend/streamlit_app.py --server.port 8502"

echo.
echo ========================================
echo Both servers are starting up!
echo.
echo Backend API: http://localhost:8000
echo Frontend App: http://localhost:8502
echo.
echo Note: Port 8502 is used to avoid conflict with other apps
echo ========================================
pause