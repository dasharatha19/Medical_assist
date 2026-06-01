"""
Appointment Scheduler Agent State
TypedDict-based state for LangGraph compatibility
"""
from typing import Optional, List
from typing_extensions import TypedDict


class SchedulerState(TypedDict, total=False):

    # Patient Information
    patient_name: str
    patient_dob: str
    patient_id: str
    patient_type: str
    appointment_duration: int

    # Contact Information
    patient_email: str
    patient_phone: str

    # Scheduling Information
    preferred_doctor: str
    appointment_date: str
    available_slots: List[str]
    selected_slot: str
    selected_time: str

    # Insurance Information
    insurance_carrier: str
    insurance_member_id: str
    insurance_group_id: str
    insurance_valid: bool

    # Appointment Booking
    appointment_id: str
    booking_confirmed: bool
    booking_success: bool

    # Reminders
    reminders_setup: bool
    reminders_count: int

    # Scheduling sub-step tracking
    available_doctors: list
    doctor_retry: int
    date_retry: int
    slot_retry: int
    scheduling_step: str

    # Insurance step tracking
    insurance_step: str
    available_carriers: list
    carrier_retry: int
    member_retry: int
    group_retry: int

    # Form Distribution
    form_created: bool
    form_sent: bool
    form_token: str
    form_url: str
    form_type: str
    form_distribution_status: str

    # New patient flag
    is_new_patient: bool

    # Workflow Control
    current_step: str
    error_message: str
    retry_count: int
    workflow_complete: bool

    # Chat UI Field Collection Tracking
    collecting_step: str
    name_asked: bool
    name_retry: int
    dob_retry: int
    phone_retry: int
    email_retry: int
    response: str

    # Confirmation tracking
    confirmation_step: str
    confirmation_retry: int

    # User Input
    user_input: str

    # Confirmation Status
    booking_confirmation_status: str

    # Email Validation
    patient_email_validated: bool

    # ── Intelligent Agent Fields ──
    conversation_phase: str      # "greeting"|"collecting"|"scheduling"|"insurance"|"confirming"|"done"
    intent: str                  # last detected intent from Gemini
    missing_fields: list         # list of fields still needed
    conversation_context: list   # full conversation for Gemini context
    db_saved: bool               # whether appointment saved to DB

    # Session isolation
    session_id: str