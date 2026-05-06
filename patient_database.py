"""
Patient Database Module
Reads from data/patients.csv (50 synthetic patients)
New patients are registered in memory + appended to CSV
"""
import csv
import os
from datetime import datetime
from typing import Dict, Optional, Tuple


class PatientDatabase:

    def __init__(self, filepath: str = None):
        # Always point to data/patients.csv relative to project root
        if filepath is None:
            base = os.path.dirname(os.path.abspath(__file__))
            # Walk up until we find the data folder
            while not os.path.exists(os.path.join(base, "data")) and base != os.path.dirname(base):
                base = os.path.dirname(base)
            filepath = os.path.join(base, "data", "patients.csv")
        self.filepath = filepath
        self.patients = self._load_database()

    def _load_database(self) -> Dict:
        """Load patients from CSV into dict keyed by patient_id"""
        patients = {}
        if not os.path.exists(self.filepath):
            print(f"⚠️ patients.csv not found at {self.filepath}")
            return patients

        with open(self.filepath, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                pid = row['patient_id'].strip()
                patients[pid] = {
                    'name': f"{row['first_name'].strip()} {row['last_name'].strip()}",
                    'first_name': row['first_name'].strip(),
                    'last_name': row['last_name'].strip(),
                    'dob': row['dob'].strip(),
                    'phone': row['phone'].strip(),
                    'email': row['email'].strip(),
                    'insurance_carrier': row['insurance_carrier'].strip(),
                    'member_id': row['member_id'].strip(),
                    'group_id': row['group_id'].strip(),
                    'last_visit': row.get('last_visit', '').strip(),
                    'patient_type': row.get('patient_type', 'returning').strip(),
                    'appointments': [],
                    'is_new': False
                }
        print(f"✅ Loaded {len(patients)} patients from CSV")
        return patients

    def _save_database(self):
        """Append any new patients to CSV"""
        if not os.path.exists(self.filepath):
            return
        # Read existing IDs
        with open(self.filepath, newline='', encoding='utf-8') as f:
            existing_ids = {row['patient_id'] for row in csv.DictReader(f)}

        # Append new patients only
        new_patients = {
            pid: data for pid, data in self.patients.items()
            if pid not in existing_ids
        }
        if not new_patients:
            return

        with open(self.filepath, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'patient_id', 'first_name', 'last_name', 'dob',
                'phone', 'email', 'insurance_carrier', 'member_id',
                'group_id', 'last_visit', 'patient_type'
            ])
            for pid, data in new_patients.items():
                writer.writerow({
                    'patient_id': pid,
                    'first_name': data.get('first_name', ''),
                    'last_name': data.get('last_name', ''),
                    'dob': data.get('dob', ''),
                    'phone': data.get('phone', ''),
                    'email': data.get('email', ''),
                    'insurance_carrier': data.get('insurance_carrier', ''),
                    'member_id': data.get('member_id', ''),
                    'group_id': data.get('group_id', ''),
                    'last_visit': data.get('last_visit', ''),
                    'patient_type': 'new'
                })

    def check_patient_exists(self, patient_id: str) -> bool:
        return patient_id in self.patients

    def get_patient(self, patient_id: str) -> Optional[Dict]:
        return self.patients.get(patient_id)

    def search_patient_by_details(self, name: str, dob: str) -> Optional[Tuple[str, Dict]]:
        """Match by name (fuzzy) and DOB"""
        name_lower = name.lower().strip()
        for pid, data in self.patients.items():
            stored_name = data.get('name', '').lower().strip()
            stored_dob = data.get('dob', '').strip()
            # Match full name or partial (first or last)
            if stored_dob == dob and (
                stored_name == name_lower or
                name_lower in stored_name or
                stored_name in name_lower
            ):
                return pid, data
        return None

    def register_new_patient(self, name: str, dob: str, doctor: str, location: str) -> str:
        """Register new patient, assign ID, save to CSV"""
        patient_id = f"P{datetime.now().strftime('%Y%m%d%H%M%S')}"
        parts = name.strip().split(' ', 1)
        self.patients[patient_id] = {
            'name': name,
            'first_name': parts[0],
            'last_name': parts[1] if len(parts) > 1 else '',
            'dob': dob,
            'phone': '',
            'email': '',
            'insurance_carrier': '',
            'member_id': '',
            'group_id': '',
            'last_visit': '',
            'patient_type': 'new',
            'preferred_doctor': doctor,
            'location': location,
            'registration_date': datetime.now().isoformat(),
            'is_new': True,
            'appointments': []
        }
        self._save_database()
        return patient_id

    def add_appointment_to_patient(self, patient_id: str, appointment_data: Dict):
        if patient_id in self.patients:
            self.patients[patient_id]['appointments'].append(appointment_data)
            self.patients[patient_id]['is_new'] = False
            self._save_database()

    def is_new_patient(self, patient_id: str) -> bool:
        if patient_id in self.patients:
            return self.patients[patient_id].get('patient_type') == 'new'
        return True