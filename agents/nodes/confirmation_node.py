"""
Confirmation Node - Chat UI Compatible Version
No print() or input() calls. Everything goes through state.get("response").
Uses state.get("confirmation_step") to track progress across turns.
"""
import logging
from agents.state import SchedulerState
from utils import (
    get_prompt_text_safe,
    ConfirmationValidator,
    EdgeCaseValidator
)

logger = logging.getLogger(__name__)


def confirmation_node(state: SchedulerState) -> SchedulerState:

    user_input = (state.get("user_input") or "").strip()

    # Cancellation check
    if user_input.lower() in ['cancel', 'quit', 'exit']:
        state["workflow_complete"] =True
        state["booking_confirmed"] =False
        state["error_message"] ="Confirmation cancelled by user"
        state["response"] ="❌ Booking cancelled. Click **New Conversation** to restart."
        return state

    # Initialize on first entry
    if not state.get("confirmation_step"):
        state["confirmation_step"] ="show_summary"
        state["confirmation_retry"] =0

    # =========================================================================
    # STEP 1: CHECK COMPLETENESS + SHOW SUMMARY
    # =========================================================================
    if state.get("confirmation_step") == "show_summary":

        # Check completeness
        state_dict = {
            'patient_name': state.get("patient_name"),
            'patient_dob': state.get("patient_dob"),
            'patient_email': state.get("patient_email"),
            'patient_phone': state.get("patient_phone"),
            'preferred_doctor': state.get("preferred_doctor"),
            'appointment_date': state.get("appointment_date"),
            'selected_time': state.get("selected_time"),
            'insurance_carrier': state.get("insurance_carrier"),
        }

        is_complete, missing_fields = EdgeCaseValidator.check_appointment_completeness(state_dict)

        if not is_complete:
            missing_str = ", ".join(missing_fields)
            logger.error(f"Incomplete appointment: {missing_str}")
            state["workflow_complete"] =True
            state["error_message"] =f"Incomplete appointment: missing {missing_str}"
            state["response"] =(
                f"❌ Appointment is incomplete. Missing: **{missing_str}**\n\n"
                "Please click **New Conversation** and try again."
            )
            return state

        # Build summary directly from state (no get_summary() print)
        insurance_display = state.get("insurance_carrier") if state.get("insurance_carrier") else "None"
        summary = (
            "📋 **Appointment Summary**\n\n"
            f"**Patient:** {state.get("patient_name")}\n"
            f"**Date of Birth:** {state.get("patient_dob")}\n"
            f"**Email:** {state.get("patient_email")}\n"
            f"**Phone:** {state.get("patient_phone")}\n\n"
            f"**Doctor:** {state.get("preferred_doctor")}\n"
            f"**Date:** {state.get("appointment_date")}\n"
            f"**Time:** {state.get("selected_time")}\n"
            f"**Duration:** {state.get("appointment_duration")} minutes\n\n"
            f"**Insurance:** {insurance_display}\n"
            f"**Member ID:** {state.get("insurance_member_id") or 'N/A'}\n"
            f"**Group ID:** {state.get("insurance_group_id") or 'N/A'}\n\n"
            "---\n"
            "✅ Would you like to **confirm** this appointment? *(yes/no)*"
        )

        state["confirmation_step"] ="collect_confirmation"
        state["confirmation_retry"] =0
        state["response"] =summary
        return state

    # =========================================================================
    # STEP 2: COLLECT YES/NO CONFIRMATION
    # =========================================================================
    if state.get("confirmation_step") == "collect_confirmation":
        if not user_input:
            state["response"] = "✅ Would you like to **confirm** this appointment? *(yes/no)*"
            return state
        is_valid, is_affirmative = ConfirmationValidator.validate_yes_no_response(user_input)

        if not is_valid:
            state["confirmation_retry"] = state.get("confirmation_retry", 0) + 1
            remaining = 3 - state.get("confirmation_retry")
            if remaining <= 0:
                state["workflow_complete"] =True
                state["booking_confirmed"] =False
                state["error_message"] ="Too many invalid confirmation responses"
                state["response"] ="❌ Too many invalid responses. Click **New Conversation** to restart."
                return state
            state["response"] =(
                f"⚠️ Please answer **yes** or **no**. ({remaining} attempt(s) left)"
            )
            return state

        if not is_affirmative:
            # User declined — ask for reason
            state["confirmation_step"] ="collect_reason"
            state["response"] =(
                get_prompt_text_safe('confirmation_prompt', 'NOT_CONFIRMED',
                                     default='😔 Sorry to hear that.') +
                "\n\n📝 Could you tell us why you're declining? *(optional — press Enter to skip)*"
            )
            return state

        # User confirmed
        logger.info("Appointment confirmed by user")
        state["booking_confirmed"] =True
        state["booking_confirmation_status"] ="confirmed"
        state["confirmation_step"] ="done"
        state["current_step"] ="reminders"
        state["response"] =(
            get_prompt_text_safe('confirmation_prompt', 'CONFIRMED',
                                 default='✅ **Appointment Confirmed!** Setting up reminders and sending forms...')
        )
        return state

    # =========================================================================
    # STEP 3: COLLECT CANCELLATION REASON (OPTIONAL)
    # =========================================================================
    if state.get("confirmation_step") == "collect_reason":
        if user_input:
            reason_valid, cleaned_reason = ConfirmationValidator.validate_cancellation_reason(user_input)
            if reason_valid:
                state["error_message"] =f"Cancelled by user. Reason: {cleaned_reason}"
            else:
                state["error_message"] ="Cancelled by user"
        else:
            state["error_message"] ="Cancelled by user (no reason given)"

        logger.info(f"Appointment declined: {state.get("error_message")}")
        state["workflow_complete"] =True
        state["booking_confirmed"] =False
        state["booking_confirmation_status"] ="rejected"
        state["confirmation_step"] ="done"
        state["response"] =(
            "❌ **Appointment Cancelled.**\n\n"
            "Thank you for letting us know. Click **New Conversation** if you'd like to reschedule."
        )
        return state

    # Fallback
    logger.error(f"Unknown confirmation_step: {state.get("confirmation_step")}")
    state["response"] ="⚠️ Something went wrong. Please click **New Conversation** to restart."
    state["workflow_complete"] =True
    return state