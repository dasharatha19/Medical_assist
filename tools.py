"""
Medical Appointment Scheduling Tools
5 core tools that implement the workflow steps
"""
import json
import os
import uuid
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Tuple


# ============================================================================
# TOOL 1: patient_lookup_tool
# ============================================================================
class PatientLookupTool:
    """Lookup patient status (new vs returning)"""
    
    def __init__(self, db_path: str = "patients.json"):
        self.db_path = db_path
        self.patients = self._load_db()
    
    def _load_db(self) -> Dict:
        if os.path.exists(self.db_path):
            with open(self.db_path, 'r') as f:
                return json.load(f)
        return {}
    
    def _save_db(self):
        with open(self.db_path, 'w') as f:
            json.dump(self.patients, f, indent=2)
    
    def lookup(self, name: str, dob: str) -> Dict:
        """
        Lookup patient by name and DOB
        Returns: {
            'found': bool,
            'patient_id': str,
            'is_new': bool,
            'status': 'new' or 'returning',
            'appointment_count': int,
            'duration_minutes': 60 or 30
        }
        """
        for patient_id, patient_data in self.patients.items():
            if (patient_data.get('name').lower() == name.lower() and 
                patient_data.get('dob') == dob):
                appointment_count = len(patient_data.get('appointments', []))
                return {
                    'found': True,
                    'patient_id': patient_id,
                    'is_new': appointment_count == 0,
                    'status': 'new' if appointment_count == 0 else 'returning',
                    'appointment_count': appointment_count,
                    'duration_minutes': 60 if appointment_count == 0 else 30
                }
        
        # Patient not found - register as new
        patient_id = f"P{datetime.now().strftime('%Y%m%d%H%M%S')}"
        self.patients[patient_id] = {
            'name': name,
            'dob': dob,
            'registration_date': datetime.now().isoformat(),
            'appointments': []
        }
        self._save_db()
        
        return {
            'found': False,
            'patient_id': patient_id,
            'is_new': True,
            'status': 'new',
            'appointment_count': 0,
            'duration_minutes': 60
        }
    
    def update_patient(self, patient_id: str, doctor: str, location: str):
        """Update patient with doctor and location preferences"""
        if patient_id in self.patients:
            self.patients[patient_id]['preferred_doctor'] = doctor
            self.patients[patient_id]['location'] = location
            self._save_db()


# ============================================================================
# TOOL 2: schedule_checker_tool
# ============================================================================
class ScheduleCheckerTool:
    """Check doctor availability and suggest slots"""
    
    def __init__(self, db_path: str = "doctors.json"):
        self.db_path = db_path
        self.doctors = self._load_db()
    
    def _load_db(self) -> Dict:
        if os.path.exists(self.db_path):
            with open(self.db_path, 'r') as f:
                return json.load(f)
        else:
            return self._create_sample_doctors()
    
    def _create_sample_doctors(self) -> Dict:
        doctors = {
            "Dr. John Smith": {
                "location": "Downtown Clinic",
                "specialization": "General Practice",
                "working_hours": {"start": "09:00", "end": "17:00"},
                "break_time": {"start": "12:00", "end": "13:00"},
                "appointments": []
            },
            "Dr. Sarah Johnson": {
                "location": "Westside Medical Center",
                "specialization": "Cardiology",
                "working_hours": {"start": "08:00", "end": "16:00"},
                "break_time": {"start": "12:00", "end": "13:00"},
                "appointments": []
            },
            "Dr. Michael Brown": {
                "location": "Downtown Clinic",
                "specialization": "Orthopedics",
                "working_hours": {"start": "10:00", "end": "18:00"},
                "break_time": {"start": "13:00", "end": "14:00"},
                "appointments": []
            }
        }
        self._save_db(doctors)
        return doctors
    
    def _save_db(self, doctors: Dict = None):
        with open(self.db_path, 'w') as f:
            json.dump(doctors or self.doctors, f, indent=2)
    
    def get_doctors(self) -> List[Dict]:
        """Get list of all available doctors"""
        result = []
        for doctor_name, info in self.doctors.items():
            result.append({
                'name': doctor_name,
                'specialization': info['specialization'],
                'location': info['location'],
                'hours': f"{info['working_hours']['start']} - {info['working_hours']['end']}"
            })
        return result
    
    def check_availability(self, doctor: str, date: str, duration: int) -> Dict:
        """
        Check available slots for doctor on given date
        Returns: {
            'available': bool,
            'doctor': str,
            'date': str,
            'slots': [str],
            'duration': int,
            'working_hours': str,
            'location': str
        }
        """
        if doctor not in self.doctors:
            return {
                'available': False,
                'error': f"Doctor '{doctor}' not found",
                'slots': []
            }
        
        doctor_info = self.doctors[doctor]
        available_slots = []
        
        try:
            start_time = datetime.strptime(doctor_info['working_hours']['start'], "%H:%M").time()
            end_time = datetime.strptime(doctor_info['working_hours']['end'], "%H:%M").time()
            break_start = datetime.strptime(doctor_info['break_time']['start'], "%H:%M").time()
            break_end = datetime.strptime(doctor_info['break_time']['end'], "%H:%M").time()
            
            apt_date = datetime.strptime(date, "%Y-%m-%d").date()
            current = datetime.combine(apt_date, start_time)
            end = datetime.combine(apt_date, end_time)
            
            while current < end:
                slot_time = current.time()
                slot_end = (current + timedelta(minutes=duration)).time()
                
                if not (slot_time >= break_start and slot_time < break_end):
                    if not (slot_end > break_start and slot_end <= break_end):
                        is_booked = any(
                            apt['datetime'].startswith(f"{date} {current.strftime('%H:%M')}")
                            for apt in doctor_info['appointments']
                        )
                        if not is_booked:
                            available_slots.append(current.strftime("%H:%M"))
                
                current += timedelta(minutes=30)
            
            return {
                'available': len(available_slots) > 0,
                'doctor': doctor,
                'date': date,
                'slots': available_slots,
                'duration': duration,
                'working_hours': f"{doctor_info['working_hours']['start']} - {doctor_info['working_hours']['end']}",
                'location': doctor_info['location']
            }
        
        except ValueError as e:
            return {
                'available': False,
                'error': f"Date format error: {str(e)}",
                'slots': []
            }


# ============================================================================
# TOOL 3: booking_tool
# ============================================================================
class BookingTool:
    """Book appointments (ONLY after confirmation)"""
    
    def __init__(self, patients_db: str = "patients.json", doctors_db: str = "doctors.json"):
        self.patients_db = patients_db
        self.doctors_db = doctors_db
        self.patients = self._load_patients()
        self.doctors = self._load_doctors()
    
    def _load_patients(self) -> Dict:
        if os.path.exists(self.patients_db):
            with open(self.patients_db, 'r') as f:
                return json.load(f)
        return {}
    
    def _load_doctors(self) -> Dict:
        if os.path.exists(self.doctors_db):
            with open(self.doctors_db, 'r') as f:
                return json.load(f)
        return {}
    
    def _save_patients(self):
        with open(self.patients_db, 'w') as f:
            json.dump(self.patients, f, indent=2)
    
    def _save_doctors(self):
        with open(self.doctors_db, 'w') as f:
            json.dump(self.doctors, f, indent=2)
    
    def book(self, patient_id: str, doctor: str, date: str, time: str, 
             duration: int) -> Dict:
        """
        Book appointment (ONLY AFTER CONFIRMATION)
        Returns: {
            'success': bool,
            'appointment_id': str,
            'error': str or None
        }
        """
        if doctor not in self.doctors:
            return {
                'success': False,
                'appointment_id': None,
                'error': f"Doctor'{doctor}' not found"
            }
        
        datetime_str = f"{date} {time}"
        for apt in self.doctors[doctor]['appointments']:
            if apt['datetime'] == datetime_str:
                return {
                    'success': False,
                    'appointment_id': None,
                    'error': f"Slot on {date} at {time} is no longer available"
                }
        
        appointment_id = str(uuid.uuid4())[:8].upper()
        
        self.doctors[doctor]['appointments'].append({
            'patient_id': patient_id,
            'datetime': datetime_str,
            'duration': duration,
            'appointment_id': appointment_id,
            'booked_at': datetime.now().isoformat()
        })
        
        self.patients[patient_id]['appointments'].append({
            'appointment_id': appointment_id,
            'doctor': doctor,
            'date': date,
            'time': time,
            'duration': duration,
            'booked_at': datetime.now().isoformat()
        })
        
        self._save_doctors()
        self._save_patients()
        
        return {
            'success': True,
            'appointment_id': appointment_id,
            'patient_id': patient_id,
            'doctor': doctor,
            'date': date,
            'time': time,
            'duration': duration
        }


# ============================================================================
# TOOL 4: notification_tool
# ============================================================================
class NotificationTool:
    """Send notifications (insurance, forms, confirmations)"""
    
    def __init__(self, insurance_db: str = "insurance.json", forms_db: str = "forms.json"):
        self.insurance_db = insurance_db
        self.forms_db = forms_db
        self.insurance = self._load_insurance()
        self.forms = self._load_forms()
        self.valid_carriers = [
            "Aetna", "Anthem", "Blue Cross Blue Shield", "Cigna", 
            "Humana", "UnitedHealthcare", "Medicaid", "Medicare", "Self-Pay"
        ]
    
    def _load_insurance(self) -> Dict:
        if os.path.exists(self.insurance_db):
            with open(self.insurance_db, 'r') as f:
                return json.load(f)
        return {}
    
    def _load_forms(self) -> Dict:
        if os.path.exists(self.forms_db):
            with open(self.forms_db, 'r') as f:
                return json.load(f)
        return {}
    
    def _save_insurance(self):
        with open(self.insurance_db, 'w') as f:
            json.dump(self.insurance, f, indent=2)
    
    def _save_forms(self):
        with open(self.forms_db, 'w') as f:
            json.dump(self.forms, f, indent=2)
    
    def validate_insurance(self, carrier: str, member_id: str, group_id: str) -> Dict:
        """Validate insurance details"""
        errors = []
        if carrier not in self.valid_carriers:
            errors.append(f"Carrier must be one of: {', '.join(self.valid_carriers)}")
        if len(member_id.strip()) < 3:
            errors.append("Member ID must be at least 3 characters")
        if len(group_id.strip()) < 2:
            errors.append("Group ID must be at least 2 characters")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'valid_carriers': self.valid_carriers
        }
    
    def collect_insurance(self, patient_id: str, carrier: str, 
                         member_id: str, group_id: str) -> Dict:
        """Collect and store insurance information"""
        validation = self.validate_insurance(carrier, member_id, group_id)
        
        if not validation['valid']:
            return {
                'success': False,
                'errors': validation['errors']
            }
        
        self.insurance[patient_id] = {
            'carrier': carrier,
            'member_id': member_id,
            'group_id': group_id,
            'collected_at': datetime.now().isoformat()
        }
        self._save_insurance()
        
        return {
            'success': True,
            'patient_id': patient_id,
            'carrier': carrier
        }
    
    def send_forms(self, appointment_id: str, patient_id: str, email: str, 
                   is_new_patient: bool) -> Dict:
        """Send forms AFTER appointment confirmation"""
        form_type = "Comprehensive Intake Form" if is_new_patient else "Patient Update Form"
        
        print(f"\n{'='*60}")
        print(f"FORMS SENT TO PATIENT")
        print(f"Type: {form_type}")
        print(f"Email: {email}")
        print(f"{'='*60}\n")
        
        self.forms[appointment_id] = {
            'patient_id': patient_id,
            'email': email,
            'form_type': form_type,
            'sent_at': datetime.now().isoformat()
        }
        self._save_forms()
        
        return {
            'success': True,
            'appointment_id': appointment_id,
            'form_type': form_type
        }


# ============================================================================
# TOOL 5: reminder_tool
# ============================================================================
class ReminderTool:
    """Setup and manage appointment reminders"""
    
    def __init__(self, db_path: str = "reminders.json"):
        self.db_path = db_path
        self.reminders = self._load_db()
    
    def _load_db(self) -> Dict:
        if os.path.exists(self.db_path):
            with open(self.db_path, 'r') as f:
                return json.load(f)
        return {}
    
    def _save_db(self):
        with open(self.db_path, 'w') as f:
            json.dump(self.reminders, f, indent=2)
    
    def setup(self, appointment_id: str, appointment_datetime: str, 
              email: str, phone: str) -> Dict:
        """
        Setup 3 reminders:
        1. Forms check (48h before)
        2. General reminder (24h before)
        3. Confirmation (1h before)
        """
        try:
            apt_dt = datetime.strptime(appointment_datetime, "%Y-%m-%d %H:%M")
            
            self.reminders[appointment_id] = {
                'appointment_datetime': appointment_datetime,
                'email': email,
                'phone': phone,
                'setup_at': datetime.now().isoformat(),
                'reminders': [
                    {
                        'id': f"{appointment_id}_R1",
                        'type': 'Forms Check',
                        'scheduled_time': (apt_dt - timedelta(hours=48)).isoformat(),
                        'sent': False
                    },
                    {
                        'id': f"{appointment_id}_R2",
                        'type': 'General Reminder',
                        'scheduled_time': (apt_dt - timedelta(hours=24)).isoformat(),
                        'sent': False
                    },
                    {
                        'id': f"{appointment_id}_R3",
                        'type': 'Confirmation',
                        'scheduled_time': (apt_dt - timedelta(hours=1)).isoformat(),
                        'sent': False
                    }
                ]
            }
            self._save_db()
            
            return {
                'success': True,
                'appointment_id': appointment_id,
                'reminders_count': 3
            }
        
        except ValueError as e:
            return {
                'success': False,
                'error': str(e)
            }


# ============================================================================
# Tool Registry
# ============================================================================
class ToolRegistry:
    """Central registry for all appointment scheduling tools"""
    
    def __init__(self):
        self.patient_lookup = PatientLookupTool()
        self.schedule_checker = ScheduleCheckerTool()
        self.booking = BookingTool()
        self.notification = NotificationTool()
        self.reminder = ReminderTool()


# Global tool registry
tools = ToolRegistry()