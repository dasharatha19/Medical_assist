@echo off
REM run_app.bat - Start the Streamlit Medical Appointment Scheduler (Windows)

echo.
echo ==========================================
echo Medical Appointment Scheduler - Streamlit
echo ==========================================
echo.

REM Check if streamlit is installed
python -c "import streamlit" >nul 2>&1
if errorlevel 1 (
    echo ERROR: Streamlit is not installed
    echo Please install it with: pip install streamlit
    pause
    exit /b 1
)

echo Starting application...
echo.
echo Opening app at http://localhost:8501
echo Press Ctrl+C to stop the server
echo.

python -m streamlit run app/main.py

echo.
echo Application stopped.
pause
