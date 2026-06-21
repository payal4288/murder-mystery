@echo off
cd /d "%~dp0"

:: Check if port 8501 is already in use
netstat -ano | findstr :8501 >nul
if %errorlevel% equ 0 (
    :: Server is already running, just open browser
    start http://localhost:8501
) else (
    :: Start the Streamlit server in the background
    start "" /b .venv\Scripts\python.exe -m streamlit run app.py
)
