"""
Insurance Module
Manages patient insurance information
"""
import json
import os
from typing import Dict, Optional

class InsuranceManager:
    """Handles insurance information collection and validation"""
    
    def __init__(self, filepath: str = "insurance.json"):
        self.filepath = filepath
        self.insurance_records = self._load_insurance()
        self.valid_carriers = [
            "Aetna",
            "Anthem",
            "Blue Cross Blue Shield",
            "Cigna",
            "Humana",
            "UnitedHealthcare",
            "Medicaid",
            "Medicare",
            "Self-Pay"
        ]
    
    def _load_insurance(self) -> Dict:
        """Load insurance records from JSON file"""
        if os.path.exists(self.filepath):
            with open(self.filepath, 'r') as f:
                return json.load(f)
        return {}
    
    def _save_insurance(self):
        """Save insurance records to JSON file"""
        with open(self.filepath, 'w') as f:
            json.dump(self.insurance_records, f, indent=2)
    
    def validate_insurance_details(self, carrier: str, member_id: str, 
                                  group_id: str) -> Dict[str, bool]:
        """Validate insurance details"""
        validation = {
            'carrier_valid': carrier in self.valid_carriers,
            'member_id_valid': len(member_id.strip()) >= 3,
            'group_id_valid': len(group_id.strip()) >= 2
        }
        return validation
    
    def add_insurance(self, patient_id: str, carrier: str, member_id: str, 
                     group_id: str) -> bool:
        """Add insurance information for a patient"""
        validation = self.validate_insurance_details(carrier, member_id, group_id)
        
        if not all(validation.values()):
            return False
        
        self.insurance_records[patient_id] = {
            'carrier': carrier,
            'member_id': member_id,
            'group_id': group_id,
            'added_date': str(os.path.getmtime(__file__))
        }
        
        self._save_insurance()
        return True
    
    def get_insurance(self, patient_id: str) -> Optional[Dict]:
        """Retrieve insurance information for a patient"""
        return self.insurance_records.get(patient_id)
    
    def update_insurance(self, patient_id: str, carrier: str, member_id: str, 
                        group_id: str) -> bool:
        """Update insurance information"""
        validation = self.validate_insurance_details(carrier, member_id, group_id)
        
        if not all(validation.values()):
            return False
        
        self.insurance_records[patient_id] = {
            'carrier': carrier,
            'member_id': member_id,
            'group_id': group_id,
            'added_date': self.insurance_records.get(patient_id, {}).get('added_date', '')
        }
        
        self._save_insurance()
        return True
    
    def get_valid_carriers(self) -> list:
        """Get list of valid insurance carriers"""
        return self.valid_carriers
