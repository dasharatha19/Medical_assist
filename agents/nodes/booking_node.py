"""
Booking Node — executes booking after conversation_node confirms.
Correct order: book slot first → then save to DB → then report.
"""
import logging
from tools import tools
from services import report_service

logger = logging.getLogger(__name__)


def booking_node(state: dict) -> dict:
    """Books appointment — correct order prevents self-overlap detection."""
    try:
        # ── Step 1: Reserve slot via doctor_availability ──────────────────────
        # This must happen BEFORE save_appointment writes to DB
        result = tools.booking.book(
            patient_id=state.get("patient_id", "NEW"),
            doctor=state.get("preferred_doctor"),
            date=state.get("appointment_date"),
            time=state.get("selected_time"),
            duration=state.get("appointment_duration", 60)
        )

        if result.get("success"):
            state["appointment_id"]   = result.get("appointment_id")
            state["booking_success"]  = True

            # ── Step 2: Save to DB AFTER slot is reserved ─────────────────────
            try:
                from database.db import save_appointment
                save_appointment(state)
                state["db_saved"] = True
                logger.info(f"Appointment saved: {state['appointment_id']}")
            except Exception as e:
                logger.warning(f"DB save failed: {e}")

            # ── Step 3: Generate Excel report ─────────────────────────────────
            try:
                report_service.record_appointment(state)
            except Exception as e:
                logger.warning(f"Report failed: {e}")

            state["current_step"] = "reminders"
            state["response"] = (
                f"🎉 **Appointment Confirmed!**\n\n"
                f"**ID:** {state.get('appointment_id')}\n"
                f"**Doctor:** {state.get('preferred_doctor')}\n"
                f"**Date:** {state.get('appointment_date')}\n"
                f"**Time:** {state.get('selected_time')}\n\n"
                "Setting up reminders and sending intake forms..."
            )

        else:
            state["booking_success"]  = False
            state["workflow_complete"] = True
            state["response"] = (
                f"❌ Booking failed: {result.get('error')}\n\n"
                "The slot may have just been taken. "
                "Would you like to choose another time?"
            )

    except Exception as e:
        logger.error(f"Booking error: {e}")
        state["booking_success"]  = False
        state["workflow_complete"] = True
        state["response"] = f"❌ Booking error: {str(e)}"

    return state