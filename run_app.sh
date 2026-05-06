#!/bin/bash
# run_app.sh - Start the Streamlit Medical Appointment Scheduler

echo "=========================================="
echo "Medical Appointment Scheduler - Streamlit"
echo "=========================================="
echo ""
echo "Starting application..."
echo ""

# Check if streamlit is installed
if ! command -v streamlit &> /dev/null
then
    echo "ERROR: Streamlit is not installed"
    echo "Please install it with: pip install streamlit"
    exit 1
fi

# Run the Streamlit app
echo "Opening app at http://localhost:8501"
echo "Press Ctrl+C to stop the server"
echo ""

streamlit run app/main.py

# Cleanup message
echo ""
echo "Application stopped."
