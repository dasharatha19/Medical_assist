"""
Reminder Node
Books the appointment and sets up reminder notifications
Uses booking_tool and reminder_tool from tools layer

Enhanced with:
- State completeness validation before booking
- Comprehensive error handling
- Graceful failure recovery
- Tool error resilience
- Automated report generation for admin review
"""
from agents.state import SchedulerState
from tools import tools
from utils import (
    get_prompt_text,
    get_section,
    format_prompt,
    EdgeCaseValidator
)
from services import report_service


def reminder_node(state: SchedulerState) -> SchedulerState:
    """
    Reminder node - Book appointment and setup reminders
    
    Responsibilities:
    - Verify booking was confirmed
    - Validate all required state before booking
    - Call booking_tool to actually book the appointment
    - Handle booking errors gracefully
    - Setup reminder notifications
    - Provide confirmation details to patient
    
    IMPORTANT: This node only executes if booking_confirmed = True
    If booking fails, appointment is NOT booked
    
    Args:
        state: Current workflow state (must have booking_confirmed=True)
    
    Returns:
        Updated state with appointment ID and reminder status
    """
    
    # =========================================================================
    # SAFETY CHECK - Booking must be confirmed
    # =========================================================================
    if not state.get("booking_confirmed"):
        warning_msg = get_prompt_text('reminder_prompt', 'NOT_CONFIRMED')
        print(f"\n{warning_msg}")
        state["workflow_complete"] =True
        state["booking_success"] =False
        state["error_message"] ="Booking not confirmed"
        return state
    
    # =========================================================================
    # VALIDATE STATE COMPLETENESS BEFORE BOOKING
    # =========================================================================
    state_dict = {
        'patient_name': state.get("patient_name"),
        'patient_id': state.get("patient_id"),
        'patient_dob': state.get("patient_dob"),
        'patient_email': state.get("patient_email"),
        'patient_phone': state.get("patient_phone"),
        'preferred_doctor': state.get("preferred_doctor"),
        'appointment_date': state.get("appointment_date"),
        'selected_time': state.get("selected_time"),
    }
    
    is_complete, missing_fields = EdgeCaseValidator.check_appointment_completeness(state_dict)
    
    if not is_complete:
        # Cannot proceed - essential data missing
        incomplete_error = f"Cannot book: missing {', '.join(missing_fields)}"
        error_msg = get_prompt_text('reminder_prompt', 'BOOKING_ERROR')
        print(f"\n{format_prompt(error_msg, error_message=incomplete_error)}")
        state["workflow_complete"] =True
        state["booking_success"] =False
        state["error_message"] =incomplete_error
        return state
    
    # =========================================================================
    # BOOKING SETUP AND MESSAGE
    # =========================================================================
    
    # Load prompts from centralized prompts/ folder
    print(get_section('reminder_prompt', 'HEADER'))
    
    # Book the appointment using booking_tool
    booking_msg = get_prompt_text('reminder_prompt', 'BOOKING')
    print(booking_msg)
    
    # =========================================================================
    # CALL BOOKING TOOL - with error handling
    # =========================================================================
    try:
        booking_result = tools.booking.book(
            patient_id=state.get("patient_id"),
            doctor=state.get("preferred_doctor"),
            date=state.get("appointment_date"),
            time=state.get("selected_time"),
            duration=state.get("appointment_duration")
        )
    except Exception as e:
        # Tool error - booking failed
        tool_error_msg = get_prompt_text('reminder_prompt', 'BOOKING_ERROR')
        error_details = f"Booking service error: {str(e)}"
        print(f"\n{format_prompt(tool_error_msg, error_message=error_details)}")
        state["booking_success"] =False
        state["error_message"] =error_details
        state["workflow_complete"] =True
        return state
    
    # =========================================================================
    # HANDLE BOOKING RESULT
    # =========================================================================
    if not booking_result.get('success', False):
        # Booking tool returned error
        failed_msg = get_prompt_text('reminder_prompt', 'BOOKING_FAILED')
        error_details = booking_result.get('error', 'Unknown booking error')
        print(f"\n{format_prompt(failed_msg, error_message=error_details)}")
        state["booking_success"] =False
        state["error_message"] =error_details
        state["workflow_complete"] =True
        return state
    
    # BOOKING SUCCESSFUL
    success_msg = get_prompt_text('reminder_prompt', 'BOOKING_SUCCESS')
    print(success_msg)
    
    # Capture appointment ID (critical for reminders and confirmation)
    appointment_id = booking_result.get('appointment_id', "")
    if not appointment_id:
        # This shouldn't happen but handle gracefully
        id_error = "Booking succeeded but appointment ID not returned"
        error_msg = get_prompt_text('reminder_prompt', 'BOOKING_ERROR')
        print(f"\n{format_prompt(error_msg, error_message=id_error)}")
        state["booking_success"] =False
        state["error_message"] =id_error
        state["workflow_complete"] =True
        return state
    
    state["appointment_id"] =appointment_id
    state["booking_success"] =True
    
    # =========================================================================
    # GENERATE ADMIN REPORT - Append record to Excel workbook
    # =========================================================================
    # This occurs automatically after every confirmed booking
    # Report includes: patient info, appointment details, status, insurance
    try:
        report_service.record_appointment(state)
    except Exception as e:
        # Log error but don't block workflow - report is not critical to booking
        error_msg = get_prompt_text('reminder_prompt', 'BOOKING_ERROR')
        print(f"\n⚠️  Warning: Could not generate admin report: {str(e)}")
        print(f"   Report location: {report_service.get_report_location()}")
    
    # =========================================================================
    # SETUP REMINDERS - with error resilience
    # =========================================================================
    reminder_setup_msg = get_prompt_text('reminder_prompt', 'REMINDER_SETUP')
    print(f"\n{reminder_setup_msg}")
    
    try:
        reminder_result = tools.reminder.setup(
            patient_id=state.get("patient_id"),
            appointment_id=state.get("appointment_id"),
            appointment_date=state.get("appointment_date"),
            appointment_time=state.get("selected_time"),
            email=state.get("patient_email"),
            phone=state.get("patient_phone")
        )
    except Exception as e:
        # Reminder setup error (not critical - booking already succeeded)
        print(f"\n⚠️  Warning: Could not setup reminders: {str(e)}")
        print("   You will need to setup reminders manually in your account.")
        state["reminders_setup"] =False
        state["reminders_count"] =0
    
    if reminder_result and reminder_result.get('success', False):
        reminders_success_msg = get_prompt_text('reminder_prompt', 'REMINDERS_SUCCESS')
        print(reminders_success_msg)
        state["reminders_setup"] =True
        state["reminders_count"] =reminder_result.get('reminder_count', 0)
    elif reminder_result:
        reminders_info_msg = get_prompt_text('reminder_prompt', 'REMINDERS_INFO')
        reminder_msg = reminder_result.get('message', 'Check your account for reminder status')
        print(f"\n{format_prompt(reminders_info_msg, reminder_message=reminder_msg)}")
        state["reminders_setup"] =False
    
    # =========================================================================
    # DISPLAY FINAL APPOINTMENT CONFIRMATION
    # =========================================================================
    final_section = get_section('reminder_prompt', 'FINAL_CONFIRMATION')
    print(f"\n{final_section}")
    
    # Display all appointment details
    appointment_id_msg = get_prompt_text('reminder_prompt', 'APPOINTMENT_ID')
    print(format_prompt(appointment_id_msg, appointment_id=state.get("appointment_id")))
    
    doctor_msg = get_prompt_text('reminder_prompt', 'DOCTOR')
    print(format_prompt(doctor_msg, doctor_name=state.get("preferred_doctor")))
    
    date_msg = get_prompt_text('reminder_prompt', 'DATE')
    print(format_prompt(date_msg, appointment_date=state.get("appointment_date")))
    
    time_msg = get_prompt_text('reminder_prompt', 'TIME')
    print(format_prompt(time_msg, appointment_time=state.get("selected_time")))
    
    duration_msg = get_prompt_text('reminder_prompt', 'DURATION')
    print(format_prompt(duration_msg, duration_minutes=state.get("appointment_duration")))
    
    # Show insurance if available
    if state.get("insurance_carrier") and state.get("insurance_carrier") != "None":
        insurance_msg = get_prompt_text('reminder_prompt', 'INSURANCE')
        print(format_prompt(insurance_msg, insurance_carrier=state.get("insurance_carrier")))
    
    # Show reminder count
    reminders_msg = get_prompt_text('reminder_prompt', 'REMINDERS')
    reminder_count_display = state.get("reminders_count") if state.get("reminders_setup") else 0
    print(f"\n{format_prompt(reminders_msg, reminder_count=reminder_count_display)}")
    
    # Final thank you message
    thank_you_msg = get_prompt_text('reminder_prompt', 'THANK_YOU')
    print(f"\n{thank_you_msg}")
    print("=" * 70 + "\n")
    
    # =========================================================================
    # MARK WORKFLOW AS COMPLETE
    # =========================================================================
    state["workflow_complete"] =True
    
    return state
