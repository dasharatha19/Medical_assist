"""
LangChain-standard tools for MediBook agent.
Uses @tool decorator — the proper LangChain way.
"""
from langchain_core.tools import tool
from services import scheduling_service, patient_service


@tool
def get_available_doctors() -> list:
    """Get list of all available doctors with specialization and location."""
    return scheduling_service.get_available_doctors()


@tool
def check_doctor_availability(doctor: str, date: str, duration: int) -> dict:
    """
    Check available appointment slots for a doctor on a given date.
    Args:
        doctor: Doctor full name e.g. 'Dr. John Smith'
        date: Date in YYYY-MM-DD format
        duration: Appointment duration in minutes (30 or 60)
    """
    return scheduling_service.check_doctor_availability(doctor, date, duration)


@tool
def lookup_patient(name: str, dob: str) -> dict:
    """
    Look up patient in database by name and date of birth.
    Args:
        name: Patient full name
        dob: Date of birth in YYYY-MM-DD format
    """
    return patient_service.lookup_patient(name, dob)


@tool
def book_appointment(patient_id: str, doctor: str, date: str,
                     time: str, duration: int) -> dict:
    """
    Book an appointment slot after patient confirms.
    Args:
        patient_id: Patient ID from lookup
        doctor: Doctor full name
        date: Appointment date YYYY-MM-DD
        time: Appointment time HH:MM
        duration: Duration in minutes
    """
    from tools.booking_tool import booking_tool
    return booking_tool.book(patient_id, doctor, date, time, duration)


# Export all tools as a list for LangGraph agent
medibook_tools = [
    get_available_doctors,
    check_doctor_availability,
    lookup_patient,
    book_appointment,
]