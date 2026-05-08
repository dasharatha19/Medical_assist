"""
Reminder Node - Chat UI Compatible Version
Books appointment, sets up reminders, generates Excel report.
"""
from agents.state import SchedulerState
from tools import tools
from services import report_service
import logging

logger = logging.getLogger(__name__)


def reminder_node(state: SchedulerState) -> SchedulerState:

    if not state.get("booking_confirmed"):
        state["workflow_complete"] = True
        state["booking_success"] = False
        state["error_message"] = "Booking not confirmed"
        state["response"] = "❌ Booking was not confirmed."
        return state

    # Book the appointment
    try:
        booking_result = tools.booking.book(
            patient_id=state.get("patient_id"),
            doctor=state.get("preferred_doctor"),
            date=state.get("appointment_date"),
            time=state.get("selected_time"),
            duration=state.get("appointment_duration")
        )
    except Exception as e:
        state["booking_success"] = False
        state["error_message"] = str(e)
        state["workflow_complete"] = True
        state["response"] = f"❌ Booking failed: {str(e)}"
        return state

    if not booking_result.get('success', False):
        state["booking_success"] = False
        state["error_message"] = booking_result.get('error', 'Unknown error')
        state["workflow_complete"] = True
        state["response"] = f"❌ Booking failed: {state['error_message']}"
        return state

    # Booking successful
    state["appointment_id"] = booking_result.get('appointment_id', '')
    state["booking_success"] = True
    logger.info(f"Appointment booked: {state['appointment_id']}")

    # Generate Excel report
    try:
        report_service.record_appointment(state)
        logger.info("Admin report generated")
    except Exception as e:
        logger.warning(f"Report generation failed: {e}")

    # Setup reminders
    try:
        reminder_result = tools.reminder.setup(
            patient_id=state.get("patient_id"),
            appointment_id=state.get("appointment_id"),
            appointment_date=state.get("appointment_date"),
            appointment_time=state.get("selected_time"),
            email=state.get("patient_email"),
            phone=state.get("patient_phone")
        )
        state["reminders_setup"] = reminder_result.get('success', False)
        state["reminders_count"] = reminder_result.get('reminder_count', 0)
    except Exception as e:
        logger.warning(f"Reminder setup failed: {e}")
        state["reminders_setup"] = False
        state["reminders_count"] = 0

    state["current_step"] = "form_distribution"
    state["workflow_complete"] = False

    state["response"] = (
        f"🎉 **Appointment Confirmed & Booked!**\n\n"
        f"**Appointment ID:** {state.get('appointment_id')}\n"
        f"**Doctor:** {state.get('preferred_doctor')}\n"
        f"**Date:** {state.get('appointment_date')}\n"
        f"**Time:** {state.get('selected_time')}\n"
        f"**Duration:** {state.get('appointment_duration')} minutes\n\n"
        f"📧 **Reminders scheduled:** {state.get('reminders_count', 0)}\n"
        f"📊 Admin report generated.\n\n"
        f"Sending your intake forms now... 📋"
    )
    return state