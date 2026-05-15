"""
Main Streamlit Application - Three Panel Layout
Left: Mini sidebar (conversations)
Center: Chat area
Right: Progress + Booking status (always visible)
"""
import sys
import re
from datetime import datetime, date
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from app.session_manager import SessionManager
from app.ui_components import (
    render_page_header, render_chat_history,
    render_input_form, render_sidebar_info,
    render_right_panel, format_agent_output
)


def initialize_session_state() -> SessionManager:
    if 'session_manager' not in st.session_state:
        st.session_state.session_manager = SessionManager()
    return st.session_state.session_manager


def render_chat_section(manager: SessionManager) -> None:
    manager.show_greeting_if_needed()
    messages = manager.get_conversation_history()
    if messages:
        render_chat_history(messages)
    else:
        # Welcome screen when no chat started
        st.markdown("""
        <div style="display:flex;flex-direction:column;align-items:center;
                    justify-content:center;padding:60px 20px;text-align:center;">
            <div style="font-size:48px;margin-bottom:16px;">🏥</div>
            <div style="font-size:24px;font-weight:600;color:#1a1a2e;
                        margin-bottom:8px;font-family:'Geist Sans',sans-serif;">
                Hi, I'm MediBook
            </div>
            <div style="font-size:15px;color:#64748b;margin-bottom:32px;
                        font-family:'Geist Sans',sans-serif;">
                AI-Powered Medical Appointment Scheduling
            </div>
            <div style="font-size:14px;color:#94a3b8;font-family:'Geist Sans',sans-serif;">
                Type your full name below to get started ↓
            </div>
        </div>
        """, unsafe_allow_html=True)


def process_pending_input(manager: SessionManager) -> None:
    messages = manager.get_conversation_history()
    if not messages or messages[-1]['role'] != 'user':
        return
    last_input = messages[-1]['content']
    typing = st.empty()
    typing.markdown("""
    <div style="display:flex;align-items:center;gap:10px;padding:4px 0;">
        <div style="width:34px;height:34px;border-radius:50%;
                    background:linear-gradient(135deg,#7c3aed,#4f1d9e);
                    display:flex;align-items:center;justify-content:center;
                    font-size:15px;flex-shrink:0;">🤖</div>
        <div style="background:#fff;border-radius:4px 14px 14px 14px;
                    padding:12px 18px;border:0.5px solid #ede9fe;">
            <div style="display:flex;gap:6px;align-items:center;">
                <span style="width:9px;height:9px;border-radius:50%;background:#7c3aed;
                             display:inline-block;animation:dotSlide 1.4s infinite ease-in-out;
                             animation-delay:0s;"></span>
                <span style="width:9px;height:9px;border-radius:50%;background:#c4b5fd;
                             display:inline-block;animation:dotSlide 1.4s infinite ease-in-out;
                             animation-delay:0.2s;"></span>
                <span style="width:9px;height:9px;border-radius:50%;background:#7c3aed;
                             display:inline-block;animation:dotSlide 1.4s infinite ease-in-out;
                             animation-delay:0.4s;"></span>
            </div>
        </div>
    </div>
    <style>
    @keyframes dotSlide {
        0%   { opacity:0.2; transform:translateX(0px) scale(0.8); }
        30%  { opacity:1;   transform:translateX(4px) scale(1.2); }
        60%  { opacity:0.5; transform:translateX(0px) scale(0.9); }
        100% { opacity:0.2; transform:translateX(0px) scale(0.8); }
    }
    </style>
    """, unsafe_allow_html=True)
    response, _ = manager.run_agent_step(last_input)
    typing.empty()
    if response:
        manager.add_message("assistant", response)


def render_dob_picker(manager: SessionManager) -> bool:
    messages = manager.get_conversation_history()
    if not messages or messages[-1]['role'] != 'assistant':
        return False
    last_msg = messages[-1]['content'].lower()
    state = manager.agent_state or {}
    if 'date of birth' not in last_msg or state.get('collecting_step') != 'dob':
        return False
    st.markdown("""
    <div style="background:linear-gradient(135deg,#667eea22,#764ba222);
                border:2px dashed #3b9eff;border-radius:16px;
                padding:16px 20px;margin:8px 0 12px 0;text-align:center;">
        <div style="font-size:28px;margin-bottom:6px;">🗓️</div>
        <div style="font-size:14px;font-weight:700;color:#1a5cdf;">Select Your Date of Birth</div>
        <div style="font-size:11px;color:#64748b;margin-top:4px;">↓ Click below to open calendar ↓</div>
    </div>
    """, unsafe_allow_html=True)
    _, col, _ = st.columns([1, 3, 1])
    with col:
        selected = st.date_input(
            "📅 Date of Birth",
            value=date(1990, 1, 1),
            min_value=date(1920, 1, 1),
            max_value=date(2010, 12, 31),
            key="dob_picker",
            format="YYYY/MM/DD"
        )
        if st.button("✅ Confirm Date of Birth", use_container_width=True,
                     key="dob_confirm", type="primary"):
            dob_str = selected.strftime("%Y-%m-%d")
            manager.add_message("user", dob_str)
            with st.spinner("🔍 Looking up your information..."):
                response, _ = manager.run_agent_step(dob_str)
            if response:
                manager.add_message("assistant", response)
            return True
    return False


def render_quick_replies(manager: SessionManager) -> bool:
    messages = manager.get_conversation_history()
    if not messages or messages[-1]['role'] != 'assistant':
        return False
    if manager.workflow_complete:
        return False

    last_msg = messages[-1]['content']
    last_lower = last_msg.lower()
    state = manager.agent_state or {}

    # ── Yes/No buttons ────────────────────────────────────────────────────────
    # Yes/No only for appointment confirmation — NOT for insurance question
    is_confirmation = any(x in last_lower for x in [
        'shall i confirm', 'confirm this appointment', 'yes/no'
    ])
    is_insurance_question = any(x in last_lower for x in [
        'out of pocket', 'do you have insurance', 'health insurance'
    ])

    if is_confirmation and not is_insurance_question and not state.get('insurance_carrier'):
        pass  # don't show yes/no yet
    elif is_confirmation and not is_insurance_question:
        c1, c2 = st.columns(2)
        with c1:
            if st.button("✅ Yes", use_container_width=True, key="qr_yes"):
                return _quick_reply(manager, "yes")
        with c2:
            if st.button("❌ No", use_container_width=True, key="qr_no"):
                return _quick_reply(manager, "no")
        return False

    # ── Doctor selection ──────────────────────────────────────────────────────
    doctor_triggers = [
        'available doctors', 'which doctor', 'doctor would you',
        'dr. john', 'dr. sarah', 'dr. michael', 'following doctors',
        'these doctors', 'our doctors', 'doctors available',
        'doctor available', 'see today', 'like to see'
    ]
    if any(t in last_lower for t in doctor_triggers) and not state.get('preferred_doctor'):
        for i, doc in enumerate(state.get("available_doctors", []), 1):
            label = (f"{i}. {doc['name']} — "
                     f"{doc.get('specialization','')} @ {doc.get('location','')}")
            if st.button(label, use_container_width=True, key=f"qr_doc_{i}"):
                # Send full doctor name not just number
                return _quick_reply(manager, doc['name'])
        return False

    # ── Date selection ────────────────────────────────────────────────────────
    if ('preferred date' in last_lower or 'available dates' in last_lower) \
            and not state.get('appointment_date'):
        import re
        dates = re.findall(r'\d{4}-\d{2}-\d{2}', last_msg)
        if dates:
            for row in range(0, len(dates), 3):
                cols = st.columns(3)
                for i, d in enumerate(dates[row:row+3]):
                    try:
                        from datetime import datetime
                        wd = datetime.strptime(d, "%Y-%m-%d").strftime("%a")
                        label = f"📅 {d} ({wd})"
                    except Exception:
                        label = f"📅 {d}"
                    with cols[i]:
                        if st.button(label, use_container_width=True,
                                     key=f"qr_d_{row+i}"):
                            return _quick_reply(manager, d)
        return False

    # ── Time slot selection — ONLY if no slot selected yet ───────────────────
    if not state.get('selected_time'):
        slots = state.get("available_slots", [])
        slot_triggers = [
            'time slot', 'available slot', 'pick one', 'specific slot',
            'following slot', 'these slot', 'time would', 'prefer',
            'available from', 'following time', 'which time'
        ]
        if slots and any(t in last_lower for t in slot_triggers):
            cols = st.columns(min(len(slots), 4))
            for i, slot in enumerate(slots):
                with cols[i % 4]:
                    if st.button(f"🕐 {slot}", use_container_width=True,
                                 key=f"qr_s_{i}"):
                        return _quick_reply(manager, slot)
            return False

    # ── Insurance carrier selection ───────────────────────────────────────────
    if 'insurance carrier' in last_lower and not state.get('insurance_carrier'):
        carriers = state.get("available_carriers", [])
        if carriers:
            cols = st.columns(2)
            for i, c in enumerate(carriers, 1):
                with cols[(i-1) % 2]:
                    if st.button(f"🏥 {c}", use_container_width=True,
                                 key=f"qr_c_{i}"):
                        return _quick_reply(manager, str(i))
        return False

    return False


def _quick_reply(manager: SessionManager, value: str) -> bool:
    manager.add_message("user", value)
    typing = st.empty()
    typing.markdown("""
    <div style="display:flex;align-items:center;gap:10px;padding:4px 0;">
        <div style="width:34px;height:34px;border-radius:50%;
                    background:linear-gradient(135deg,#7c3aed,#4f1d9e);
                    display:flex;align-items:center;justify-content:center;
                    font-size:15px;">🤖</div>
        <div style="background:#fff;border-radius:4px 14px 14px 14px;padding:12px 18px;
                    border:0.5px solid #ede9fe;">
            <div style="display:flex;gap:6px;">
                <span style="width:9px;height:9px;border-radius:50%;background:#7c3aed;
                             display:inline-block;animation:dotSlide 1.4s infinite;
                             animation-delay:0s;"></span>
                <span style="width:9px;height:9px;border-radius:50%;background:#c4b5fd;
                             display:inline-block;animation:dotSlide 1.4s infinite;
                             animation-delay:0.2s;"></span>
                <span style="width:9px;height:9px;border-radius:50%;background:#7c3aed;
                             display:inline-block;animation:dotSlide 1.4s infinite;
                             animation-delay:0.4s;"></span>
            </div>
        </div>
    </div>
    <style>
    @keyframes dotSlide {
        0%,100%{opacity:0.2;transform:scale(0.8);}
        30%{opacity:1;transform:scale(1.2);}
    }
    </style>
    """, unsafe_allow_html=True)
    response, _ = manager.run_agent_step(value)
    typing.empty()
    if response:
        manager.add_message("assistant", response)
    return True


def render_text_input(manager: SessionManager) -> bool:
    user_input = render_input_form()
    if user_input is None:
        return False
    manager.add_message("user", user_input)
    return True


def main():
    render_page_header()
    manager = initialize_session_state()

    # ── Left sidebar — past appointments + new chat ──
    render_sidebar_info(manager.get_state_summary(), manager)

    # ── Three column layout ──
    # Left gap | Center chat | Right panel
    _, center, right = st.columns([0.05, 0.65, 0.30])

    with right:
        render_right_panel(manager.get_state_summary(), manager)

    with center:
        # Top bar
        state_dict = manager.get_state_summary()
        patient_name = state_dict.get('patient_name', '')
        subtitle = f"Hi {patient_name} 👋" if patient_name else "AI-Powered Appointment Scheduling"
        st.markdown(f"""
        <div style="background:#fff;border-radius:14px;padding:12px 20px;
                    margin-bottom:16px;display:flex;align-items:center;
                    justify-content:space-between;border:0.5px solid #ede9fe;
                    box-shadow:0 1px 4px rgba(124,58,237,0.08);">
            <div>
                <div style="font-size:16px;font-weight:600;color:#1a1a2e;
                            font-family:'Geist Sans',sans-serif;">🏥 MediBook</div>
                <div style="font-size:12px;color:#64748b;
                            font-family:'Geist Sans',sans-serif;">{subtitle}</div>
            </div>
            <span style="font-size:11px;padding:4px 12px;background:#f0fdf4;
                         color:#059669;border-radius:20px;border:1px solid #a7f3d0;">
                ● Online
            </span>
        </div>
        """, unsafe_allow_html=True)

        # Chat messages
        with st.container():
            render_chat_section(manager)
            if (manager.get_conversation_history() and
                    manager.get_conversation_history()[-1]['role'] == 'user' and
                    not manager.workflow_complete):
                process_pending_input(manager)
                st.rerun()

        st.divider()

        if not manager.workflow_complete:
            if render_dob_picker(manager):
                st.rerun()
            if render_quick_replies(manager):
                st.rerun()
            st.subheader("💬 Your Response")
            if render_text_input(manager):
                st.rerun()
        else:
            # Check if cancelled or completed
            state_dict = manager.get_state_summary()
            if state_dict.get('booking_confirmed'):
                st.success("✅ Appointment Booking Complete!")
            else:
                st.warning("❌ Appointment was cancelled. Your info has been saved.")
            
            if st.button("🔄 Book Another Appointment", use_container_width=True):
                manager.reset_conversation()
                st.rerun()


if __name__ == "__main__":
    main()