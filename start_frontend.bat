@echo off
echo Starting SmartResume AI Frontend...
cd /d "C:\Users\User\Desktop\SmartResume"
"C:\Users\User\Desktop\SmartResume\smartresume_env\Scripts\python.exe" -m streamlit run frontend/streamlit_app.py --server.port 8502
pause