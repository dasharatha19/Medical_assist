"""
UI Components Module - Redesigned Health Assistant UI
"""

import streamlit as st
from typing import List, Dict, Optional


# ─── STEP CONFIG ─────────────────────────────────────────────────────────────
STEPS = [
    ("greeting",        "Your Name"),
    ("patient_lookup",  "Patient Check"),
    ("scheduling",      "Pick a Date"),
    ("insurance",       "Insurance"),
    ("confirmation",    "Confirm"),
    ("reminders",       "Done!"),
]

STEP_KEYS = [s[0] for s in STEPS]


# ─── CSS INJECTION ────────────────────────────────────────────────────────────
def inject_css() -> None:
    st.markdown("""
    <style>    
    /* Make << close button visible */
    button[data-testid="baseButton-headerNoPadding"] {
        background: rgba(124,58,237,0.5) !important;
        border-radius: 8px !important;
        border: 1px solid rgba(124,58,237,0.8) !important;
        width: 32px !important;
        height: 32px !important;
    }
    button[data-testid="baseButton-headerNoPadding"] svg {
        fill: white !important;
        color: white !important;
    }
    /* Make >> open button visible */
    [data-testid="collapsedControl"] {
        background: #1a1a2e !important;
    }
    [data-testid="collapsedControl"] button {
        background: rgba(124,58,237,0.5) !important;
        border: 1px solid rgba(124,58,237,0.8) !important;
        border-radius: 0 8px 8px 0 !important;
        color: white !important;
    }
    [data-testid="collapsedControl"] svg {
        fill: white !important;
    }       
    @import url('https://fonts.googleapis.com/css2?family=Geist+Sans:wght@300;400;500;600&display=swap');

    html, body, [class*="css"] {
        font-family: 'Geist Sans', sans-serif !important;
    }

    /* ── Sidebar dark theme ── */
    section[data-testid="stSidebar"] {
        background: #1a1a2e !important;
        border-right: none !important;
    }
    section[data-testid="stSidebar"] > div {
        background: #1a1a2e !important;
        padding-top: 1rem !important;
    }
    section[data-testid="stSidebar"] .stMarkdown p,
    section[data-testid="stSidebar"] .stMarkdown span,
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] .stButton button {
        color: rgba(255,255,255,0.8) !important;
        font-family: 'Inter', sans-serif !important;
    }
    section[data-testid="stSidebar"] hr {
        border-color: rgba(255,255,255,0.1) !important;
    }
section[data-testid="stSidebar"] .stButton button {
        background: rgba(124,58,237,0.15) !important;
        border: 1px solid rgba(124,58,237,0.3) !important;
        border-radius: 8px !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 14px !important;
        font-weight: 500 !important;
        color: white !important;
    }
    section[data-testid="stSidebar"] .stButton button:hover {
        background: rgba(124,58,237,0.3) !important;
    }

    /* ── Hide default streamlit chrome ── */
    .stDeployButton { display: none; }

    /* ── Page background ── */
    .stApp { background: #f5f3ff; }
    .main .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 1rem !important;
        max-width: 100% !important;
    }

    /* ── Top header bar ── */
    .top-header {
        background: #ffffff;
        border-radius: 14px;
        padding: 14px 20px;
        margin-bottom: 16px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        border: 0.5px solid #ede9fe;
        box-shadow: 0 1px 4px rgba(124,58,237,0.08);
    }
    .top-header-title {
        font-size: 17px;
        font-weight: 600;
        color: #1a1a2e;
        margin: 0;
        font-family: 'Inter', sans-serif;
    }
    .top-header-sub {
        font-size: 12px;
        color: #64748b;
        margin: 0;
        font-family: 'Inter', sans-serif;
    }
    .status-dot {
        font-size: 11px;
        padding: 4px 12px;
        background: #f0fdf4;
        color: #059669;
        border-radius: 20px;
        border: 1px solid #a7f3d0;
        font-weight: 500;
        font-family: 'Inter', sans-serif;
    }

    /* ── Chat bubbles ── */
    .chat-wrapper {
        display: flex;
        flex-direction: column;
        gap: 10px;
        padding: 4px 0;
    }
    .msg-row-bot {
        display: flex;
        align-items: flex-start;
        gap: 10px;
        max-width: 78%;
    }
    .msg-row-user {
        display: flex;
        align-items: flex-start;
        flex-direction: row-reverse;
        gap: 10px;
        max-width: 78%;
        align-self: flex-end;
        margin-left: auto;
    }
    .avatar-bot {
        width: 34px; height: 34px;
        border-radius: 50%;
        background: linear-gradient(135deg, #7c3aed, #4f1d9e);
        display: flex; align-items: center; justify-content: center;
        font-size: 15px; flex-shrink: 0;
        box-shadow: 0 2px 6px rgba(124,58,237,0.3);
    }
    .avatar-user {
        width: 34px; height: 34px;
        border-radius: 50%;
        background: #ede9fe;
        display: flex; align-items: center; justify-content: center;
        font-size: 11px; font-weight: 600;
        color: #7c3aed; flex-shrink: 0;
        font-family: 'Inter', sans-serif;
    }
    .bubble-bot {
        background: #ffffff;
        border-radius: 4px 14px 14px 14px;
        padding: 11px 15px;
        font-size: 14px;
        line-height: 1.6;
        color: #1e293b;
        box-shadow: 0 1px 4px rgba(124,58,237,0.07);
        border: 0.5px solid #ede9fe;
        font-family: 'Inter', sans-serif;
    }
    .bubble-user {
        background: #7c3aed;
        border-radius: 14px 4px 14px 14px;
        padding: 11px 15px;
        font-size: 14px;
        line-height: 1.6;
        color: #ffffff;
        font-family: 'Inter', sans-serif;
    }

    /* ── Input area ── */
    .stTextInput input {
        border: none !important;
        background: transparent !important;
        box-shadow: none !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 14px !important;
    }
    .stForm {
        border: none !important;
        padding: 0 !important;
    }
    .stFormSubmitButton button {
        background: #7c3aed !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 8px 20px !important;
        font-weight: 500 !important;
        font-family: 'Inter', sans-serif !important;
    }
    .stFormSubmitButton button:hover {
        background: #6d28d9 !important;
    }

/* ── Booking summary card ── */
    .booking-card {
        background: rgba(124,58,237,0.15);
        border-radius: 10px;
        padding: 12px;
        border: 0.5px solid rgba(124,58,237,0.3);
    }
    .booking-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 5px 0;
        border-bottom: 0.5px solid rgba(255,255,255,0.1);
        font-size: 12.5px;
        font-family: 'Inter', sans-serif;
    }
    .booking-row:last-child { border-bottom: none; }
    .bkey { color: rgba(255,255,255,0.6); }
    .bval { color: #ffffff; font-weight: 500; text-align: right; max-width: 110px; word-break: break-word; }
    .bval-pending { color: rgba(255,255,255,0.3); font-style: italic; font-weight: 400; }
    /* ── Success banner ── */
    .success-banner {
        background: #f0fdf4;
        border: 1px solid #a7f3d0;
        border-radius: 12px;
        padding: 16px 20px;
        text-align: center;
        margin: 12px 0;
    }
    .success-banner h3 {
        color: #065f46;
        font-size: 16px;
        margin: 0 0 4px;
        font-family: 'Inter', sans-serif;
    }
    .success-banner p {
        color: #059669;
        font-size: 13px;
        margin: 0;
        font-family: 'Inter', sans-serif;
    }

    /* ── Info tip ── */
    .info-tip {
        background: #f5f3ff;
        border: 1px solid #ede9fe;
        border-radius: 8px;
        padding: 9px 12px;
        font-size: 12px;
        color: #7c3aed;
        line-height: 1.5;
        margin-top: 8px;
        font-family: 'Inter', sans-serif;
    }

    /* ── Typing indicator ── */
    .typing-indicator {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 4px 0;
    }
    .typing-dots {
        display: flex;
        gap: 4px;
        background: #ffffff;
        border-radius: 4px 14px 14px 14px;
        padding: 11px 15px;
        box-shadow: 0 1px 4px rgba(124,58,237,0.07);
        border: 0.5px solid #ede9fe;
    }
    .typing-dots span {
        width: 8px;
        height: 8px;
        background: #7c3aed;
        border-radius: 50%;
        display: inline-block;
        animation: typingBounce 1.2s infinite ease-in-out;
    }
    .typing-dots span:nth-child(1) { animation-delay: 0s; }
    .typing-dots span:nth-child(2) { animation-delay: 0.2s; }
    .typing-dots span:nth-child(3) { animation-delay: 0.4s; }
    @keyframes typingBounce {
        0%, 60%, 100% { opacity: 0.2; transform: scale(0.8); }
        30% { opacity: 1; transform: scale(1.2); }
    }

    /* ── Step items in sidebar ── */
    .step-item-done   { opacity: 0.65; }
    .step-item-active { font-weight: 600; }
    .step-item-future { opacity: 0.35; }
/* ── Streamlit buttons global ── */
    .stButton button {
        font-family: 'Inter', sans-serif !important;
        border-radius: 8px !important;
    }
    /* Position << button top right */
    [data-testid="stSidebarCollapseButton"] {
        position: absolute !important;
        top: 12px !important;
        right: 12px !important;
    }
    /* ── Sidebar toggle buttons ── */
    button[data-testid="baseButton-headerNoPadding"] {
        background: #7c3aed !important;
        border-radius: 8px !important;
        border: 2px solid #a855f7 !important;
        width: 32px !important;
        height: 32px !important;
        opacity: 1 !important;
    }
    button[data-testid="baseButton-headerNoPadding"] svg {
        fill: white !important;
        color: white !important;
        opacity: 1 !important;
        stroke: white !important;
    }
    button[data-testid="baseButton-headerNoPadding"] svg path {
        fill: white !important;
        stroke: white !important;
    }
    [data-testid="collapsedControl"] {
        background: #1a1a2e !important;
        opacity: 1 !important;
    }
    [data-testid="collapsedControl"] button {
        background: #7c3aed !important;
        border: 2px solid #a855f7 !important;
        border-radius: 0 8px 8px 0 !important;
        color: white !important;
        opacity: 1 !important;
        width: 28px !important;
        height: 48px !important;
    }
    [data-testid="collapsedControl"] svg {
        fill: white !important;
        color: white !important;
        opacity: 1 !important;
    }
    /* Always visible sidebar collapse button */
    [data-testid="stSidebarCollapseButton"] {
        opacity: 1 !important;
        visibility: visible !important;
    }
    [data-testid="stSidebarCollapseButton"] button {
        background: #7c3aed !important;
        border: 2px solid #a855f7 !important;
        border-radius: 8px !important;
        opacity: 1 !important;
        visibility: visible !important;
    }
    [data-testid="stSidebarCollapseButton"] svg {
        fill: white !important;
        stroke: white !important;
        opacity: 1 !important;
    }
    [data-testid="stSidebarCollapseButton"] svg path {
        fill: white !important;
        stroke: white !important;
    }
    /* Override hover-only behavior */
    section[data-testid="stSidebar"]:not(:hover) [data-testid="stSidebarCollapseButton"] {
        opacity: 1 !important;
        visibility: visible !important;
        display: block !important;
    }
    </style>
    """, unsafe_allow_html=True)


# ─── PAGE HEADER ─────────────────────────────────────────────────────────────
# ✅ REPLACE WITH
def render_page_header() -> None:
    st.set_page_config(
        page_title="MediBook – AI Scheduler",
        page_icon="🏥",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    inject_css()

# ─── TOP BAR (replaces st.title) ─────────────────────────────────────────────
def render_top_bar(patient_name: str = "") -> None:
    subtitle = f"Hi {patient_name}, let's find you the right doctor" if patient_name else "AI-Powered Appointment Scheduling"
    st.markdown(f"""
    <div class="top-header">
        <div>
            <p class="top-header-title">🏥 MediBook</p>
            <p class="top-header-sub">{subtitle}</p>
        </div>
        <span class="status-dot">● Online</span>
    </div>
    """, unsafe_allow_html=True)


def render_chat_message(role: str, content: str) -> None:
    """Render a single styled chat bubble."""
    if role == "user":
        st.markdown(f"""
        <div class="msg-row-user">
            <div class="avatar-user">ME</div>
            <div class="bubble-user">{content}</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Replace emoji with styled HTML symbols
        styled = content \
            .replace("✅", '<span style="color:#22c55e;font-size:15px;font-weight:700;">✔</span>') \
            .replace("❌", '<span style="color:#ef4444;font-size:15px;font-weight:700;">✘</span>') \
            .replace("⚠️", '<span style="color:#f59e0b;font-size:15px;font-weight:700;">⚠</span>') \
            .replace("🎉", "🎉") \
            .replace("📋", "📋")
        st.markdown(f"""
        <div class="msg-row-bot">
            <div class="avatar-bot">🤖</div>
            <div class="bubble-bot">{styled}</div>
        </div>
        """, unsafe_allow_html=True)


def render_chat_history(messages: List[Dict[str, str]]) -> None:
    """Render full conversation history."""
    st.markdown('<div class="chat-wrapper">', unsafe_allow_html=True)
    for message in messages:
        render_chat_message(
            message.get('role', 'assistant'),
            message.get('content', '')
        )
    st.markdown('</div>', unsafe_allow_html=True)


# ─── INPUT FORM ───────────────────────────────────────────────────────────────
def render_input_form() -> Optional[str]:
    """Render the styled input form."""
    with st.form(key="user_input_form", clear_on_submit=True):
        col_inp, col_btn = st.columns([5, 1])
        with col_inp:
            user_input = st.text_input(
                "response",
                placeholder="Type your answer here...",
                label_visibility="collapsed"
            )
        with col_btn:
            submitted = st.form_submit_button("Send ↗", use_container_width=True)

        if submitted and user_input.strip():
            return user_input.strip()
    return None


# ── Sidebar ────────────────────────────────────────────────────────────────────
# ─── UPDATED SIDEBAR (left — past appointments) ───────────────────────────────
def render_sidebar_info(state_dict: Dict, manager=None) -> None:
    with st.sidebar:
        # Logo
        st.markdown("""
        <div style="display:flex;align-items:center;gap:10px;padding:8px 0 16px;
                    border-bottom:1px solid rgba(124,58,237,0.2);margin-bottom:12px;">
            <div style="width:36px;height:36px;background:linear-gradient(135deg,#7c3aed,#4f1d9e);
                        border-radius:10px;display:flex;align-items:center;justify-content:center;
                        font-size:18px;">🏥</div>
            <div>
                <div style="font-size:15px;font-weight:600;color:#fff;">MediBook</div>
                <div style="font-size:10px;color:rgba(255,255,255,0.35);">AI Scheduler</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # New appointment button
        if st.button("✏️ New Appointment", use_container_width=True, key="new_appt_btn"):
            st.session_state.pop('session_manager', None)
            st.rerun()

        st.markdown("<div style='margin:8px 0;'></div>", unsafe_allow_html=True)

        # Past appointments from DB
        st.markdown("""
        <div style="font-size:10px;color:rgba(255,255,255,0.35);text-transform:uppercase;
                    letter-spacing:0.1em;margin-bottom:8px;">
            Past Appointments
        </div>
        """, unsafe_allow_html=True)

        try:
            from database.db import get_appointments_by_session
            session_id = manager.thread_id if manager else ''
            appointments = get_appointments_by_session(session_id) if session_id else []
            if appointments:
                for appt in appointments[:10]:
                    name = appt.get('patient_name', 'Unknown')[:12]
                    doctor = appt.get('doctor_name', '').replace('Dr. ', 'Dr.')[:15]
                    appt_date = appt.get('appointment_date', '')
                    appt_id = appt.get('appointment_id', '')
                    label = f"👤 {name} · {doctor} · {appt_date}"
                    if st.button(label, key=f"sidebar_appt_{appt_id}",
                                 use_container_width=True):
                        st.session_state['viewed_appt'] = appt
                        st.rerun()
            else:
                st.markdown("""
                <div style="font-size:12px;color:rgba(255,255,255,0.25);
                            padding:8px;text-align:center;">
                    No past appointments
                </div>
                """, unsafe_allow_html=True)
        except Exception:
            st.markdown("""
            <div style="font-size:12px;color:rgba(255,255,255,0.25);padding:8px;">
                No history yet
            </div>
            """, unsafe_allow_html=True)
            
# ─── STATUS PANEL (right column) ─────────────────────────────────────────────
def render_state_info(state_dict: Dict) -> None:
    """Live booking status card in the right panel."""
    if not state_dict:
        return

    st.markdown("##### 📋 Booking Status")

    fields = [
        ("Patient",      state_dict.get('patient_name', '')),
        ("Type",         state_dict.get('patient_type', '')),
        ("Doctor",       state_dict.get('preferred_doctor', '')),
        ("Date",         state_dict.get('appointment_date', '')),
        ("Time",         state_dict.get('selected_time', '')),
        ("Duration",     f"{state_dict.get('appointment_duration', '')} min"
                         if state_dict.get('appointment_duration') else ''),
        ("Insurance",    state_dict.get('insurance_carrier', '')),
    ]

    rows_html = ""
    for label, val in fields:
        if val and val.strip() and val != " min":
            rows_html += (f'<div class="booking-row">'
                          f'<span class="bkey">{label}</span>'
                          f'<span class="bval">{val}</span></div>')

    if state_dict.get('appointment_id'):
        rows_html += (f'<div class="booking-row">'
                      f'<span class="bkey">Appt ID</span>'
                      f'<span class="bval" style="color:#059669;font-size:11px;">'
                      f'{state_dict["appointment_id"]}</span></div>')

    if rows_html:
        st.markdown(f'<div class="booking-card">{rows_html}</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="booking-card"><span class="bval-pending" '
                    'style="font-size:12px;">Collecting info...</span></div>',
                    unsafe_allow_html=True)


def render_workflow_status(complete: bool, success: bool = False, error: str = "") -> None:
    """Show workflow completion state."""
    if not complete:
        return
    st.divider()
    if success:
        st.markdown("""
        <div class="success-banner">
            <h3>✅ Appointment Confirmed!</h3>
            <p>Check Booking Status for your appointment ID.</p>
        </div>
        """, unsafe_allow_html=True)
    elif error:
        st.error(f"❌ {error}")
    else:
        st.warning("⚠️ Booking was not completed.")


# ─── AVAILABLE SLOTS ─────────────────────────────────────────────────────────
def render_available_slots(slots: List[str]) -> None:
    """Display available time slots as pills."""
    if not slots:
        return
    st.markdown("**Available slots:**")
    cols = st.columns(3)
    for idx, slot in enumerate(slots):
        with cols[idx % 3]:
            st.button(slot, key=f"slot_{idx}", use_container_width=True)


# ─── FORMAT AGENT OUTPUT ─────────────────────────────────────────────────────
def format_agent_output(output: str) -> str:
    """Clean up raw agent output — remove banners, ASCII art, extra blanks."""
    if not output:
        return ""
    lines = output.split('\n')
    cleaned, prev_blank = [], False
    for line in lines:
        stripped = line.strip()
        if not stripped:
            if not prev_blank:
                cleaned.append('')
                prev_blank = True
            continue
        prev_blank = False
        if all(c in '=-_*' for c in stripped):
            continue
        if stripped.startswith('🏥') and 'Scheduler' in stripped:
            continue
        cleaned.append(stripped)
    return '\n'.join(cleaned).strip()


def render_typing_indicator() -> None:
    """Show animated typing dots in chat."""
    st.markdown("""
    <div class="typing-indicator">
        <div class="avatar-bot">🤖</div>
        <div class="typing-dots">
            <span></span><span></span><span></span>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ─── RIGHT PANEL (always visible) ────────────────────────────────────────────
def render_right_panel(state_dict: Dict, manager) -> None:
    """Right panel — progress + booking summary. Always visible."""
    
    current_step = state_dict.get('current_step', 'greeting')
    current_idx = STEP_KEYS.index(current_step) if current_step in STEP_KEYS else 0
    pct = int((current_idx / len(STEPS)) * 100)

    st.markdown("""
    <div style="font-size:10px;color:#94a3b8;text-transform:uppercase;
                letter-spacing:0.1em;margin-bottom:10px;
                font-family:'Geist Sans',sans-serif;">
        Your Progress
    </div>
    """, unsafe_allow_html=True)

    for i, (key, label) in enumerate(STEPS):
        if i < current_idx:
            icon, icon_color = "✔", "#22c55e"
            bg, border = "rgba(34,197,94,0.08)", "rgba(34,197,94,0.2)"
            color, weight = "#64748b", "400"
        elif i == current_idx:
            icon, icon_color = "▶", "#7c3aed"
            bg, border = "rgba(124,58,237,0.08)", "rgba(124,58,237,0.3)"
            color, weight = "#1a1a2e", "600"
        else:
            icon, icon_color = str(i+1), "#cbd5e1"
            bg, border = "transparent", "transparent"
            color, weight = "#cbd5e1", "400"

        st.markdown(f"""
        <div style="display:flex;align-items:center;gap:8px;padding:6px 8px;
                    margin-bottom:3px;border-radius:8px;background:{bg};
                    border:1px solid {border};">
            <div style="width:20px;height:20px;border-radius:50%;
                        background:rgba(124,58,237,0.1);display:flex;
                        align-items:center;justify-content:center;
                        font-size:10px;color:{icon_color};
                        font-weight:700;flex-shrink:0;">{icon}</div>
            <div style="font-size:12px;color:{color};font-weight:{weight};
                        font-family:'Geist Sans',sans-serif;">{label}</div>
        </div>
        """, unsafe_allow_html=True)

    # Progress bar
    st.markdown(f"""
    <div style="margin:10px 0 16px;">
        <div style="display:flex;justify-content:space-between;margin-bottom:4px;">
            <div style="font-size:10px;color:#94a3b8;">Step {current_idx+1} of {len(STEPS)}</div>
            <div style="font-size:10px;color:#7c3aed;font-weight:500;">{pct}%</div>
        </div>
        <div style="height:4px;background:#f1f5f9;border-radius:4px;">
            <div style="height:100%;width:{pct}%;
                        background:linear-gradient(90deg,#7c3aed,#a855f7);
                        border-radius:4px;"></div>
        </div>
    </div>
    <hr style="border-color:#f1f5f9;margin:0 0 12px;">
    """, unsafe_allow_html=True)

    # Booking summary
    st.markdown("""
    <div style="font-size:10px;color:#94a3b8;text-transform:uppercase;
                letter-spacing:0.1em;margin-bottom:8px;
                font-family:'Geist Sans',sans-serif;">
        Booking Summary
    </div>
    """, unsafe_allow_html=True)

    fields = [
        ("👤 Patient",   state_dict.get('patient_name', '')),
        ("👨‍⚕️ Doctor",   state_dict.get('preferred_doctor', '')),
        ("📅 Date",      state_dict.get('appointment_date', '')),
        ("🕐 Time",      state_dict.get('selected_time', '')),
        ("🏥 Insurance", state_dict.get('insurance_carrier', '')),
    ]
    rows = ""
    for label, val in fields:
        v = val if val else "—"
        vc = "#1a1a2e" if val else "#cbd5e1"
        rows += (
            f'<div style="display:flex;justify-content:space-between;'
            f'padding:5px 0;border-bottom:1px solid #f1f5f9;">'
            f'<span style="font-size:11px;color:#94a3b8;">{label}</span>'
            f'<span style="font-size:11px;color:{vc};font-weight:500;'
            f'text-align:right;max-width:100px;word-break:break-word;">{v}</span>'
            f'</div>'
        )
    if state_dict.get('appointment_id'):
        rows += (
            f'<div style="display:flex;justify-content:space-between;padding:5px 0;">'
            f'<span style="font-size:11px;color:#94a3b8;">🎫 ID</span>'
            f'<span style="font-size:11px;color:#7c3aed;font-weight:600;">'
            f'{state_dict["appointment_id"]}</span></div>'
        )

    st.markdown(
        f'<div style="background:#f8fafc;border-radius:10px;padding:10px 12px;'
        f'border:1px solid #e2e8f0;">{rows}</div>',
        unsafe_allow_html=True
    )

    if state_dict.get('booking_confirmed'):
        st.markdown("""
        <div style="background:#f0fdf4;border:1px solid #a7f3d0;border-radius:8px;
                    padding:8px 12px;margin-top:10px;text-align:center;">
            <div style="font-size:12px;color:#059669;font-weight:600;">
                ✔ Appointment Confirmed!
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='margin-top:12px;'></div>", unsafe_allow_html=True)
    if st.button("🔄 New Conversation", use_container_width=True, key="right_new_conv"):
        st.session_state.pop('session_manager', None)
        st.rerun()

