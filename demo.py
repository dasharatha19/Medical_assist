"""
Demo Script - Medical Appointment Scheduling Assistant
This script demonstrates all the features of the appointment scheduler
Run this to see how the system works without interactive prompts
"""

from patient_database import PatientDatabase
from doctor_availability import DoctorAvailability
from insurance_manager import InsuranceManager
from reminder_manager import ReminderManager
from form_manager import FormManager
from datetime import datetime, timedelta


def demo():
    """Run a demonstration of all system features"""
    
    print("="*70)
    print("MEDICAL APPOINTMENT SCHEDULING SYSTEM - FEATURE DEMO")
    print("="*70)
    
    # Initialize all modules
    patient_db = PatientDatabase()
    doctor_avail = DoctorAvailability()
    insurance_mgr = InsuranceManager()
    reminder_mgr = ReminderManager()
    form_mgr = FormManager()
    
    # ============================================================
    # DEMO 1: Patient Registration
    # ============================================================
    print("\n" + "-"*70)
    print("DEMO 1: PATIENT REGISTRATION")
    print("-"*70)
    
    patient_id = patient_db.register_new_patient(
        name="Jane Doe",
        dob="1985-03-20",
        doctor="Dr. John Smith",
        location="Downtown Clinic"
    )
    print(f"\n✓ New patient registered")
    print(f"  Patient ID: {patient_id}")
    print(f"  Name: Jane Doe")
    print(f"  DOB: 1985-03-20")
    print(f"  Is New Patient: {patient_db.is_new_patient(patient_id)}")
    
    # ============================================================
    # DEMO 2: Doctor Availability
    # ============================================================
    print("\n" + "-"*70)
    print("DEMO 2: DOCTOR AVAILABILITY")
    print("-"*70)
    
    doctors = doctor_avail.get_available_doctors()
    print(f"\n✓ Available Doctors ({len(doctors)}):")
    for doctor in doctors:
        info = doctor_avail.get_doctor_info(doctor)
        print(f"\n  Doctor: {doctor}")
        print(f"    Specialization: {info['specialization']}")
        print(f"    Location: {info['location']}")
        print(f"    Working Hours: {info['working_hours']['start']} - {info['working_hours']['end']}")
        print(f"    Break Time: {info['break_time']['start']} - {info['break_time']['end']}")
    
    # ============================================================
    # DEMO 3: Check Available Slots
    # ============================================================
    print("\n" + "-"*70)
    print("DEMO 3: AVAILABLE APPOINTMENT SLOTS")
    print("-"*70)
    
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    doctor = "Dr. John Smith"
    duration = 60  # New patient = 60 minutes
    
    slots = doctor_avail.get_available_slots(doctor, tomorrow, duration)
    print(f"\n✓ Available slots for {doctor} on {tomorrow}:")
    print(f"  (Appointment duration: {duration} minutes)")
    for i, slot in enumerate(slots[:5], 1):  # Show first 5
        print(f"  {i}. {slot}")
    if len(slots) > 5:
        print(f"  ... and {len(slots) - 5} more slots")
    
    # ============================================================
    # DEMO 4: Book Appointment
    # ============================================================
    print("\n" + "-"*70)
    print("DEMO 4: BOOKING APPOINTMENT")
    print("-"*70)
    
    selected_time = slots[0]
    booked = doctor_avail.book_slot(
        doctor, tomorrow, selected_time, patient_id, duration
    )
    print(f"\n✓ Appointment Booked!")
    print(f"  Doctor: {doctor}")
    print(f"  Date: {tomorrow}")
    print(f"  Time: {selected_time}")
    print(f"  Duration: {duration} minutes")
    
    # ============================================================
    # DEMO 5: Insurance Information
    # ============================================================
    print("\n" + "-"*70)
    print("DEMO 5: INSURANCE MANAGEMENT")
    print("-"*70)
    
    insurance_added = insurance_mgr.add_insurance(
        patient_id,
        carrier="Blue Cross Blue Shield",
        member_id="BC123456789",
        group_id="GRP001"
    )
    print(f"\n✓ Insurance Information Added")
    
    insurance_info = insurance_mgr.get_insurance(patient_id)
    print(f"  Carrier: {insurance_info['carrier']}")
    print(f"  Member ID: {insurance_info['member_id']}")
    print(f"  Group ID: {insurance_info['group_id']}")
    
    # ============================================================
    # DEMO 6: Form Management
    # ============================================================
    print("\n" + "-"*70)
    print("DEMO 6: FORM MANAGEMENT")
    print("-"*70)
    
    appointment_id = f"APT{datetime.now().strftime('%Y%m%d%H%M%S')}"
    form_created = form_mgr.create_form_for_appointment(
        appointment_id,
        patient_id,
        "jane.doe@email.com",
        is_new_patient=True
    )
    print(f"\n✓ Form Created for New Patient")
    
    form_info = form_mgr.get_form(appointment_id)
    print(f"  Form Type: {form_info['form_type']}")
    print(f"  Fields to Complete: {len(form_info['fields'])}")
    print(f"  Form URL: {form_info['form_url']}")
    
    # Send forms
    form_mgr.send_forms(appointment_id, "jane.doe@email.com")
    
    # ============================================================
    # DEMO 7: Reminder Setup
    # ============================================================
    print("\n" + "-"*70)
    print("DEMO 7: REMINDER MANAGEMENT")
    print("-"*70)
    
    appointment_datetime = f"{tomorrow} {selected_time}"
    reminders_setup = reminder_mgr.setup_reminders(
        appointment_id,
        appointment_datetime,
        "5551234567",
        "jane.doe@email.com"
    )
    print(f"\n✓ Reminders Set Up for {appointment_datetime}")
    
    reminder_data = reminder_mgr.get_reminders_for_appointment(appointment_id)
    for i, reminder in enumerate(reminder_data['reminders'], 1):
        print(f"\n  Reminder {i}: {reminder['type']}")
        print(f"    Message: {reminder['message']}")
        print(f"    Scheduled: {reminder['scheduled_time']}")
    
    # ============================================================
    # DEMO 8: Input Validation
    # ============================================================
    print("\n" + "-"*70)
    print("DEMO 8: INPUT VALIDATION EXAMPLES")
    print("-"*70)
    
    from input_validator import InputValidator
    
    validator = InputValidator()
    
    test_cases = [
        ("Name", validator.validate_name("John Smith")),
        ("DOB", validator.validate_dob("1990-05-15")),
        ("Email", validator.validate_email("john@example.com")),
        ("Phone", validator.validate_phone("5551234567")),
        ("Invalid Name", validator.validate_name("123")),
        ("Invalid Email", validator.validate_email("invalid-email")),
    ]
    
    print("\n✓ Validation Tests:")
    for test_name, (valid, result) in test_cases:
        status = "✓ PASS" if valid else "✗ FAIL"
        print(f"  {status}: {test_name} → {result}")
    
    # ============================================================
    # DEMO 9: Insurance Carriers
    # ============================================================
    print("\n" + "-"*70)
    print("DEMO 9: SUPPORTED INSURANCE CARRIERS")
    print("-"*70)
    
    carriers = insurance_mgr.get_valid_carriers()
    print(f"\n✓ Supported Carriers ({len(carriers)}):")
    for i, carrier in enumerate(carriers, 1):
        print(f"  {i}. {carrier}")
    
    # ============================================================
    # DEMO 10: Complete Workflow Summary
    # ============================================================
    print("\n" + "="*70)
    print("WORKFLOW SUMMARY")
    print("="*70)
    
    print(f"\n✓ Complete Appointment Booking Workflow Demonstrated:")
    print(f"  1. ✓ Patient registered: {patient_id}")
    print(f"  2. ✓ Appointment duration assigned: {duration} minutes")
    print(f"  3. ✓ Doctor availability checked")
    print(f"  4. ✓ Appointment slot selected: {selected_time}")
    print(f"  5. ✓ Appointment confirmed")
    print(f"  6. ✓ Insurance collected")
    print(f"  7. ✓ Appointment booked: {appointment_id}")
    print(f"  8. ✓ Forms sent to patient")
    print(f"  9. ✓ Reminders configured (3 reminders)")
    print(f"  10. ✓ Final confirmation displayed")
    
    print("\n" + "="*70)
    print("DEMO COMPLETE!")
    print("="*70)
    print("\nTo run the interactive scheduling assistant, execute:")
    print("  python appointment_scheduler.py")
    print("="*70 + "\n")


if __name__ == "__main__":
    try:
        demo()
    except Exception as e:
        print(f"\n❌ Error during demo: {str(e)}")
        import traceback
        traceback.print_exc()
