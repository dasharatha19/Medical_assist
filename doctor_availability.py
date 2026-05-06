"""
Doctor Availability Module
Manages doctor schedules and available appointment slots
"""
import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional

class DoctorAvailability:
    """Manages doctor schedules and availability"""
    
    def __init__(self, filepath: str = "doctors.json"):
        self.filepath = filepath
        self.doctors = self._load_doctors()
    
    def _load_doctors(self) -> Dict:
        """Load doctor data from JSON file"""
        if os.path.exists(self.filepath):
            with open(self.filepath, 'r') as f:
                return json.load(f)
        else:
            # Initialize with sample doctors
            return self._create_sample_doctors()
    
    def _create_sample_doctors(self) -> Dict:
        """Create sample doctor data"""
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
        self._save_doctors(doctors)
        return doctors
    
    def _save_doctors(self, doctors: Dict):
        """Save doctor data to JSON file"""
        with open(self.filepath, 'w') as f:
            json.dump(doctors, f, indent=2)
    
    def get_doctor_info(self, doctor_name: str) -> Optional[Dict]:
        """Get doctor information"""
        return self.doctors.get(doctor_name)
    
    def get_available_doctors(self) -> List[str]:
        """Get list of all available doctors"""
        return list(self.doctors.keys())
    
    def get_available_slots(self, doctor_name: str, date: str, 
                          duration: int) -> List[str]:
        """
        Get available appointment slots for a doctor on a given date
        duration: appointment duration in minutes (30 or 60)
        """
        if doctor_name not in self.doctors:
            return []
        
        doctor = self.doctors[doctor_name]
        available_slots = []
        
        # Parse time strings
        start_time = datetime.strptime(doctor['working_hours']['start'], "%H:%M").time()
        end_time = datetime.strptime(doctor['working_hours']['end'], "%H:%M").time()
        break_start = datetime.strptime(doctor['break_time']['start'], "%H:%M").time()
        break_end = datetime.strptime(doctor['break_time']['end'], "%H:%M").time()
        
        # Generate slots
        current = datetime.combine(datetime.strptime(date, "%Y-%m-%d").date(), start_time)
        end = datetime.combine(datetime.strptime(date, "%Y-%m-%d").date(), end_time)
        
        while current < end:
            slot_time = current.time()
            slot_end_time = (current + timedelta(minutes=duration)).time()
            
            # Skip break time
            if not (slot_time >= break_start and slot_time < break_end):
                # Check if slot doesn't overlap with break
                slot_end_datetime = current + timedelta(minutes=duration)
                if slot_end_datetime.time() <= break_start or current.time() >= break_end:
                    if not self._is_slot_booked(doctor_name, current.strftime("%Y-%m-%d %H:%M")):
                        available_slots.append(current.strftime("%H:%M"))
            
            current += timedelta(minutes=30)  # 30-minute intervals
        
        return available_slots
    
    def _is_slot_booked(self, doctor_name: str, datetime_str: str) -> bool:
        """Check if a slot is already booked"""
        if doctor_name not in self.doctors:
            return False
        
        doctor = self.doctors[doctor_name]
        for appointment in doctor['appointments']:
            if appointment.get('datetime', "") == datetime_str:
                return True
        
        return False
    
    def book_slot(self, doctor_name: str, date: str, time: str, 
                 patient_id: str, duration: int) -> bool:
        """Book an appointment slot"""
        if doctor_name not in self.doctors:
            return False
        
        datetime_str = f"{date} {time}"
        
        if self._is_slot_booked(doctor_name, datetime_str):
            return False
        
        self.doctors[doctor_name]['appointments'].append({
            'patient_id': patient_id,
            'datetime': datetime_str,
            'duration': duration,
            'booked_at': datetime.now().isoformat()
        })
        
        self._save_doctors(self.doctors)
        return True
    
    def validate_date(self, date_str: str) -> bool:
        """Validate if date is in future and is a valid format"""
        try:
            appointment_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            if appointment_date >= datetime.now().date():
                return True
            return False
        except ValueError:
            return False
