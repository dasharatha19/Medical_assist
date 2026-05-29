"""
Patient Lookup Tool
Simple wrapper that uses PatientService
Provides: lookup by name/DOB, update preferences
"""
import sys; sys.path.insert(0, '..')
from services import patient_service


class PatientLookupTool:
    """Tool for patient lookup operations"""
    
    def lookup(self, name: str, dob: str) -> dict:
        """
        Lookup patient by name and DOB
        Calls PatientService.lookup_patient()
        
        Args:
            name: Patient full name
            dob: Date of birth (YYYY-MM-DD)
        
        Returns:
            dict with patient info and status
        """
        return patient_service.lookup_patient(name, dob)
    
    def update_preferences(self, patient_id: str, doctor: str, location: str) -> bool:
        """
        Update patient's preferred doctor and location
        Calls PatientService.update_patient_preferences()
        
        Args:
            patient_id: Patient ID
            doctor: Preferred doctor name
            location: Preferred location
        
        Returns:
            bool: Success status
        """
        return patient_service.update_patient_preferences(patient_id, doctor, location)


# Global tool instance
patient_lookup_tool = PatientLookupTool()
