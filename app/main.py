"""
Main Streamlit Application
Entry point for the Medical Appointment Scheduler chat interface

This module:
1. Initializes the Streamlit page
2. Manages session state
3. Displays chat interface
4. Integrates with the LangGraph agent
5. Handles conversation flow
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.ui_components import (
    render_page_header,
    render_top_bar,
    render_chat_history,
    render_chat_message,
    render_state_info,
    render_workflow_status,
    render_input_form,
    render_sidebar_info,
    format_agent_output
)
import streamlit as st
from app.session_manager import SessionManager


def initialize_session_state() -> SessionManager:
    """
    Initialize or retrieve the session manager from Streamlit session state
    
    SessionManager handles:
    - Conversation history
    - Agent state
    - Input/output management
    - Workflow execution
    
    Returns:
        SessionManager instance
    """
    if 'session_manager' not in st.session_state:
        st.session_state.session_manager = SessionManager()
    
    return st.session_state.session_manager


def display_chat_interface(manager: SessionManager) -> None:
    """
    Display the chat message history from current conversation
    
    Shows all messages in chronological order with proper formatting
    Automatically shows assistant greeting on first load
    
    Args:
        manager: SessionManager with conversation history
    """
    # Show initial greeting if this is the first time
    manager.show_greeting_if_needed()
    
    # Get conversation history
    messages = manager.get_conversation_history()
    
    # Display all messages in the conversation (including the initial greeting)
    if messages:
        render_chat_history(messages)


def handle_user_input(manager: SessionManager) -> bool:
    user_input = render_input_form()
    if user_input is None:
        return False

    # Show user message in chat immediately
    manager.add_message("user", user_input)

    # Run agent with this input — pass user_input directly
    response, workflow_complete = manager.run_agent_step(user_input)

    # Show agent response
    if response:
        manager.add_message("assistant", response)

    return True


def display_status_panel(manager: SessionManager) -> None:
    state_dict = manager.get_state_summary()
    render_state_info(state_dict)

    if manager.workflow_complete:
        # ✅ get_state_summary() already returns a dict — use .get()
        success = state_dict.get("booking_success", False)
        error = state_dict.get("error_message", "")
        render_workflow_status(
            complete=True,
            success=success,
            error=error
        )


def handle_reset_conversation(manager: SessionManager) -> None:
    """
    Reset the conversation and start a new one
    
    Clears all conversation history and workflow state
    Resets greeting flag so the initial greeting will show again
    
    Args:
        manager: SessionManager to reset
    """
    manager.reset_conversation()
    st.rerun()


def main():
    render_page_header()
    manager = initialize_session_state()

    # ✅ FIX 1: render_sidebar_info BEFORE columns — it uses st.sidebar internally
    # If called inside a column block, Streamlit renders it twice
    render_sidebar_info(manager.get_state_summary())

    # ✅ FIX 2: top bar with patient name
    state_dict = manager.get_state_summary()
    render_top_bar(patient_name=state_dict.get('patient_name', ''))

    chat_col, status_col = st.columns([3, 1])

    with chat_col:
        with st.container():
            display_chat_interface(manager)
        st.divider()
        if not manager.workflow_complete:
            st.subheader("💬 Your Response")
            if handle_user_input(manager):
                st.rerun()
        else:
            st.success("✅ Workflow Complete!")
            st.info("Start a new conversation with the button below")

    with status_col:
        display_status_panel(manager)
        st.divider()
        st.subheader("⚙️ Controls")
        if st.button("🔄 New Conversation", use_container_width=True):
            handle_reset_conversation(manager)
        # ❌ DELETE any render_sidebar_info() call that was inside this block


if __name__ == "__main__":
    main()
