"""
Notification Tool
Simple wrapper that uses insurance and form managers
Provides: collect insurance, send forms
"""
import sys; sys.path.insert(0, '..')
from insurance_manager import InsuranceManager
from form_manager import FormManager


class NotificationTool:
    """Tool for patient notifications"""
    
    def __init__(self):
        self.insurance_mgr = InsuranceManager()
        self.form_mgr = FormManager()
    
    def collect_insurance(self, patient_id: str, carrier: str, 
                         member_id: str, group_id: str) -> dict:
        """
        Collect and validate insurance information
        Calls InsuranceManager.add_insurance()
        
        Args:
            patient_id: Patient ID
            carrier: Insurance carrier name
            member_id: Insurance member ID
            group_id: Insurance group ID
        
        Returns:
            dict with collection result
        """
        # Validate
        validation = self.insurance_mgr.validate_insurance_details(
            carrier, member_id, group_id
        )
        
        if not all(validation.values()):
            return {
                'success': False,
                'errors': ['Invalid insurance details']
            }
        
        # Add to database
        success = self.insurance_mgr.add_insurance(
            patient_id, carrier, member_id, group_id
        )
        
        if not success:
            return {
                'success': False,
                'errors': ['Failed to save insurance']
            }
        
        return {
            'success': True,
            'patient_id': patient_id,
            'carrier': carrier
        }
    
    def send_forms(self, appointment_id: str, patient_id: str, 
                   email: str, is_new_patient: bool) -> dict:
        """
        Send appointment forms to patient (AFTER booking confirmation)
        Calls FormManager.send_forms()
        
        Args:
            appointment_id: Appointment ID
            patient_id: Patient ID
            email: Patient email
            is_new_patient: Whether patient is new
        
        Returns:
            dict with form sending result
        """
        # Create forms
        self.form_mgr.create_form_for_appointment(
            appointment_id, patient_id, email, is_new_patient
        )
        
        # Send forms
        success = self.form_mgr.send_forms(appointment_id, email)
        
        if not success:
            return {
                'success': False,
                'error': 'Failed to send forms'
            }
        
        form = self.form_mgr.get_form(appointment_id)
        
        return {
            'success': True,
            'appointment_id': appointment_id,
            'form_type': form['form_type'],
            'sent_to': email
        }
    
    def get_valid_carriers(self) -> list:
        """
        Get list of valid insurance carriers
        
        Returns:
            list of carrier names
        """
        return self.insurance_mgr.get_valid_carriers()


# Global tool instance
notification_tool = NotificationTool()
