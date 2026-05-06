"""
Patient Lookup Node - Chat UI Compatible Version
Collects patient info one field per turn (no input() calls).
Each invocation handles ONE user message, sets state.get("response"), and returns.
Tracks progress via state.get("collecting_step") across turns.
"""
import logging
from agents.state import SchedulerState
from tools import tools
from utils import (
    get_prompt_text_safe,
    get_section_safe,
    format_prompt,
    PatientDataValidator,
    ContactValidator,
    EdgeCaseValidator
)

logger = logging.getLogger(__name__)


def patient_lookup_node(state: SchedulerState) -> SchedulerState:
    """
    Chat-compatible patient lookup node.
    One user message → one field collected → one question asked back.
    Uses state.get("collecting_step") to know where we are across turns.
    """

    max_retries = 3
    user_input = (state.get("user_input") or "").strip()

    # ── Cancellation check (works at any step) ──
    if user_input.lower() in ['cancel', 'quit', 'exit']:
        state["workflow_complete"] =True
        state["error_message"] ="Patient lookup cancelled by user"
        state["response"] ="❌ Booking cancelled. Feel free to start again anytime."
        return state

    if not state.get("collecting_step"):
        state["collecting_step"] = "name"
        state["name_asked"] = True
        state["name_retry"] = 0
        state["dob_retry"] = 0
        state["phone_retry"] = 0
        state["email_retry"] = 0

    # =========================================================================
    # STEP 1: COLLECT NAME
    # =========================================================================
    if state.get("collecting_step") == "name":

        # Second pass — user_input IS the name they typed
        name_valid, name_result = PatientDataValidator.validate_name(user_input)

        if name_valid:
            state["patient_name"] =name_result
            state["collecting_step"] ="dob"
            state["dob_retry"] =0
            logger.info(f"Name collected: {name_result}")
            state["response"] =get_prompt_text_safe(
                'extraction_prompt', 'DOB',
                default='📅 What is your **date of birth**? *(format: YYYY-MM-DD)*'
            )
            return state
        else:
            state["name_retry"] = state.get("name_retry", 0) + 1
            remaining = max_retries - state.get("name_retry")
            logger.warning(f"Invalid name attempt {state.get("name_retry")}: {name_result}")
            if remaining <= 0:
                state["workflow_complete"] =True
                state["error_message"] ="Too many invalid name attempts"
                state["response"] ="❌ Too many invalid attempts. Please click **New Conversation** to restart."
                return state
            state["response"] =(
                f"⚠️ {name_result}\n\n"
                f"Please enter your full name. ({remaining} attempt(s) left)"
            )
            return state

    # =========================================================================
    # STEP 2: COLLECT DATE OF BIRTH
    # =========================================================================
    if state.get("collecting_step") == "dob":

        dob_valid, dob_result = PatientDataValidator.validate_dob(user_input)

        if dob_valid:
                    state["patient_dob"] = dob_result
                    logger.info(f"DOB collected: {dob_result}")
                    state["collecting_step"] = "lookup"
                    state["response"] = "🔍 Looking up your information..."
                    return state
        else:
            state["dob_retry"] = state.get("dob_retry", 0) + 1
            remaining = max_retries - state.get("dob_retry")
            logger.warning(f"Invalid DOB attempt {state.get("dob_retry")}: {dob_result}")
            if remaining <= 0:
                state["workflow_complete"] =True
                state["error_message"] ="Too many invalid DOB attempts"
                state["response"] ="❌ Too many invalid attempts. Please click **New Conversation** to restart."
                return state
            state["response"] =(
                f"⚠️ Invalid date format.\n\n"
                f"Please use **YYYY-MM-DD** (e.g. `1990-05-21`). "
                f"({remaining} attempt(s) left)"
            )
            return state

    # =========================================================================
    # STEP 3: PATIENT LOOKUP (runs immediately after DOB is valid)
    # =========================================================================
    if state.get("collecting_step") == "lookup":

        processing_msg = get_prompt_text_safe(
            'extraction_prompt', 'PATIENT_LOOKUP_PROCESSING',
            default='🔍 Looking up your information...'
        )
        logger.info("Starting patient lookup")

        try:
            lookup_result = tools.patient_lookup.lookup(
                state.get("patient_name"), state.get("patient_dob")
            )
        except Exception as e:
            logger.error(f"Patient lookup failed: {e}")
            state["workflow_complete"] =True
            state["error_message"] =f"Patient lookup failed: {str(e)}"
            state["response"] =format_prompt(
                get_prompt_text_safe('extraction_prompt', 'LOOKUP_ERROR',
                                     default='❌ Could not look up information: {error_message}'),
                error_message=str(e)
            )
            return state

        # Update state from lookup result
        state["patient_id"] =lookup_result.get('patient_id', 'NEW_PATIENT')
        state["patient_type"] =lookup_result.get('status', 'new')
        state["appointment_duration"] =lookup_result.get('duration_minutes', 60)
        state["is_new_patient"] =not lookup_result.get('found', False)

        if lookup_result.get('found', False):
            status_msg = format_prompt(
                get_prompt_text_safe('extraction_prompt', 'PATIENT_FOUND',
                                     default='✅ Welcome back! Your patient ID: {patient_id}. Appointment: {duration_minutes} min.'),
                patient_id=state.get("patient_id"),
                appointment_count=lookup_result.get('appointment_count', 0),
                duration_minutes=state.get("appointment_duration"),
                patient_type=state.get("patient_type")
            )
            logger.info(f"Returning patient found: {state.get("patient_id")}")
        else:
            status_msg = format_prompt(
                get_prompt_text_safe('extraction_prompt', 'PATIENT_NEW',
                                     default='👋 New patient registered! Your ID: {patient_id}. Appointment: {duration_minutes} min.'),
                patient_id=state.get("patient_id"),
                duration_minutes=state.get("appointment_duration"),
                patient_type=state.get("patient_type")
            )
            logger.info(f"New patient registered: {state.get("patient_id")}")

        state["collecting_step"] ="phone"
        state["phone_retry"] =0
        state["response"] =(
            status_msg + "\n\n" +
            get_prompt_text_safe('extraction_prompt', 'PHONE',
                                 default='📞 Please enter your **phone number**:')
        )
        return state

    # =========================================================================
    # STEP 4: COLLECT PHONE
    # =========================================================================
    if state.get("collecting_step") == "phone":
        # Guard against empty input (auto-trigger calls)
        if not user_input:
            state["response"] = "📞 Please enter your **phone number**:"
            return state

        phone_valid, phone_result = ContactValidator.validate_phone(user_input)
        if phone_valid:
            state["patient_phone"] =phone_result
            state["collecting_step"] ="email"
            state["email_retry"] =0
            logger.info(f"Phone collected: {phone_result}")
            state["response"] =get_prompt_text_safe(
                'extraction_prompt', 'EMAIL',
                default='📧 Please enter your **email address**:'
            )
            return state
        
        else:
            state["phone_retry"] = state.get("phone_retry", 0) + 1
            remaining = max_retries - state.get("phone_retry")
            logger.warning(f"Invalid phone attempt {state.get("phone_retry")}: {phone_result}")
            if remaining <= 0:
                state["workflow_complete"] =True
                state["error_message"] ="Too many invalid phone attempts"
                state["response"] ="❌ Too many invalid attempts. Please click **New Conversation** to restart."
                return state
            state["response"] =(
                f"⚠️ {phone_result}\n\n"
                f"Please enter a valid phone number. ({remaining} attempt(s) left)"
            )
            return state

    # =========================================================================
    # STEP 5: COLLECT EMAIL
    # =========================================================================
    if state.get("collecting_step") == "email":
        # Guard against empty input
        if not user_input:
            state["response"] = "📧 Please enter your **email address**:"
            return state

        email_valid, email_result = ContactValidator.validate_email(user_input)
        
        if email_valid:
            state["patient_email"] =email_result
            state["collecting_step"] ="done"
            state["current_step"] ="scheduling"
            logger.info(f"Email collected: {email_result}")
            logger.info(
                f"Patient info complete — Name: {state.get("patient_name")}, "
                f"DOB: {state.get("patient_dob")}, Phone: {state.get("patient_phone")}, "
                f"Email: {state.get("patient_email")}"
            )
            state["response"] =get_prompt_text_safe(
                'extraction_prompt', 'CONTACT_CONFIRMED',
                default='✅ All information collected! Moving to scheduling...'
            )
            return state
        else:
            state["email_retry"] = state.get("email_retry", 0) + 1
            remaining = max_retries - state.get("email_retry")
            logger.warning(f"Invalid email attempt {state.get("email_retry")}: {email_result}")
            if remaining <= 0:
                state["workflow_complete"] =True
                state["error_message"] ="Too many invalid email attempts"
                state["response"] ="❌ Too many invalid attempts. Please click **New Conversation** to restart."
                return state
            state["response"] =(
                f"⚠️ {email_result}\n\n"
                f"Please enter a valid email address. ({remaining} attempt(s) left)"
            )
            return state

    # =========================================================================
    # FALLBACK — should never reach here
    # =========================================================================
    logger.error(f"Unknown collecting_step: {state.get("collecting_step")}")
    state["response"] ="⚠️ Something went wrong. Please click **New Conversation** to restart."
    state["workflow_complete"] =True
    return state