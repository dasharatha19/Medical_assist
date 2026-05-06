"""
Reminder Service Layer
Encapsulates reminder business logic
Calls reminder_manager.py for reminder management
Supports form completion checking and form reminders
"""
from reminder_manager import ReminderManager
from datetime import datetime, timedelta
import logging


logger = logging.getLogger(__name__)


class ReminderService:
    """Service for reminder operations"""
    
    def __init__(self):
        """Initialize reminder service"""
        self.reminder_mgr = ReminderManager()
    
    def setup_appointment_reminders(self, appointment_id: str, appointment_datetime: str,
                                    email: str, phone: str) -> dict:
        """
        Setup 3-tier reminder system for appointment:
        1. Forms check - 48 hours before
        2. General reminder - 24 hours before
        3. Confirmation - 1 hour before
        
        Args:
            appointment_id: Unique appointment ID
            appointment_datetime: Appointment date/time (YYYY-MM-DD HH:MM)
            email: Patient email for notifications
            phone: Patient phone for notifications
        
        Returns:
            dict: {
                'success': bool,
                'appointment_id': str,
                'reminders_count': int,
                'reminder_schedule': [dict],
                'error': str or None
            }
        """
        try:
            apt_dt = datetime.strptime(appointment_datetime, "%Y-%m-%d %H:%M")
            
            # Validate appointment is in future
            if apt_dt <= datetime.now():
                return {
                    'success': False,
                    'error': 'Appointment must be in the future'
                }
            
            success = self.reminder_mgr.setup_reminders(
                appointment_id, appointment_datetime, email, phone
            )
            
            if not success:
                return {
                    'success': False,
                    'error': 'Failed to setup reminders'
                }
            
            return {
                'success': True,
                'appointment_id': appointment_id,
                'reminders_count': 3,
                'reminder_schedule': [
                    {
                        'position': 1,
                        'type': 'Forms Check',
                        'time_before': '48 hours',
                        'message': 'Please confirm if you have filled out appointment forms.'
                    },
                    {
                        'position': 2,
                        'type': 'General Reminder',
                        'time_before': '24 hours',
                        'message': f'Reminder: You have appointment tomorrow at {apt_dt.strftime("%H:%M")}.'
                    },
                    {
                        'position': 3,
                        'type': 'Confirmation',
                        'time_before': '1 hour',
                        'message': 'Your appointment is in 1 hour. Confirm attendance or provide cancellation reason.'
                    }
                ]
            }
        
        except ValueError as e:
            return {
                'success': False,
                'error': f'Invalid datetime format: {str(e)}'
            }
    
    def get_appointment_reminders(self, appointment_id: str) -> dict:
        """
        Get all reminders for an appointment
        
        Args:
            appointment_id: Appointment ID
        
        Returns:
            dict: Reminder data for appointment
        """
        return self.reminder_mgr.get_reminders_for_appointment(appointment_id)
    
    def mark_reminder_sent(self, appointment_id: str, reminder_id: str) -> bool:
        """
        Mark a reminder as sent
        
        Args:
            appointment_id: Appointment ID
            reminder_id: Reminder ID
        
        Returns:
            bool: Success status
        """
        return self.reminder_mgr.mark_reminder_sent(appointment_id, reminder_id)
    
    # =========================================================================
    # FORM COMPLETION CHECKING & REMINDERS
    # =========================================================================
    
    def check_form_completion(self, appointment_id: str) -> dict:
        """
        Check if forms have been completed for an appointment
        
        Args:
            appointment_id: Appointment ID
        
        Returns:
            dict: {
                'success': bool,
                'completed': bool,
                'form_type': str,
                'completed_at': str or None,
                'days_since_sent': int
            }
        """
        try:
            from services.form_distribution_service import get_form_distribution_service
            form_service = get_form_distribution_service()
            
            form_status = form_service.get_form_status(appointment_id)
            
            if not form_status:
                return {
                    'success': False,
                    'error': 'Form not found'
                }
            
            status = form_status.get('status', {})
            completed = status.get('completed', False)
            completed_at = status.get('completed_at')
            sent_at = status.get('sent_at')
            
            # Calculate days since sent
            days_since_sent = 0
            if sent_at:
                sent_time = datetime.fromisoformat(sent_at)
                days_since_sent = (datetime.now() - sent_time).days
            
            return {
                'success': True,
                'completed': completed,
                'form_type': form_status.get('form_type'),
                'completed_at': completed_at,
                'days_since_sent': days_since_sent,
                'sent_at': sent_at
            }
        
        except Exception as e:
            logger.error(f"Error checking form completion: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def send_form_reminder(self, appointment_id: str) -> dict:
        """
        Send reminder email for incomplete form
        
        Args:
            appointment_id: Appointment ID
        
        Returns:
            dict: {
                'success': bool,
                'message': str,
                'reminder_sent': bool
            }
        """
        try:
            from services.form_distribution_service import get_form_distribution_service
            form_service = get_form_distribution_service()
            
            # Check if form exists and is incomplete
            form_status = form_service.get_form_status(appointment_id)
            
            if not form_status:
                return {
                    'success': False,
                    'error': 'Form not found'
                }
            
            status = form_status.get('status', {})
            
            if status.get('completed'):
                return {
                    'success': True,
                    'message': 'Form already completed',
                    'reminder_sent': False
                }
            
            if not status.get('sent'):
                return {
                    'success': True,
                    'message': 'Form not yet sent',
                    'reminder_sent': False
                }
            
            # Send reminder
            success, message = form_service.send_form_reminder(appointment_id)
            
            return {
                'success': success,
                'message': message,
                'reminder_sent': success
            }
        
        except Exception as e:
            logger.error(f"Error sending form reminder: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'reminder_sent': False
            }
    
    def get_pending_form_reminders(self, hours_since_sent: int = 24) -> dict:
        """
        Get list of forms that need reminders
        
        Args:
            hours_since_sent: Only remind if form was sent more than X hours ago
        
        Returns:
            dict: {
                'success': bool,
                'pending_reminders': [dict],
                'count': int
            }
        """
        try:
            from services.form_distribution_service import get_form_distribution_service
            form_service = get_form_distribution_service()
            
            pending = form_service.get_pending_form_reminders(hours_since_sent)
            
            return {
                'success': True,
                'pending_reminders': pending,
                'count': len(pending)
            }
        
        except Exception as e:
            logger.error(f"Error getting pending form reminders: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'pending_reminders': [],
                'count': 0
            }
