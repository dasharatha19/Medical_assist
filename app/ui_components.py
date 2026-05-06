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
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,wght@0,300;0,400;0,500;0,600&display=swap');

    html, body, [class*="css"] {
        font-family: 'DM Sans', sans-serif !important;
    }

    /* ── Sidebar dark theme ── */
    section[data-testid="stSidebar"] {
        background: #0f2744 !important;
        border-right: none !important;
    }
    section[data-testid="stSidebar"] .stMarkdown p,
    section[data-testid="stSidebar"] .stMarkdown span,
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] .stButton button {
        color: rgba(255,255,255,0.8) !important;
    }
    section[data-testid="stSidebar"] hr {
        border-color: rgba(255,255,255,0.1) !important;
    }
    section[data-testid="stSidebar"] .stButton button {
        background: rgba(255,255,255,0.08) !important;
        border: 1px solid rgba(255,255,255,0.15) !important;
        border-radius: 8px !important;
    }
    section[data-testid="stSidebar"] .stButton button:hover {
        background: rgba(59,158,255,0.2) !important;
    }

    /* ── Hide default streamlit chrome ── */
    #MainMenu, footer, header { visibility: hidden; }
    .stDeployButton { display: none; }

    /* ── Page background ── */
    .stApp { background: #f0f4f8; }
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
        border: 0.5px solid #e2e8f0;
        box-shadow: 0 1px 4px rgba(0,0,0,0.05);
    }
    .top-header-title {
        font-size: 17px;
        font-weight: 600;
        color: #1a2840;
        margin: 0;
    }
    .top-header-sub {
        font-size: 12px;
        color: #64748b;
        margin: 0;
    }
    .status-dot {
        font-size: 11px;
        padding: 4px 12px;
        background: #ecfdf5;
        color: #059669;
        border-radius: 20px;
        border: 1px solid #a7f3d0;
        font-weight: 500;
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
        background: linear-gradient(135deg, #3b9eff, #0d5fcb);
        display: flex; align-items: center; justify-content: center;
        font-size: 15px; flex-shrink: 0;
        box-shadow: 0 2px 6px rgba(59,158,255,0.3);
    }
    .avatar-user {
        width: 34px; height: 34px;
        border-radius: 50%;
        background: #e2e8f0;
        display: flex; align-items: center; justify-content: center;
        font-size: 11px; font-weight: 600;
        color: #475569; flex-shrink: 0;
    }
    .bubble-bot {
        background: #ffffff;
        border-radius: 4px 14px 14px 14px;
        padding: 11px 15px;
        font-size: 14px;
        line-height: 1.6;
        color: #1e293b;
        box-shadow: 0 1px 4px rgba(0,0,0,0.07);
        border: 0.5px solid #e8edf3;
    }
    .bubble-user {
        background: #1a5cdf;
        border-radius: 14px 4px 14px 14px;
        padding: 11px 15px;
        font-size: 14px;
        line-height: 1.6;
        color: #ffffff;
    }
    .step-tag {
        display: inline-block;
        font-size: 10px;
        background: #eff6ff;
        color: #2563eb;
        border-radius: 4px;
        padding: 2px 7px;
        margin-bottom: 6px;
        font-weight: 600;
        letter-spacing: 0.05em;
        text-transform: uppercase;
    }

    /* ── Input area ── */
    .input-wrapper {
        background: #ffffff;
        border-radius: 12px;
        border: 1px solid #e2e8f0;
        padding: 4px 4px 4px 14px;
        display: flex;
        align-items: center;
        gap: 8px;
        margin-top: 12px;
    }
    .stTextInput input {
        border: none !important;
        background: transparent !important;
        box-shadow: none !important;
        font-family: 'DM Sans', sans-serif !important;
        font-size: 14px !important;
    }
    .stForm {
        border: none !important;
        padding: 0 !important;
    }
    .stFormSubmitButton button {
        background: #1a5cdf !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 8px 20px !important;
        font-weight: 500 !important;
        font-family: 'DM Sans', sans-serif !important;
    }
    .stFormSubmitButton button:hover {
        background: #1549b8 !important;
    }

    /* ── Booking summary card ── */
    .booking-card {
        background: #f8fafc;
        border-radius: 10px;
        padding: 12px;
        border: 0.5px solid #e2e8f0;
    }
    .booking-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 5px 0;
        border-bottom: 0.5px solid #f1f5f9;
        font-size: 12.5px;
    }
    .booking-row:last-child { border-bottom: none; }
    .bkey { color: #64748b; }
    .bval { color: #1e293b; font-weight: 500; text-align: right; max-width: 110px; word-break: break-word; }
    .bval-pending { color: #94a3b8; font-style: italic; font-weight: 400; }

    /* ── Success banner ── */
    .success-banner {
        background: #ecfdf5;
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
    }
    .success-banner p {
        color: #059669;
        font-size: 13px;
        margin: 0;
    }

    /* ── Info tip ── */
    .info-tip {
        background: #f0f9ff;
        border: 1px solid #bae6fd;
        border-radius: 8px;
        padding: 9px 12px;
        font-size: 12px;
        color: #0369a1;
        line-height: 1.5;
        margin-top: 8px;
    }

    /* ── Step items in sidebar ── */
    .step-item-done   { opacity: 0.65; }
    .step-item-active { font-weight: 600; }
    .step-item-future { opacity: 0.35; }
    </style>
    """, unsafe_allow_html=True)


# ─── PAGE HEADER ─────────────────────────────────────────────────────────────
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


# ─── CHAT RENDERING ───────────────────────────────────────────────────────────
def render_chat_message(role: str, content: str) -> None:
    """Render a single styled chat bubble."""
    if role == "user":
        initials = "ME"
        st.markdown(f"""
        <div class="msg-row-user">
            <div class="avatar-user">{initials}</div>
            <div class="bubble-user">{content}</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="msg-row-bot">
            <div class="avatar-bot">🤖</div>
            <div class="bubble-bot">{content}</div>
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


# ─── SIDEBAR ─────────────────────────────────────────────────────────────────
def render_sidebar_info(state_dict: Dict) -> None:
    """Redesigned sidebar with progress steps and live booking summary."""
    with st.sidebar:
        # Logo
        st.markdown("""
        <div style="display:flex;align-items:center;gap:10px;padding-bottom:14px;
                    border-bottom:1px solid rgba(255,255,255,0.1);margin-bottom:14px;">
            <div style="width:38px;height:38px;background:linear-gradient(135deg,#3b9eff,#0d5fcb);
                        border-radius:10px;display:flex;align-items:center;justify-content:center;
                        font-size:18px;">🏥</div>
            <div>
                <div style="font-size:15px;font-weight:600;color:#fff;">MediBook</div>
                <div style="font-size:11px;color:rgba(255,255,255,0.4);">AI Scheduler</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Progress steps
        current_step = state_dict.get('current_step', 'greeting')
        current_idx = STEP_KEYS.index(current_step) if current_step in STEP_KEYS else 0

        st.markdown('<div style="font-size:11px;color:rgba(255,255,255,0.4);'
                    'text-transform:uppercase;letter-spacing:0.08em;margin-bottom:8px;">'
                    'Your Progress</div>', unsafe_allow_html=True)

        for i, (key, label) in enumerate(STEPS):
            if i < current_idx:
                icon = "✅"
                css = "opacity:0.7;color:rgba(255,255,255,0.7);"
            elif i == current_idx:
                icon = "▶"
                css = "color:#fff;font-weight:600;"
            else:
                icon = f"{i+1}"
                css = "color:rgba(255,255,255,0.3);"
            st.markdown(
                f'<div style="font-size:13px;padding:4px 0;{css}">{icon} {label}</div>',
                unsafe_allow_html=True
            )

        # Progress bar
        pct = int(((current_idx) / len(STEPS)) * 100)
        st.markdown(f"""
        <div style="margin-top:14px;">
            <div style="height:3px;background:rgba(255,255,255,0.1);border-radius:2px;">
                <div style="height:100%;width:{pct}%;background:#3b9eff;border-radius:2px;
                            transition:width 0.4s ease;"></div>
            </div>
            <div style="font-size:11px;color:rgba(255,255,255,0.35);margin-top:5px;">
                Step {current_idx + 1} of {len(STEPS)}
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.divider()

        # Live booking summary
        st.markdown('<div style="font-size:11px;color:rgba(255,255,255,0.4);'
                    'text-transform:uppercase;letter-spacing:0.08em;margin-bottom:8px;">'
                    'Booking Summary</div>', unsafe_allow_html=True)

        fields = [
            ("Patient",   state_dict.get('patient_name', '')),
            ("Doctor",    state_dict.get('preferred_doctor', '')),
            ("Date",      state_dict.get('appointment_date', '')),
            ("Time",      state_dict.get('selected_time', '')),
            ("Insurance", state_dict.get('insurance_carrier', '')),
        ]

        rows_html = ""
        for label, val in fields:
            if val:
                rows_html += (f'<div class="booking-row">'
                              f'<span class="bkey">{label}</span>'
                              f'<span class="bval">{val}</span></div>')
            else:
                rows_html += (f'<div class="booking-row">'
                              f'<span class="bkey">{label}</span>'
                              f'<span class="bval-pending">—</span></div>')

        if state_dict.get('appointment_id'):
            rows_html += (f'<div class="booking-row">'
                          f'<span class="bkey">ID</span>'
                          f'<span class="bval" style="color:#059669;">'
                          f'{state_dict["appointment_id"]}</span></div>')

        st.markdown(f'<div class="booking-card">{rows_html}</div>', unsafe_allow_html=True)

        st.markdown('<div class="info-tip">🔒 Your data is private and only used for scheduling.</div>',
                    unsafe_allow_html=True)

        st.divider()

        # Controls
        st.markdown('<div style="font-size:11px;color:rgba(255,255,255,0.4);'
                    'text-transform:uppercase;letter-spacing:0.08em;margin-bottom:8px;">'
                    'Controls</div>', unsafe_allow_html=True)


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