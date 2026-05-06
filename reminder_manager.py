"""
Reminder Module
Manages appointment reminders
"""
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional

class ReminderManager:
    """Manages appointment reminders"""
    
    def __init__(self, filepath: str = "reminders.json"):
        self.filepath = filepath
        self.reminders = self._load_reminders()
    
    def _load_reminders(self) -> Dict:
        """Load reminders from JSON file"""
        if os.path.exists(self.filepath):
            with open(self.filepath, 'r') as f:
                return json.load(f)
        return {}
    
    def _save_reminders(self):
        """Save reminders to JSON file"""
        with open(self.filepath, 'w') as f:
            json.dump(self.reminders, f, indent=2)
    
    def setup_reminders(self, appointment_id: str, appointment_datetime: str,
                       patient_phone: str, patient_email: str) -> bool:
        """
        Setup three reminders for an appointment:
        1. Basic reminder - 24 hours before
        2. Form reminder - 48 hours before
        3. Confirmation reminder - 1 hour before
        """
        try:
            apt_datetime = datetime.strptime(appointment_datetime, "%Y-%m-%d %H:%M")
            
            # Reminder 1: 48 hours before (ask if forms are filled)
            reminder_1_time = apt_datetime - timedelta(hours=48)
            
            # Reminder 2: 24 hours before (basic reminder)
            reminder_2_time = apt_datetime - timedelta(hours=24)
            
            # Reminder 3: 1 hour before (ask confirmation or cancellation reason)
            reminder_3_time = apt_datetime - timedelta(hours=1)
            
            self.reminders[appointment_id] = {
                'appointment_datetime': appointment_datetime,
                'patient_phone': patient_phone,
                'patient_email': patient_email,
                'reminders': [
                    {
                        'id': f"{appointment_id}_R1",
                        'type': 'Forms Check',
                        'message': 'Please confirm if you have filled out the appointment forms.',
                        'scheduled_time': reminder_1_time.isoformat(),
                        'sent': False
                    },
                    {
                        'id': f"{appointment_id}_R2",
                        'type': 'Basic Reminder',
                        'message': f'Reminder: You have an appointment tomorrow at {apt_datetime.strftime("%H:%M")}.',
                        'scheduled_time': reminder_2_time.isoformat(),
                        'sent': False
                    },
                    {
                        'id': f"{appointment_id}_R3",
                        'type': 'Confirmation',
                        'message': 'Your appointment is in 1 hour. Please confirm attendance or provide cancellation reason.',
                        'scheduled_time': reminder_3_time.isoformat(),
                        'sent': False
                    }
                ],
                'created_at': datetime.now().isoformat()
            }
            
            self._save_reminders()
            return True
        
        except ValueError:
            return False
    
    def get_pending_reminders(self) -> List[Dict]:
        """Get all pending reminders that should be sent now"""
        pending = []
        current_time = datetime.now()
        
        for appointment_id, reminder_data in self.reminders.items():
            for reminder in reminder_data.get('reminders', []):
                if not reminder['sent']:
                    reminder_time = datetime.fromisoformat(reminder['scheduled_time'])
                    if reminder_time <= current_time:
                        pending.append({
                            'appointment_id': appointment_id,
                            'reminder': reminder,
                            'contact': {
                                'phone': reminder_data['patient_phone'],
                                'email': reminder_data['patient_email']
                            }
                        })
        
        return pending
    
    def mark_reminder_sent(self, appointment_id: str, reminder_id: str) -> bool:
        """Mark a reminder as sent"""
        if appointment_id in self.reminders:
            for reminder in self.reminders[appointment_id]['reminders']:
                if reminder['id'] == reminder_id:
                    reminder['sent'] = True
                    reminder['sent_at'] = datetime.now().isoformat()
                    self._save_reminders()
                    return True
        return False
    
    def get_reminders_for_appointment(self, appointment_id: str) -> Optional[Dict]:
        """Get all reminders for a specific appointment"""
        return self.reminders.get(appointment_id)
    
    def simulate_send_reminder(self, contact: Dict, reminder: Dict) -> bool:
        """
        Simulate sending a reminder via email/SMS
        In production, this would integrate with email/SMS services
        """
        print(f"\n{'='*60}")
        print(f"REMINDER SENT TO PATIENT")
        print(f"{'='*60}")
        print(f"Type: {reminder['type']}")
        print(f"Message: {reminder['message']}")
        print(f"Email: {contact.get('email', 'N/A')}")
        print(f"Phone: {contact.get('phone', 'N/A')}")
        print(f"Sent at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}\n")
        return True
