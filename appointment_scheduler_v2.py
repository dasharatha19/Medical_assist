"""
Refactored Appointment Scheduler Using Tool-Based Architecture
Follows strict workflow with tool invocations
"""
from tools import tools
from input_validator import InputValidator
from datetime import datetime


class AppointmentSchedulerV2:
    """Tool-based appointment scheduler"""
    
    def __init__(self):
        self.validator = InputValidator()
        self.appointment = {}
    
    def display_welcome(self):
        print("\n" + "="*70)
        print(" "*10 + "MEDICAL APPOINTMENT SCHEDULING SYSTEM")
        print("="*70 + "\n")
    
    def step_1_collect_patient_info(self) -> tuple[str, str]:
        """STEP 1: Collect patient information with clear, helpful prompts"""
        print("\n" + "-"*70)
        print("STEP 1: PATIENT INFORMATION")
        print("-"*70)
        print("Please provide the following details accurately.\n")
        
        # Collect Full Name - more polite and clear
        while True:
            print("→ What is your full name? (First Middle Last)")
            name = input("Full name: ").strip()
            valid, result = self.validator.validate_name(name)
            if valid:
                break
            print(f"❌ {result}")
        
        # Collect Date of Birth - much clearer guidance
        while True:
            print("\n→ What is your date of birth?")
            print("   Please enter in YYYY-MM-DD format (Example: 1995-03-22)")
            print("   This helps us identify your records and ensure correct age calculation.")
            dob = input("Date of birth (YYYY-MM-DD): ").strip()
            
            valid, result = self.validator.validate_dob(dob)
            if valid:
                            # Optional: Show calculated age for confirmation
                try:
                    birth_date = datetime.strptime(dob, "%Y-%m-%d")
                    age = (datetime.now().date() - birth_date.date()).days // 365
                    print(f"   → You will be approximately {age} years old.")
                    if not self.validator.get_yes_no_input("Is this correct?"):
                        continue  # ask DOB again
                except:
                    pass
                
                break
            print(f"❌ {result}")
            print("   Tip: Use four digits for year, e.g., 1990-12-05")
        
        # Show available doctors (this part can stay the same or be improved later)
        print("\nAvailable doctors:")
        doctors = tools.schedule_checker.get_doctors()
        for i, doc in enumerate(doctors, 1):
            print(f"  {i}. {doc['name']} - {doc['specialization']} @ {doc['location']}")
        
        # Select doctor
        while True:
            try:
                choice = int(input("\nSelect doctor (enter number): "))
                if 1 <= choice <= len(doctors):
                    doctor = doctors[choice - 1]['name']
                    location = doctors[choice - 1]['location']
                    break
                print("❌ Invalid selection. Please choose a number from the list.")
            except ValueError:
                print("❌ Please enter a valid number.")
        
        # Store in appointment dict
        self.appointment['name'] = name
        self.appointment['dob'] = dob
        self.appointment['doctor'] = doctor
        self.appointment['location'] = location
        
        return name, dob
    
    def step_2_patient_identification(self, name: str, dob: str) -> str:
        """STEP 2: Use patient_lookup_tool to identify patient"""
        print("\n" + "-"*70)
        print("STEP 2: PATIENT IDENTIFICATION")
        print("-"*70)
        
        # Call patient_lookup_tool
        result = tools.patient_lookup.lookup(name, dob)
        
        patient_id = result['patient_id']
        is_new = result['is_new']
        duration = result['duration_minutes']
        
        if result['found']:
            print(f"\n✓ Welcome back! Patient ID: {patient_id}")
            print(f"  Previous appointments: {result['appointment_count']}")
        else:
            print(f"\n✓ New patient registered! Patient ID: {patient_id}")
        
        print(f"  Appointment duration: {duration} minutes ({'NEW' if is_new else 'RETURNING'})")
        
        self.appointment['patient_id'] = patient_id
        self.appointment['is_new'] = is_new
        self.appointment['duration'] = duration
        
        return patient_id
    
    def step_3_collect_contact_info(self):
        """STEP 3: Collect contact information"""
        print("\n" + "-"*70)
        print("STEP 3: CONTACT INFORMATION")
        print("-"*70)
        
        # Email
        while True:
            email = input("Email: ").strip()
            valid, result = self.validator.validate_email(email)
            if valid:
                break
            print(f"❌ {result}")
        
        # Phone
        while True:
            phone = input("Phone (10 digits): ").strip()
            valid, result = self.validator.validate_phone(phone)
            if valid:
                break
            print(f"❌ {result}")
        
        self.appointment['email'] = email
        self.appointment['phone'] = phone
    
    def step_4_check_availability(self):
        """STEP 4: Use schedule_checker_tool to check availability"""
        print("\n" + "-"*70)
        print("STEP 4: CHECK DOCTOR AVAILABILITY")
        print("-"*70)
        
        # Get preferred date
        while True:
            date = input("Preferred date (YYYY-MM-DD): ").strip()
            valid, result = self.validator.validate_appointment_date(date)
            if valid:
                break
            print(f"❌ {result}")
        
        # Call schedule_checker_tool
        doctor = self.appointment['doctor']
        duration = self.appointment['duration']
        
        availability = tools.schedule_checker.check_availability(doctor, date, duration)
        
        if not availability['available']:
            print(f"\n❌ No slots available on {date}")
            print("Try another date.")
            self.step_4_check_availability()
            return
        
        # Show available slots
        slots = availability['slots']
        print(f"\nAvailable slots on {date}:")
        for i, slot in enumerate(slots, 1):
            print(f"  {i}. {slot}")
        
        # Select slot
        while True:
            try:
                choice = int(input("Select slot (number): "))
                if 1 <= choice <= len(slots):
                    time = slots[choice - 1]
                    break
                print("❌ Invalid selection")
            except ValueError:
                print("❌ Enter a number")
        
        self.appointment['date'] = date
        self.appointment['time'] = time
        print(f"\n✓ Selected: {date} at {time}")
    
    def step_5_confirm_before_booking(self) -> bool:
        """STEP 5: Confirm before booking"""
        print("\n" + "-"*70)
        print("STEP 5: APPOINTMENT CONFIRMATION")
        print("-"*70)
        
        print("\nDetails:")
        print(f"  Name: {self.appointment['name']}")
        print(f"  Doctor: {self.appointment['doctor']}")
        print(f"  Date: {self.appointment['date']}")
        print(f"  Time: {self.appointment['time']}")
        print(f"  Duration: {self.appointment['duration']} min")
        
        return self.validator.get_yes_no_input("\nConfirm booking?")
    
    def step_6_collect_insurance(self):
        """STEP 6: Collect insurance using notification_tool"""
        print("\n" + "-"*70)
        print("STEP 6: INSURANCE INFORMATION")
        print("-"*70)
        
        # Hardcoded or get from tool via method (recommended)
        valid_carriers = tools.notification.get_valid_carriers()  # ← Add this method to tool
        
        # If you don't want to add method yet, use this temporary list:
        # valid_carriers = ["Aetna", "Blue Cross Blue Shield", "Cigna", "UnitedHealthcare", 
        #                   "Humana", "Kaiser Permanente"]

        print("Carriers:")
        for i, carrier in enumerate(valid_carriers, 1):
            print(f"  {i}. {carrier}")
        
        # Rest of your code remains the same...
        while True:
            carrier_input = input("Carrier (name or number): ").strip()
            if carrier_input.isdigit():
                idx = int(carrier_input) - 1
                if 0 <= idx < len(valid_carriers):
                    carrier = valid_carriers[idx]
                else:
                    print("❌ Invalid number")
                    continue
            else:
                carrier = carrier_input
            
            member_id = input("Member ID: ").strip()
            group_id = input("Group ID: ").strip()
            
            result = tools.notification.collect_insurance(
                self.appointment['patient_id'], carrier, member_id, group_id
            )
            
            if result['success']:
                print(f"\n✓ Insurance saved: {result['carrier']}")
                break
            else:
                print(f"❌ {result['errors'][0]}")
    
    def step_7_book_appointment(self) -> str | None:
        """STEP 7: Use booking_tool to BOOK (ONLY after confirmation)"""
        print("\n" + "-"*70)
        print("STEP 7: BOOKING APPOINTMENT")
        print("-"*70)
        
        # Call booking_tool
        result = tools.booking.book(
            self.appointment['patient_id'],
            self.appointment['doctor'],
            self.appointment['date'],
            self.appointment['time'],
            self.appointment['duration']
        )
        
        if not result['success']:
                print(f"\n❌ Booking failed: {result['error']}")
                return None

        appointment_id = result['appointment_id']
        print(f"\n✓ APPOINTMENT BOOKED! ID: {appointment_id}")

            # ✅ NEW: Export to Excel for admin review (assignment requirement)
        try:
            from services.excel_exporter import export_appointment_to_excel
            excel_path = export_appointment_to_excel({
                    **self.appointment,
                    'appointment_id': appointment_id,
                })
            print(f"✓ Admin report saved: {excel_path}")
        except Exception as e:
                print(f"⚠️ Excel export failed: {e}")

        return appointment_id
    
    def step_8_send_forms(self, appointment_id: str):
        """STEP 8: Send forms AFTER confirmation using notification_tool"""
        print("\n" + "-"*70)
        print("STEP 8: SENDING FORMS")
        print("-"*70)
        
        # Call notification_tool to send forms
        result = tools.notification.send_forms(
            appointment_id,
            self.appointment['patient_id'],
            self.appointment['email'],
            self.appointment['is_new']
        )
        
        if result['success']:
            print(f"✓ {result['form_type']} sent to {self.appointment['email']}")
    
    def step_9_setup_reminders(self, appointment_id: str):
        """STEP 9: Setup 3 reminders using reminder_tool"""
        print("\n" + "-"*70)
        print("STEP 9: SETTING UP REMINDERS")
        print("-"*70)
        
        datetime_str = f"{self.appointment['date']} {self.appointment['time']}"
        
        # Call reminder_tool
        result = tools.reminder.setup(
            appointment_id,
            datetime_str,
            self.appointment['email'],
            self.appointment['phone']
        )
        
        if result['success']:
            print(f"\n✓ {result['reminders_count']} reminders scheduled:")
            print("  1. Forms check (48h before)")
            print("  2. General reminder (24h before)")
            print("  3. Confirmation request (1h before)")
    
    def step_10_final_confirmation(self, appointment_id: str):
        """STEP 10: Final confirmation"""
        print("\n" + "="*70)
        print("APPOINTMENT BOOKING COMPLETE!")
        print("="*70)
        
        print(f"\n✓ Appointment ID: {appointment_id}")
        print(f"✓ Doctor: {self.appointment['doctor']}")
        print(f"✓ Date: {self.appointment['date']} at {self.appointment['time']}")
        print(f"✓ Forms sent to {self.appointment['email']}")
        print(f"✓ 3 reminders scheduled")
        print("\n" + "="*70 + "\n")
    
    def run(self):
        """Execute complete workflow"""
        try:
            self.display_welcome()
            
            # STEP 1: Collect patient info
            name, dob = self.step_1_collect_patient_info()
            
            # STEP 2: Identify patient (new/returning, assign duration)
            patient_id = self.step_2_patient_identification(name, dob)
            
            # STEP 3: Collect contact
            self.step_3_collect_contact_info()
            
            # STEP 4: Check availability
            self.step_4_check_availability()
            
            # STEP 5: Confirm before booking
            if not self.step_5_confirm_before_booking():
                print("\n❌ Booking cancelled")
                return
            
            # STEP 6: Collect insurance
            self.step_6_collect_insurance()
            
            # STEP 7: Book appointment
            appointment_id = self.step_7_book_appointment()
            if not appointment_id:
                return
            
            # STEP 8: Send forms (AFTER booking confirmation)
            self.step_8_send_forms(appointment_id)
            
            # STEP 9: Setup reminders
            self.step_9_setup_reminders(appointment_id)
            
            # STEP 10: Final confirmation
            self.step_10_final_confirmation(appointment_id)
        
        except KeyboardInterrupt:
            print("\n\n❌ Booking cancelled by user")


def main():
    scheduler = AppointmentSchedulerV2()
    scheduler.run()


if __name__ == "__main__":
    main()