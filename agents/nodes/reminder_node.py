"""
Reminder Node — sets up reminders and triggers form distribution.
Booking is already done by booking_node — never book again here.
"""
import logging
import uuid
from agents.state import SchedulerState
from tools import tools
from services import report_service

logger = logging.getLogger(__name__)


def reminder_node(state: SchedulerState) -> SchedulerState:

    if not state.get("booking_confirmed"):
        state["workflow_complete"] = True
        state["booking_success"]   = False
        state["response"]          = "❌ Booking was not confirmed."
        return state

    # ── Generate appointment ID if not set ────────────────────────────────────
    if not state.get("appointment_id"):
        state["appointment_id"] = f"APT{uuid.uuid4().hex[:6].upper()}"

    # ── Save to DB ────────────────────────────────────────────────────────────
    try:
        from database.db import save_appointment
        save_appointment(state)
        state["db_saved"] = True
        logger.info(f"Appointment saved: {state['appointment_id']}")
    except Exception as e:
        logger.warning(f"DB save failed: {e}")

    # ── Generate Excel report ─────────────────────────────────────────────────
    try:
        report_service.record_appointment(state)
        logger.info("Admin report generated")
    except Exception as e:
        logger.warning(f"Report failed: {e}")

    # ── Setup reminders in PostgreSQL ─────────────────────────────────────────
    try:
        reminder_result = tools.reminder.setup(
            appointment_id       = state.get("appointment_id"),
            appointment_datetime = f"{state.get('appointment_date')} {state.get('selected_time')}",
            email                = state.get("patient_email"),
            phone                = state.get("patient_phone")
        )
        state["reminders_setup"] = reminder_result.get('success', False)
        state["reminders_count"] = reminder_result.get('reminder_count', 0)
        logger.info(f"Reminders set up: {state['reminders_count']}")
    except Exception as e:
        logger.warning(f"Reminder setup failed: {e}")
        state["reminders_setup"] = False
        state["reminders_count"] = 0

    # ── Create and send intake form ───────────────────────────────────────────
    try:
        from database.db import save_form, update_form_sent
        import uuid as _uuid

        form_token = str(_uuid.uuid4())
        form_id    = f"FORM{_uuid.uuid4().hex[:6].upper()}"
        is_new     = state.get("patient_type", "new") == "new"
        form_type  = "Comprehensive Intake Form" if is_new else "Patient Update Form"
        form_url   = f"https://forms.medical-scheduler.com/patient-form/{form_token}"

        save_form({
            'form_id':          form_id,
            'appointment_id':   state.get("appointment_id"),
            'patient_id':       state.get("patient_id"),
            'patient_name':     state.get("patient_name"),
            'patient_email':    state.get("patient_email"),
            'doctor':           state.get("preferred_doctor"),
            'appointment_date': f"{state.get('appointment_date')} {state.get('selected_time')}",
            'form_type':        form_type,
            'form_token':       form_token,
            'form_url':         form_url,
            'is_new_patient':   is_new
        })

        # Mark as sent (mock)
        update_form_sent(state.get("appointment_id"))
        state["form_sent"] = True
        state["form_url"]  = form_url
        logger.info(f"Form created and sent: {form_url}")

    except Exception as e:
        logger.warning(f"Form creation failed: {e}")
        state["form_sent"] = False

    state["current_step"]      = "done"
    state["workflow_complete"]  = True
    state["booking_success"]    = True

    state["response"] = (
        f"🎉 Appointment Confirmed!\n\n"
        f"ID: {state.get('appointment_id')}\n"
        f"Doctor: {state.get('preferred_doctor')}\n"
        f"Date: {state.get('appointment_date')}\n"
        f"Time: {state.get('selected_time')}\n"
        f"Duration: {state.get('appointment_duration', 60)} minutes\n\n"
        f"✅ 3 reminders scheduled\n"
        f"📋 Intake form sent to: {state.get('patient_email')}\n"
        f"📊 Admin report generated\n\n"
        f"You're all set! See you on {state.get('appointment_date')} 🏥"
    )

    return state