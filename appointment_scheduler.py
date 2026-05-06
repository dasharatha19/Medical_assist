"""
Medical Appointment Scheduling Assistant
Main orchestrator for the appointment booking workflow
"""
import uuid
from datetime import datetime
from patient_database import PatientDatabase
from doctor_availability import DoctorAvailability
from insurance_manager import InsuranceManager
from reminder_manager import ReminderManager
from form_manager import FormManager
from input_validator import InputValidator

class AppointmentScheduler:
    """Main appointment scheduling system"""
    
    def __init__(self):
        self.patient_db = PatientDatabase()
        self.doctor_availability = DoctorAvailability()
        self.insurance_manager = InsuranceManager()
        self.reminder_manager = ReminderManager()
        self.form_manager = FormManager()
        self.validator = InputValidator()
        self.current_appointment = {}
    
    def display_welcome(self):
        """Display welcome message"""
        print("\n" + "="*70)
        print(" "*15 + "MEDICAL APPOINTMENT SCHEDULING ASSISTANT")
        print("="*70)
        print("\nWelcome! I'm here to help you schedule a medical appointment.")
        print("Let's get started by collecting your information...\n")
    
    def step_1_collect_patient_details(self) -> str:
        """Step 1: Collect patient details"""
        print("\n" + "-"*70)
        print("STEP 1: PATIENT INFORMATION")
        print("-"*70)
        
        # Collect name
        while True:
            name = input("Please enter your full name: ").strip()
            valid, result = self.validator.validate_name(name)
            if valid:
                break
            print(f"❌ {result}")
        
        # Collect DOB
        while True:
            dob = input("Enter your date of birth (YYYY-MM-DD): ").strip()
            valid, result = self.validator.validate_dob(dob)
            if valid:
                break
            print(f"❌ {result}")
        
        # Collect doctor preference
        print("\nAvailable doctors:")
        doctors = self.doctor_availability.get_available_doctors()
        for i, doctor in enumerate(doctors, 1):
            doc_info = self.doctor_availability.get_doctor_info(doctor)
            print(f"  {i}. {doctor} - {doc_info['specialization']} @ {doc_info['location']}")
        
        while True:
            try:
                choice = int(input("Select doctor (number): "))
                if 1 <= choice <= len(doctors):
                    doctor = doctors[choice - 1]
                    break
                print("❌ Invalid selection")
            except ValueError:
                print("❌ Please enter a number")
        
        # Collect location
        doctor_info = self.doctor_availability.get_doctor_info(doctor)
        location = doctor_info['location']
        
        print(f"\nDoctor: {doctor}")
        print(f"Location: {location}")
        print(f"Name: {name}")
        print(f"DOB: {dob}")
        
        # Store in current appointment
        self.current_appointment['name'] = name
        self.current_appointment['dob'] = dob
        self.current_appointment['doctor'] = doctor
        self.current_appointment['location'] = location
        
        # Check if patient is new or returning
        result = self.patient_db.search_patient_by_details(name, dob)
        if result:
            patient_id, patient_data = result
            is_new = False
            print(f"\n✓ Welcome back! Patient ID: {patient_id}")
        else:
            patient_id = self.patient_db.register_new_patient(name, dob, doctor, location)
            is_new = True
            print(f"\n✓ New patient registered! Patient ID: {patient_id}")
        
        self.current_appointment['patient_id'] = patient_id
        self.current_appointment['is_new'] = is_new
        
        return patient_id
    
    def step_2_assign_appointment_duration(self) -> int:
        """Step 2: Assign appointment duration"""
        print("\n" + "-"*70)
        print("STEP 2: APPOINTMENT DURATION")
        print("-"*70)
        
        is_new = self.current_appointment['is_new']
        duration = 60 if is_new else 30
        
        print(f"You are a {'NEW' if is_new else 'RETURNING'} patient.")
        print(f"Appointment duration: {duration} minutes")
        
        self.current_appointment['duration'] = duration
        return duration
    
    def step_3_collect_contact_info(self):
        """Collect additional contact information"""
        print("\n" + "-"*70)
        print("STEP 3: CONTACT INFORMATION")
        print("-"*70)
        
        # Collect email
        while True:
            email = input("Enter your email address: ").strip()
            valid, result = self.validator.validate_email(email)
            if valid:
                break
            print(f"❌ {result}")
        
        # Collect phone
        while True:
            phone = input("Enter your phone number (10 digits): ").strip()
            valid, result = self.validator.validate_phone(phone)
            if valid:
                break
            print(f"❌ {result}")
        
        self.current_appointment['email'] = email
        self.current_appointment['phone'] = phone
        
        print(f"\n✓ Email: {email}")
        print(f"✓ Phone: {phone}")
    
    def step_4_check_doctor_availability(self):
        """Step 4: Check doctor availability"""
        print("\n" + "-"*70)
        print("STEP 4: CHECK DOCTOR AVAILABILITY")
        print("-"*70)
        
        # Collect preferred date
        while True:
            date = input("Enter preferred appointment date (YYYY-MM-DD): ").strip()
            valid, result = self.validator.validate_appointment_date(date)
            if valid:
                break
            print(f"❌ {result}")
        
        self.current_appointment['date'] = date
        
        # Get available slots
        doctor = self.current_appointment['doctor']
        duration = self.current_appointment['duration']
        
        available_slots = self.doctor_availability.get_available_slots(
            doctor, date, duration
        )
        
        if not available_slots:
            print(f"\n❌ No available slots on {date}")
            print("Please try another date.")
            self.step_4_check_doctor_availability()
            return
        
        print(f"\nAvailable slots on {date}:")
        for i, slot in enumerate(available_slots, 1):
            print(f"  {i}. {slot}")
        
        # Select time slot
        while True:
            try:
                choice = int(input("Select time slot (number): "))
                if 1 <= choice <= len(available_slots):
                    time = available_slots[choice - 1]
                    break
                print("❌ Invalid selection")
            except ValueError:
                print("❌ Please enter a number")
        
        self.current_appointment['time'] = time
        print(f"\n✓ Selected: {date} at {time}")
    
    def step_5_confirm_appointment(self) -> bool:
        """Step 5: Confirm appointment details"""
        print("\n" + "-"*70)
        print("STEP 5: APPOINTMENT CONFIRMATION")
        print("-"*70)
        
        print("\nPlease review your appointment details:")
        print(f"  Patient Name: {self.current_appointment['name']}")
        print(f"  Date of Birth: {self.current_appointment['dob']}")
        print(f"  Doctor: {self.current_appointment['doctor']}")
        print(f"  Location: {self.current_appointment['location']}")
        print(f"  Appointment Date: {self.current_appointment['date']}")
        print(f"  Appointment Time: {self.current_appointment['time']}")
        print(f"  Duration: {self.current_appointment['duration']} minutes")
        print(f"  Email: {self.current_appointment['email']}")
        print(f"  Phone: {self.current_appointment['phone']}")
        
        confirmed = self.validator.get_yes_no_input("\nDo you want to proceed with this appointment?")
        
        if not confirmed:
            print("\n❌ Appointment booking cancelled.")
            return False
        
        print("\n✓ Appointment confirmed!")
        return True
    
    def step_6_collect_insurance(self):
        """Step 6: Collect insurance details"""
        print("\n" + "-"*70)
        print("STEP 6: INSURANCE INFORMATION")
        print("-"*70)
        
        print("Valid insurance carriers:")
        carriers = self.insurance_manager.get_valid_carriers()
        for i, carrier in enumerate(carriers, 1):
            print(f"  {i}. {carrier}")
        
        # Collect carrier
        while True:
            carrier = input("Enter insurance carrier or number from list: ").strip()
            if carrier.isdigit():
                try:
                    idx = int(carrier) - 1
                    if 0 <= idx < len(carriers):
                        carrier = carriers[idx]
                except ValueError:
                    pass
            valid, result = self.insurance_manager.validate_insurance_details(
                carrier, "temp", "temp"
            )
            if valid:
                break
            print(f"❌ Invalid carrier")
        
        # Collect member ID
        while True:
            member_id = input("Enter member ID: ").strip()
            valid, result = self.validator.validate_member_id(member_id)
            if valid:
                break
            print(f"❌ {result}")
        
        # Collect group ID
        while True:
            group_id = input("Enter group ID: ").strip()
            valid, result = self.validator.validate_group_id(group_id)
            if valid:
                break
            print(f"❌ {result}")
        
        # Store insurance
        self.insurance_manager.add_insurance(
            self.current_appointment['patient_id'],
            carrier, member_id, group_id
        )
        
        print(f"\n✓ Insurance Information Saved:")
        print(f"  Carrier: {carrier}")
        print(f"  Member ID: {member_id}")
        print(f"  Group ID: {group_id}")
    
    def step_7_book_appointment(self) -> str:
        """Step 7: Book the appointment"""
        print("\n" + "-"*70)
        print("STEP 7: BOOKING APPOINTMENT")
        print("-"*70)
        
        doctor = self.current_appointment['doctor']
        date = self.current_appointment['date']
        time = self.current_appointment['time']
        patient_id = self.current_appointment['patient_id']
        duration = self.current_appointment['duration']
        
        # Book the slot
        if self.doctor_availability.book_slot(doctor, date, time, patient_id, duration):
            appointment_id = str(uuid.uuid4())[:8]
            
            # Store appointment
            appointment_data = {
                'appointment_id': appointment_id,
                'patient_id': patient_id,
                'doctor': doctor,
                'date': date,
                'time': time,
                'datetime': f"{date} {time}",
                'duration': duration,
                'booked_at': datetime.now().isoformat()
            }
            
            self.patient_db.add_appointment_to_patient(patient_id, appointment_data)
            self.current_appointment['appointment_id'] = appointment_id
            
            print(f"\n✓ APPOINTMENT BOOKED SUCCESSFULLY!")
            print(f"  Appointment ID: {appointment_id}")
            print(f"  Date & Time: {date} {time}")
            print(f"  Doctor: {doctor}")
            
            return appointment_id
        else:
            print("\n❌ Failed to book appointment. Slot may have been taken.")
            return None
    
    def step_8_send_forms(self, appointment_id: str):
        """Step 8: Send forms to patient"""
        print("\n" + "-"*70)
        print("STEP 8: SENDING FORMS")
        print("-"*70)
        
        patient_id = self.current_appointment['patient_id']
        email = self.current_appointment['email']
        is_new = self.current_appointment['is_new']
        
        # Create forms
        self.form_manager.create_form_for_appointment(
            appointment_id, patient_id, email, is_new
        )
        
        # Send forms
        if self.form_manager.send_forms(appointment_id, email):
            print(f"\n✓ Forms sent successfully to {email}")
    
    def step_9_setup_reminders(self, appointment_id: str):
        """Step 9: Setup appointment reminders"""
        print("\n" + "-"*70)
        print("STEP 9: SETTING UP REMINDERS")
        print("-"*70)
        
        datetime_str = f"{self.current_appointment['date']} {self.current_appointment['time']}"
        phone = self.current_appointment['phone']
        email = self.current_appointment['email']
        
        if self.reminder_manager.setup_reminders(appointment_id, datetime_str, phone, email):
            print("\n✓ Reminders set up:")
            print("  → Reminder 1 (48h before): Check if forms are filled")
            print("  → Reminder 2 (24h before): Basic appointment reminder")
            print("  → Reminder 3 (1h before): Ask confirmation/cancellation reason")
    
    def step_10_final_confirmation(self, appointment_id: str):
        """Step 10: Final confirmation"""
        print("\n" + "="*70)
        print("APPOINTMENT BOOKING COMPLETE!")
        print("="*70)
        
        print(f"\nYour appointment has been successfully scheduled!")
        print(f"\nAppointment Details:")
        print(f"  Appointment ID: {appointment_id}")
        print(f"  Patient Name: {self.current_appointment['name']}")
        print(f"  Doctor: {self.current_appointment['doctor']}")
        print(f"  Date: {self.current_appointment['date']}")
        print(f"  Time: {self.current_appointment['time']}")
        print(f"  Duration: {self.current_appointment['duration']} minutes")
        print(f"  Location: {self.current_appointment['location']}")
        
        print(f"\nWe have sent:")
        print(f"  ✓ Appointment confirmation to {self.current_appointment['email']}")
        print(f"  ✓ Patient forms to {self.current_appointment['email']}")
        
        print(f"\nYou will receive reminders:")
        print(f"  ✓ 48 hours before (forms check)")
        print(f"  ✓ 24 hours before (basic reminder)")
        print(f"  ✓ 1 hour before (confirmation)")
        
        print(f"\nThank you for scheduling with us!")
        print("="*70 + "\n")
    
    def run(self):
        """Run the complete appointment scheduling workflow"""
        try:
            self.display_welcome()
            
            # Step 1: Collect patient details
            patient_id = self.step_1_collect_patient_details()
            
            # Step 2: Assign appointment duration
            duration = self.step_2_assign_appointment_duration()
            
            # Step 3: Collect contact info
            self.step_3_collect_contact_info()
            
            # Step 4: Check doctor availability
            self.step_4_check_doctor_availability()
            
            # Step 5: Confirm appointment
            if not self.step_5_confirm_appointment():
                print("\nWould you like to start over?")
                if self.validator.get_yes_no_input(""):
                    self.current_appointment = {}
                    self.run()
                return
            
            # Step 6: Collect insurance
            self.step_6_collect_insurance()
            
            # Step 7: Book appointment
            appointment_id = self.step_7_book_appointment()
            if not appointment_id:
                print("\nPlease try again with a different date/time.")
                return
            
            # Step 8: Send forms (AFTER confirmation)
            self.step_8_send_forms(appointment_id)
            
            # Step 9: Setup reminders
            self.step_9_setup_reminders(appointment_id)
            
            # Step 10: Final confirmation
            self.step_10_final_confirmation(appointment_id)
            
        except KeyboardInterrupt:
            print("\n\nAppointment scheduling cancelled by user.")
        except Exception as e:
            print(f"\n❌ An error occurred: {str(e)}")
            raise


def main():
    """Main entry point"""
    scheduler = AppointmentScheduler()
    scheduler.run()


if __name__ == "__main__":
    main()
