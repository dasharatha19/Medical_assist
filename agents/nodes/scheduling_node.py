"""
Scheduling Node - Chat UI Compatible Version
Handles doctor selection, date, and time slot — one field per turn.
No print() or input() calls. Everything goes through state.get("response").
"""
import logging
from datetime import datetime, timedelta
from agents.state import SchedulerState
from tools import tools
from utils import (
    get_prompt_text_safe,
    get_section_safe,
    format_prompt,
    SchedulingValidator,
    EdgeCaseValidator,
    ConfirmationValidator
)

logger = logging.getLogger(__name__)


def scheduling_node(state: SchedulerState) -> SchedulerState:

    max_retries = 3
    user_input = (state.get("user_input") or "").strip()

    # Cancellation check
    if user_input.lower() in ['cancel', 'quit', 'exit']:
        state["workflow_complete"] =True
        state["error_message"] ="Scheduling cancelled by user"
        state["response"] ="❌ Scheduling cancelled. Click **New Conversation** to restart."
        return state

    # ✅ Use scheduling_step — never touches collecting_step
    if not state.get("scheduling_step"):
        state["scheduling_step"] ="show_doctors"
        state["doctor_retry"] =0
        state["date_retry"] =0
        state["slot_retry"] =0

    # =========================================================================
    # STEP 1: SHOW DOCTORS LIST
    # =========================================================================
    if state.get("scheduling_step") == "show_doctors":
        try:
            doctors = tools.schedule_checker.get_doctors()
        except Exception as e:
            logger.error(f"Doctor fetch error: {e}")
            state["workflow_complete"] =True
            state["error_message"] =f"Could not fetch doctors: {str(e)}"
            state["response"] =f"❌ Could not fetch doctors: {str(e)}"
            return state

        if not doctors:
            state["workflow_complete"] =True
            state["error_message"] ="No doctors available"
            state["response"] ="❌ No doctors are currently available. Please try again later."
            return state

        state["available_doctors"] =doctors

        doctor_list = "\n".join([
            f"  {i}. {d['name']} - {d.get('specialization','General')} @ {d.get('location','Unknown')}"
            for i, d in enumerate(doctors, 1)
        ])

        state["scheduling_step"] ="select_doctor"
        state["doctor_retry"] =0
        state["response"] =(
            "👨‍⚕️ **Available Doctors:**\n\n"
            f"{doctor_list}\n\n"
            "Please enter the **number** of your preferred doctor:"
        )
        return state

    # =========================================================================
    # STEP 2: COLLECT DOCTOR SELECTION
    # =========================================================================
    if state.get("scheduling_step") == "select_doctor":
        doctors = state.get("available_doctors") or []

        try:
            choice = int(user_input)
            if 1 <= choice <= len(doctors):
                selected = doctors[choice - 1]
                state["preferred_doctor"] =selected['name']
                state["scheduling_step"] ="select_date"
                state["date_retry"] =0
                logger.info(f"Doctor selected: {state.get("preferred_doctor")}")
                available_dates = []
                for i in range(1, 15):
                    d = (datetime.now() + timedelta(days=i)).strftime("%Y-%m-%d")
                    weekday = (datetime.now() + timedelta(days=i)).strftime("%A")
                    if weekday != "Sunday":  # Skip Sundays
                        available_dates.append(f"  • {d} ({weekday})")

                dates_text = "\n".join(available_dates[:7])  # Show next 7 days

                state["response"] = (
                    f"✅ Great! You selected **{state.get('preferred_doctor')}**.\n\n"
                    f"📅 **Available dates:**\n{dates_text}\n\n"
                    "Please enter your preferred date *(format: YYYY-MM-DD)*:"
                )
                return state
            else:
                raise ValueError("out of range")
        except ValueError:
            state["doctor_retry"] = state.get("doctor_retry", 0) + 1
            remaining = max_retries - state.get("doctor_retry")
            if remaining <= 0:
                state["workflow_complete"] =True
                state["error_message"] ="Too many invalid doctor selections"
                state["response"] ="❌ Too many invalid attempts. Click **New Conversation** to restart."
                return state
            state["response"] =(
                f"⚠️ Invalid selection. Please enter a number between 1 and {len(doctors)}. "
                f"({remaining} attempt(s) left)"
            )
            return state

    # =========================================================================
    # STEP 3: COLLECT APPOINTMENT DATE
    # =========================================================================
    if state.get("scheduling_step") == "select_date":
        valid, result = SchedulingValidator.validate_appointment_date(user_input)

        if valid:
            state["appointment_date"] =user_input.strip()
            logger.info(f"Date selected: {state.get("appointment_date")}")

            try:
                availability = tools.schedule_checker.check_availability(
                    state.get("preferred_doctor"),
                    state.get("appointment_date"),
                    state.get("appointment_duration")
                )
            except Exception as e:
                state["workflow_complete"] =True
                state["error_message"] =f"Availability check failed: {str(e)}"
                state["response"] =f"❌ Could not check availability: {str(e)}"
                return state

            if not availability.get('available', False):
                alternatives = availability.get('alternative_dates', [])
                alt_text = ""
                if alternatives:
                    alt_list = "\n".join([f"  • {d}" for d in alternatives[:3]])
                    alt_text = f"\n\n💡 **Alternative dates:**\n{alt_list}"

                state["date_retry"] = state.get("date_retry", 0) + 1
                if state.get("date_retry") >= max_retries:
                    state["workflow_complete"] =True
                    state["response"] ="❌ Too many attempts. Click **New Conversation** to restart."
                    return state

                state["scheduling_step"] ="retry_date"
                state["response"] =(
                    f"❌ No slots available on **{state.get("appointment_date")}**.{alt_text}\n\n"
                    "Would you like to try a different date? *(yes/no)*"
                )
                return state

            slots = availability.get('slots', [])
            slots_ok, slots_msg = EdgeCaseValidator.check_slot_availability(slots)
            if not slots_ok:
                state["workflow_complete"] =True
                state["error_message"] =slots_msg
                state["response"] =f"❌ {slots_msg}"
                return state

            state["available_slots"] =slots
            slot_list = "\n".join([f"  {i}. {s}" for i, s in enumerate(slots, 1)])

            state["scheduling_step"] ="select_slot"
            state["slot_retry"] =0
            state["response"] =(
                f"✅ Available slots on **{state.get("appointment_date")}**:\n\n"
                f"{slot_list}\n\n"
                "Please enter the **number** of your preferred time slot:"
            )
            return state

        else:
            state["date_retry"] = state.get("date_retry", 0) + 1
            remaining = max_retries - state.get("date_retry")
            if remaining <= 0:
                state["workflow_complete"] =True
                state["error_message"] ="Too many invalid date entries"
                state["response"] ="❌ Too many invalid attempts. Click **New Conversation** to restart."
                return state
            state["response"] =(
                f"⚠️ Invalid date: {result}\n\n"
                f"Please use **YYYY-MM-DD** format (e.g. `2025-06-15`). "
                f"({remaining} attempt(s) left)"
            )
            return state

    # =========================================================================
    # STEP 4: RETRY DATE
    # =========================================================================
    if state.get("scheduling_step") == "retry_date":
        is_valid, is_yes = ConfirmationValidator.validate_yes_no_response(user_input)

        if is_valid and is_yes:
            state["scheduling_step"] ="select_date"
            state["response"] ="📅 Please enter a new **appointment date**: *(format: YYYY-MM-DD)*"
            return state
        else:
            state["workflow_complete"] =True
            state["response"] ="❌ Scheduling cancelled. Click **New Conversation** to restart."
            return state

    # =========================================================================
    # STEP 5: COLLECT TIME SLOT
    # =========================================================================
    if state.get("scheduling_step") == "select_slot":
        slots = state.get("available_slots") or []

        try:
            choice = int(user_input)
            if 1 <= choice <= len(slots):
                state["selected_slot"] =slots[choice - 1]
                state["selected_time"] =slots[choice - 1]

                valid_time, _ = SchedulingValidator.validate_time_slot(state.get("selected_time"))
                if not valid_time:
                    state["response"] ="⚠️ Invalid time format. Please select again."
                    return state

                valid_dur, _ = SchedulingValidator.validate_duration_match(state.get("appointment_duration"))
                if not valid_dur:
                    state["workflow_complete"] =True
                    state["error_message"] =f"Invalid duration: {state.get("appointment_duration")}"
                    state["response"] ="❌ Appointment duration error. Please restart."
                    return state

                state["scheduling_step"] ="done"
                state["current_step"] ="insurance"
                logger.info(f"Slot selected: {state.get("selected_time")} on {state.get("appointment_date")}")
                state["response"] =(
                    f"✅ **Appointment Scheduled!**\n\n"
                    f"**Doctor:** {state.get("preferred_doctor")}\n"
                    f"**Date:** {state.get("appointment_date")}\n"
                    f"**Time:** {state.get("selected_time")}\n"
                    f"**Duration:** {state.get("appointment_duration")} minutes\n\n"
                    "Now let's collect your **insurance information**. 🏥"
                )
                return state
            else:
                raise ValueError("out of range")

        except ValueError:
            state["slot_retry"] = state.get("slot_retry", 0) + 1
            remaining = max_retries - state.get("slot_retry")
            if remaining <= 0:
                state["workflow_complete"] =True
                state["error_message"] ="Too many invalid slot selections"
                state["response"] ="❌ Too many invalid attempts. Click **New Conversation** to restart."
                return state
            state["response"] =(
                f"⚠️ Invalid selection. Please enter a number between 1 and {len(slots)}. "
                f"({remaining} attempt(s) left)"
            )
            return state

    # Fallback
    logger.error(f"Unknown scheduling_step: {state.get("scheduling_step")}")
    state["response"] ="⚠️ Something went wrong. Please click **New Conversation** to restart."
    state["workflow_complete"] =True
    return state