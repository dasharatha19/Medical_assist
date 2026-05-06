"""
Scheduling Service Layer
Encapsulates appointment scheduling business logic
Calls doctor_availability.py for availability checking
"""
from doctor_availability import DoctorAvailability
from datetime import datetime, timedelta


class SchedulingService:
    """Service for scheduling operations"""
    
    def __init__(self):
        """Initialize scheduling service with doctor availability"""
        self.doctor_avail = DoctorAvailability()
    
    def get_available_doctors(self) -> list:
        """
        Get list of all available doctors with full details
        
        Returns:
            list: List of doctor dicts with name, specialization, location, hours
        """
        doctors = []
        for doctor_name in self.doctor_avail.get_available_doctors():
            info = self.doctor_avail.get_doctor_info(doctor_name)
            doctors.append({
                'name': doctor_name,
                'specialization': info['specialization'],
                'location': info['location'],
                'hours': f"{info['working_hours']['start']} - {info['working_hours']['end']}"
            })
        return doctors
    
    def check_doctor_availability(self, doctor: str, date: str, duration: int) -> dict:
        """
        Check available time slots for a doctor on a given date
        Validates date is in future and finds all available slots
        
        Args:
            doctor: Doctor name
            date: Appointment date (YYYY-MM-DD)
            duration: Appointment duration in minutes (30 or 60)
        
        Returns:
            dict: {
                'available': bool,
                'doctor': str,
                'date': str,
                'slots': [str],  # Times like '09:00', '09:30', etc.
                'duration': int,
                'working_hours': str,
                'location': str,
                'error': str or None
            }
        """
        # Validate date is in future
        if not self.doctor_avail.validate_date(date):
            return {
                'available': False,
                'error': 'Date must be today or in the future',
                'slots': [],
                'doctor': doctor,
                'date': date
            }
        
        # Get available slots
        slots = self.doctor_avail.get_available_slots(doctor, date, duration)
        
        if not slots:
            return {
                'available': False,
                'error': f'No available slots on {date}',
                'slots': [],
                'doctor': doctor,
                'date': date
            }
        
        doctor_info = self.doctor_avail.get_doctor_info(doctor)
        
        return {
            'available': True,
            'doctor': doctor,
            'date': date,
            'slots': slots,
            'duration': duration,
            'working_hours': f"{doctor_info['working_hours']['start']} - {doctor_info['working_hours']['end']}",
            'location': doctor_info['location']
        }
    
    def reserve_slot(self, doctor: str, date: str, time: str, 
                    patient_id: str, duration: int) -> dict:
        """
        Reserve (book) an appointment slot with the doctor
        
        Args:
            doctor: Doctor name
            date: Appointment date (YYYY-MM-DD)
            time: Appointment time (HH:MM)
            patient_id: Patient ID
            duration: Appointment duration in minutes
        
        Returns:
            dict: {
                'success': bool,
                'doctor': str,
                'date': str,
                'time': str,
                'duration': int,
                'reserved_at': str,
                'error': str or None
            }
        """
        success = self.doctor_avail.book_slot(doctor, date, time, patient_id, duration)
        
        if not success:
            return {
                'success': False,
                'error': 'Slot is no longer available',
                'doctor': doctor,
                'date': date,
                'time': time
            }
        
        return {
            'success': True,
            'doctor': doctor,
            'date': date,
            'time': time,
            'duration': duration,
            'reserved_at': datetime.now().isoformat()
        }
