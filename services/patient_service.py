"""
Patient Service Layer
Encapsulates all patient-related business logic
Calls patient_database.py for data persistence
"""
from patient_database import PatientDatabase


class PatientService:
    """Service for patient operations"""
    
    def __init__(self):
        """Initialize patient service with database"""
        self.db = PatientDatabase()
    
    def lookup_patient(self, name: str, dob: str) -> dict:
        """
        Lookup patient by name and DOB
        
        Args:
            name: Patient full name
            dob: Date of birth (YYYY-MM-DD)
        
        Returns:
            dict: {
                'found': bool,
                'patient_id': str,
                'is_new': bool,
                'status': 'new' or 'returning',
                'appointment_count': int,
                'duration_minutes': 60 or 30
            }
        """
        result = self.db.search_patient_by_details(name, dob)
                
        if result:
                    patient_id, patient_data = result
                    appointment_count = len(patient_data.get('appointments', []))
                    patient_type = patient_data.get('patient_type', 'returning')

                    return {
                        'found': True,
                        'patient_id': patient_id,
                        'is_new': patient_type == 'new',
                        'status': patient_type,
                        'appointment_count': appointment_count,
                        'duration_minutes': 30 if patient_type == 'returning' else 60
                    }
        
        # Register as new patient
        patient_id = self.db.register_new_patient(name, dob, '', '')
        
        return {
            'found': False,
            'patient_id': patient_id,
            'is_new': True,
            'status': 'new',
            'appointment_count': 0,
            'duration_minutes': 60
        }
    
    def update_patient_preferences(self, patient_id: str, doctor: str, location: str) -> bool:
        """
        Update patient's preferred doctor and location
        
        Args:
            patient_id: Patient ID
            doctor: Preferred doctor name
            location: Preferred location
        
        Returns:
            bool: Success status
        """
        patient = self.db.get_patient(patient_id)
        if not patient:
            return False
        
        # Update in database
        self.db.patients[patient_id]['preferred_doctor'] = doctor
        self.db.patients[patient_id]['location'] = location
        self.db._save_database()
        return True
    
    def get_patient_info(self, patient_id: str) -> dict:
        """
        Retrieve complete patient information
        
        Args:
            patient_id: Patient ID
        
        Returns:
            dict: Patient data or None if not found
        """
        return self.db.get_patient(patient_id)
    
    def record_appointment(self, patient_id: str, appointment_data: dict) -> bool:
        """
        Record a new appointment for patient
        
        Args:
            patient_id: Patient ID
            appointment_data: Dictionary with appointment details
        
        Returns:
            bool: Success status
        """
        self.db.add_appointment_to_patient(patient_id, appointment_data)
        return True
