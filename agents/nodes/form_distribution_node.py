"""
Form Distribution Node
LangGraph node for handling form creation and distribution after appointment confirmation

Responsibilities:
- Create forms for confirmed appointments
- Generate unique form URLs
- Send forms to patient via email
- Track form delivery status
- Set up form completion tracking
"""

import logging

from agents.state import SchedulerState
from services.form_distribution_service import get_form_distribution_service

logger = logging.getLogger(__name__)


def form_distribution_node(state: SchedulerState) -> SchedulerState:
    """
    Form Distribution Node - Create and send forms after appointment booking

    Responsibilities:
    - Verify appointment was successfully booked
    - Create appropriate forms based on patient type (new vs returning)
    - Generate unique form URLs
    - Send forms to patient email
    - Track form delivery status
    - Handle errors gracefully

    IMPORTANT: This node executes AFTER reminder_node if booking successful

    Args:
        state: Current workflow state with appointment details

    Returns:
        Updated state with form distribution status
    """

    # =========================================================================
    # SAFETY CHECK - Appointment must be booked
    # =========================================================================
    if not state.get("booking_success") or not state.get("appointment_id"):
        warning_msg = "Form distribution skipped: Appointment not successfully booked"
        logger.warning(warning_msg)
        state["form_distribution_status"] = "skipped"
        state["error_message"] = warning_msg
        return state

    # =========================================================================
    # DETERMINE PATIENT TYPE (new vs returning)
    # =========================================================================
    # Use patient_type from state set during patient_lookup_node
    is_new_patient = state.get("patient_type").lower() == "new"
    state["is_new_patient"] = is_new_patient

    # =========================================================================
    # INITIALIZE FORM DISTRIBUTION SERVICE
    # =========================================================================
    try:
        form_service = get_form_distribution_service()
    except Exception as e:
        error_msg = f"Failed to initialize form service: {str(e)}"
        logger.error(error_msg)
        state["form_distribution_status"] = "failed"
        state["error_message"] = error_msg
        return state

    # =========================================================================
    # DISPLAY FORM DISTRIBUTION HEADER
    # =========================================================================
    print("\n" + "=" * 70)
    print(" " * 15 + "STEP 9: FORM DISTRIBUTION")
    print("=" * 70 + "\n")

    print("📋 Creating appointment forms...\n")

    # =========================================================================
    # CREATE FORMS
    # =========================================================================
    try:
        # Prepare form creation parameters
        appointment_datetime = (
            f"{state.get('appointment_date')} {state.get('selected_time')}"
        )

        form_result = form_service.create_form_for_appointment(
            appointment_id=state.get("appointment_id"),
            patient_id=state.get("patient_id"),
            patient_name=state.get("patient_name"),
            patient_email=state.get("patient_email"),
            doctor=state.get("preferred_doctor"),
            appointment_date=appointment_datetime,
            is_new_patient=is_new_patient,
        )

        if not form_result.get("success", False):
            error_msg = form_result.get("error", "Unknown error creating form")
            logger.error(f"Form creation failed: {error_msg}")
            state["form_distribution_status"] = "creation_failed"
            state["error_message"] = error_msg
            return state

        # Store form info in state with type-safe defaults
        state["form_created"] = True
        state["form_token"] = form_result.get("form_token", "")
        state["form_url"] = form_result.get("form_url", "")
        state["form_type"] = form_result.get("form_type", "")

        print("✓ Forms created successfully")
        print(f"  Form Type: {state.get('form_type')}")
        print(f"  Form Token: {state.get('form_token')[:8]}...")

    except Exception as e:
        error_msg = f"Error creating forms: {str(e)}"
        logger.error(error_msg)
        state["form_distribution_status"] = "creation_failed"
        state["error_message"] = error_msg
        return state

    # =========================================================================
    # SEND FORMS TO PATIENT
    # =========================================================================
    try:
        print(f"\n📧 Sending forms to patient ({state.get('patient_email')})...\n")

        success, message = form_service.send_form_email(
            appointment_id=state.get("appointment_id"),
            patient_email=state.get("patient_email"),
            patient_name=state.get("patient_name"),
        )

        if success:
            print(f"✓ Forms sent successfully to {state.get('patient_email')}")
            state["form_sent"] = True
            state["form_distribution_status"] = "sent"

            # Log delivery
            # logger.info(f"Form sent for appointment {state.get('appointment_id')}")
            logger.info(f"Form sent for appointment {state.get('appointment_id')}")
        else:
            # Form creation succeeded but delivery failed
            # This is not a critical failure - user can access form via URL
            print(f"⚠️  Warning: Could not send form email ({message})")
            # print(f"   Patient can access form at: {state.get("form_url")}")
            print(f"   Patient can access form at: {state.get('form_url')}")

            state["form_sent"] = False
            state["form_distribution_status"] = "creation_only"
            logger.warning(f"Form email delivery failed: {message}")

    except Exception as e:
        error_msg = f"Error sending forms: {str(e)}"
        logger.error(error_msg)
        state["form_distribution_status"] = "send_failed"
        # Don't fail workflow - form was created, just not delivered
        logger.warning(f"Form delivery error (non-critical): {error_msg}")

    # =========================================================================
    # DISPLAY FORM INFORMATION & NEXT STEPS
    # =========================================================================
    form_status = form_service.get_form_status(state.get("appointment_id"))

    if form_status:
        print(f"\n{'='*70}")
        print("USER INSTRUCTIONS - FORM COMPLETION")
        print(f"{'='*70}\n")

        print(f"📝 {state.get('form_type')}")
        print(
            f"   Status: {'✓ Sent to email' if state.get('form_sent') else '⚠️  Not emailed (access via URL)'}"
        )
        print(f"\n   Form URL: {state.get('form_url')}")

        # Show required fields
        fields = form_status.get("status", {}).get("fields", [])
        if fields:
            print("\n   Required Fields:")
            for field in fields:
                required = " *" if field.get("required") else ""
                print(f"   - {field.get('label')}{required}")

        print("\n   ⏰ Please complete this form before your appointment")
        # print(f"      ({state.get("appointment_date")} with {state.get("preferred_doctor")})")
        print(
            f"      ({state.get('appointment_date')} with {state.get('preferred_doctor')})"
        )

        print(f"\n{'='*70}\n")

    # =========================================================================
    # WORKFLOW COMPLETION
    # =========================================================================
    state["form_distribution_status"] = "completed"

    logger.info(
        f"Form distribution completed "
        f"(ID: {state.get('appointment_id')}, Token: {state.get('form_token')[:8]}...)"
    )

    return state
