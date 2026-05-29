"""
Booking Tool
Simple wrapper that uses SchedulingService and PatientService
Provides: book appointment (ONLY after confirmation)
"""
import sys; sys.path.insert(0, '..')
import uuid
from datetime import datetime
from services import scheduling_service, patient_service


class BookingTool:
    """Tool for booking appointments"""
    
    def book(self, patient_id: str, doctor: str, date: str, 
             time: str, duration: int) -> dict:
        """
        Book an appointment (ONLY after confirmation)
        Calls:
        - SchedulingService.reserve_slot() to reserve with doctor
        - PatientService.record_appointment() to record in patient record
        
        Args:
            patient_id: Patient ID
            doctor: Doctor name
            date: Appointment date (YYYY-MM-DD)
            time: Appointment time (HH:MM)
            duration: Duration in minutes
        
        Returns:
            dict with booking result and appointment ID
        """
        # Reserve the slot
        reserve_result = scheduling_service.reserve_slot(
            doctor, date, time, patient_id, duration
        )
        
        if not reserve_result['success']:
            return {
                'success': False,
                'appointment_id': None,
                'error': reserve_result.get('error', 'Booking failed')
            }
        
        # Generate appointment ID
        appointment_id = str(uuid.uuid4())[:8].upper()
        
        # Record in patient's record
        appointment_data = {
            'appointment_id': appointment_id,
            'doctor': doctor,
            'date': date,
            'time': time,
            'duration': duration,
            'booked_at': datetime.now().isoformat()
        }
        
        patient_service.record_appointment(patient_id, appointment_data)
        
        return {
            'success': True,
            'appointment_id': appointment_id,
            'patient_id': patient_id,
            'doctor': doctor,
            'date': date,
            'time': time,
            'duration': duration
        }


# Global tool instance
booking_tool = BookingTool()
