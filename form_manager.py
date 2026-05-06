"""
Form Management Module
Handles patient intake forms and form sending
"""
import json
import os
from datetime import datetime
from typing import Dict, Optional

class FormManager:
    """Manages patient intake forms"""
    
    def __init__(self, filepath: str = "forms.json"):
        self.filepath = filepath
        self.forms = self._load_forms()
    
    def _load_forms(self) -> Dict:
        """Load forms data from JSON file"""
        if os.path.exists(self.filepath):
            with open(self.filepath, 'r') as f:
                return json.load(f)
        return {}
    
    def _save_forms(self):
        """Save forms data to JSON file"""
        with open(self.filepath, 'w') as f:
            json.dump(self.forms, f, indent=2)
    
    def create_form_for_appointment(self, appointment_id: str, patient_id: str,
                                   patient_email: str, is_new_patient: bool) -> bool:
        """
        Create forms for an appointment
        New patients get comprehensive intake form
        Returning patients get brief update form
        """
        form_type = "Comprehensive Intake Form" if is_new_patient else "Patient Update Form"
        
        self.forms[appointment_id] = {
            'patient_id': patient_id,
            'patient_email': patient_email,
            'appointment_id': appointment_id,
            'form_type': form_type,
            'created_at': datetime.now().isoformat(),
            'sent': False,
            'sent_at': None,
            'completed': False,
            'completed_at': None,
            'form_url': f"https://forms.example.com/form/{appointment_id}",
            'fields': self._get_form_fields(is_new_patient)
        }
        
        self._save_forms()
        return True
    
    def _get_form_fields(self, is_new_patient: bool) -> list:
        """Get form fields based on patient type"""
        common_fields = [
            {'name': 'current_medications', 'label': 'Current Medications', 'type': 'text'},
            {'name': 'allergies', 'label': 'Known Allergies', 'type': 'text'},
            {'name': 'reason_for_visit', 'label': 'Reason for Visit', 'type': 'textarea'},
        ]
        
        new_patient_fields = [
            {'name': 'emergency_contact', 'label': 'Emergency Contact', 'type': 'text'},
            {'name': 'medical_history', 'label': 'Medical History', 'type': 'textarea'},
            {'name': 'family_history', 'label': 'Family History', 'type': 'textarea'},
            {'name': 'lifestyle', 'label': 'Lifestyle (smoking, alcohol, etc.)', 'type': 'textarea'},
        ] + common_fields
        
        return new_patient_fields if is_new_patient else common_fields
    
    def send_forms(self, appointment_id: str, patient_email: str) -> bool:
        """
        Send forms to patient email
        In production, this would integrate with email service
        """
        if appointment_id not in self.forms:
            return False
        
        form = self.forms[appointment_id]
        
        # Simulate sending email
        print(f"\n{'='*60}")
        print(f"FORMS SENT TO PATIENT")
        print(f"{'='*60}")
        print(f"Form Type: {form['form_type']}")
        print(f"Recipient Email: {patient_email}")
        print(f"Form URL: {form['form_url']}")
        print(f"Sent at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Fields to complete: {len(form['fields'])}")
        for field in form['fields']:
            print(f"  - {field['label']}")
        print(f"{'='*60}\n")
        
        self.forms[appointment_id]['sent'] = True
        self.forms[appointment_id]['sent_at'] = datetime.now().isoformat()
        self._save_forms()
        
        return True
    
    def get_form(self, appointment_id: str) -> Optional[Dict]:
        """Get form information"""
        return self.forms.get(appointment_id)
    
    def mark_form_completed(self, appointment_id: str) -> bool:
        """Mark form as completed"""
        if appointment_id in self.forms:
            self.forms[appointment_id]['completed'] = True
            self.forms[appointment_id]['completed_at'] = datetime.now().isoformat()
            self._save_forms()
            return True
        return False
    
    def is_form_sent(self, appointment_id: str) -> bool:
        """Check if form has been sent"""
        form = self.forms.get(appointment_id)
        return form['sent'] if form else False
    
    def is_form_completed(self, appointment_id: str) -> bool:
        """Check if form has been completed"""
        form = self.forms.get(appointment_id)
        return form['completed'] if form else False
