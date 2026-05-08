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
    render_typing_indicator,
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

    # Add user message
    manager.add_message("user", user_input)
    
    return True  # rerun first to show user message


def process_pending_input(manager: SessionManager) -> None:
    """Process the last user message and show typing indicator in chat."""
    messages = manager.get_conversation_history()
    
    # Check if last message is from user and needs processing
    if not messages or messages[-1]['role'] != 'user':
        return
    
    last_input = messages[-1]['content']
    
    # Show typing indicator in chat area
    typing_placeholder = st.empty()
    typing_placeholder.markdown("""
    <div class="msg-row-bot">
        <div class="avatar-bot">🤖</div>
        <div class="typing-dots">
            <span></span><span></span><span></span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Run agent
    response, workflow_complete = manager.run_agent_step(last_input)
    
    # Clear typing indicator
    typing_placeholder.empty()
    
    if response:
        manager.add_message("assistant", response)


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

def render_quick_replies(manager: SessionManager) -> bool:
    messages = manager.get_conversation_history()
    if not messages or messages[-1]['role'] != 'assistant':
        return False
    if manager.workflow_complete:
        return False

    last_msg = messages[-1]['content']
    last_msg_lower = last_msg.lower()
    state = manager.agent_state or {}

    # ── YES/NO questions ──
    if any(x in last_msg_lower for x in ['yes/no', 'health insurance', 'confirm this appointment']):
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Yes", use_container_width=True, key="qr_yes"):
                return _send_quick_reply(manager, "yes")
        with col2:
            if st.button("❌ No", use_container_width=True, key="qr_no"):
                return _send_quick_reply(manager, "no")

    # ── Cancellation reason ──
    elif 'declining' in last_msg_lower:
        cols = st.columns(3)
        options = ["Personal reasons", "Found another doctor", "Schedule conflict"]
        for i, opt in enumerate(options):
            with cols[i]:
                if st.button(opt, use_container_width=True, key=f"qr_reason_{i}"):
                    return _send_quick_reply(manager, opt)
        # Skip button
        if st.button("⏭️ Skip (no reason)", use_container_width=True, key="qr_skip"):
            return _send_quick_reply(manager, "skip")

    # ── Doctor selection ──
    elif 'available doctors' in last_msg_lower:
        doctors = state.get("available_doctors", [])
        for i, doc in enumerate(doctors, 1):
            label = f"{i}. {doc['name']} - {doc.get('specialization','')} @ {doc.get('location','')}"
            if st.button(label, use_container_width=True, key=f"qr_doc_{i}"):
                return _send_quick_reply(manager, str(i))

    # ── Date selection ──
    elif 'preferred date' in last_msg_lower or 'available dates' in last_msg_lower:
        import re
        dates = re.findall(r'\d{4}-\d{2}-\d{2}', last_msg)
        if dates:
            cols = st.columns(min(len(dates), 4))
            for i, date in enumerate(dates[:4]):
                from datetime import datetime
                try:
                    weekday = datetime.strptime(date, "%Y-%m-%d").strftime("%a")
                    label = f"📅 {date}\n({weekday})"
                except:
                    label = f"📅 {date}"
                with cols[i % 4]:
                    if st.button(label, use_container_width=True, key=f"qr_date_{i}"):
                        return _send_quick_reply(manager, date)

    # ── Time slot selection ──
    elif 'time slot' in last_msg_lower or 'available slots' in last_msg_lower:
        slots = state.get("available_slots", [])
        if slots:
            cols = st.columns(min(len(slots), 4))
            for i, slot in enumerate(slots, 1):
                with cols[(i-1) % 4]:
                    if st.button(f"🕐 {slot}", use_container_width=True, key=f"qr_slot_{i}"):
                        return _send_quick_reply(manager, str(i))

    return False


def _send_quick_reply(manager: SessionManager, value: str) -> bool:
    """Helper to send a quick reply value."""
    manager.add_message("user", value)
    with st.spinner("MediBook is thinking..."):
        response, wf = manager.run_agent_step(value)
    if response:
        manager.add_message("assistant", response)
    return True

def render_dob_picker(manager: SessionManager) -> bool:
    """Show date picker for DOB input."""
    messages = manager.get_conversation_history()
    if not messages or messages[-1]['role'] != 'assistant':
        return False
    
    last_msg = messages[-1]['content'].lower()
    state = manager.agent_state or {}
    
    # Show date picker when asking for DOB
    if 'date of birth' in last_msg and state.get('collecting_step') == 'dob':
        from datetime import date
        selected_date = st.date_input(
            "📅 Select your date of birth:",
            value=date(1990, 1, 1),
            min_value=date(1920, 1, 1),
            max_value=date(2010, 12, 31),
            key="dob_picker"
        )
        if st.button("✅ Confirm Date of Birth", use_container_width=True, key="dob_confirm"):
            dob_str = selected_date.strftime("%Y-%m-%d")
            manager.add_message("user", dob_str)
            with st.spinner("MediBook is thinking..."):
                response, wf = manager.run_agent_step(dob_str)
            if response:
                manager.add_message("assistant", response)
            return True
    
    return False



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

            # DOB calendar picker
            if render_dob_picker(manager):
                st.rerun()
        
            # Quick reply buttons
            if render_quick_replies(manager):
                st.rerun()
                
            # Show typing indicator and process inside chat area
            if manager.get_conversation_history() and \
               manager.get_conversation_history()[-1]['role'] == 'user' and \
               not manager.workflow_complete:
                process_pending_input(manager)
                st.rerun()
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
