"""
Reminder Tool
Simple wrapper that uses ReminderService
Provides: setup reminders, get reminders
"""

import sys

sys.path.insert(0, "..")
from services import reminder_service


class ReminderTool:
    """Tool for appointment reminders"""

    def setup(
        self, appointment_id: str, appointment_datetime: str, email: str, phone: str
    ) -> dict:
        """
        Setup 3-tier reminder system (AFTER booking confirmation)
        Calls ReminderService.setup_appointment_reminders()

        Args:
            appointment_id: Appointment ID
            appointment_datetime: Appointment date/time (YYYY-MM-DD HH:MM)
            email: Patient email
            phone: Patient phone

        Returns:
            dict with reminder setup result
        """
        return reminder_service.setup_appointment_reminders(
            appointment_id, appointment_datetime, email, phone
        )

    def get_reminders(self, appointment_id: str) -> dict:
        """
        Get all reminders for an appointment
        Calls ReminderService.get_appointment_reminders()

        Args:
            appointment_id: Appointment ID

        Returns:
            dict: Reminder data for appointment
        """
        return reminder_service.get_appointment_reminders(appointment_id)

    def mark_sent(self, appointment_id: str, reminder_id: str) -> bool:
        """
        Mark a reminder as sent
        Calls ReminderService.mark_reminder_sent()

        Args:
            appointment_id: Appointment ID
            reminder_id: Reminder ID

        Returns:
            bool: Success status
        """
        return reminder_service.mark_reminder_sent(appointment_id, reminder_id)


# Global tool instance
reminder_tool = ReminderTool()
