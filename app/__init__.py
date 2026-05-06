"""
Streamlit App Module
Medical Appointment Scheduler Chat Interface

This package provides a Streamlit-based chat interface for the AI medical scheduling agent.

Modules:
- main.py: Main Streamlit application entry point
- session_manager.py: Conversation and state management
- ui_components.py: UI rendering helpers
"""

from app.session_manager import SessionManager
from app.ui_components import (
    render_chat_message,
    render_chat_history,
    render_state_info,
    render_workflow_status,
)

__all__ = [
    'SessionManager',
    'render_chat_message',
    'render_chat_history',
    'render_state_info',
    'render_workflow_status',
]
