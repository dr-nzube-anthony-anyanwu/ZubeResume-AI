@echo off
echo Starting SmartResume AI Backend Server...
cd /d "C:\Users\User\Desktop\SmartResume"
"C:\Users\User\Desktop\SmartResume\smartresume_env\Scripts\python.exe" -m uvicorn backend.app:app --host 0.0.0.0 --port 8001
pause