"""
Reminder Service Layer — PostgreSQL only.
Replaces reminder_manager.py dependency.
"""

import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class ReminderService:
    def setup_appointment_reminders(
        self, appointment_id: str, appointment_datetime: str, email: str, phone: str
    ) -> dict:
        try:
            apt_dt = datetime.strptime(appointment_datetime, "%Y-%m-%d %H:%M")

            reminders = [
                {
                    "reminder_id": f"{appointment_id}_R1",
                    "reminder_type": "Forms Check",
                    "scheduled_time": (apt_dt - timedelta(hours=48)).isoformat(),
                },
                {
                    "reminder_id": f"{appointment_id}_R2",
                    "reminder_type": "General Reminder",
                    "scheduled_time": (apt_dt - timedelta(hours=24)).isoformat(),
                },
                {
                    "reminder_id": f"{appointment_id}_R3",
                    "reminder_type": "Confirmation",
                    "scheduled_time": (apt_dt - timedelta(hours=1)).isoformat(),
                },
            ]

            from database.db import save_reminders

            save_reminders(appointment_id, email or "", phone or "", reminders)

            logger.info(f"3 reminders saved to DB: {appointment_id}")

            return {
                "success": True,
                "appointment_id": appointment_id,
                "reminders_count": 3,
                "reminder_schedule": [
                    {
                        "position": 1,
                        "type": "Forms Check",
                        "time_before": "48 hours",
                        "message": "Please confirm if you " "have filled your forms.",
                    },
                    {
                        "position": 2,
                        "type": "General Reminder",
                        "time_before": "24 hours",
                        "message": f"Appointment tomorrow " f"at " f'{apt_dt.strftime("%H:%M")}.',
                    },
                    {
                        "position": 3,
                        "type": "Confirmation",
                        "time_before": "1 hour",
                        "message": "Your appointment is in " "1 hour. Confirm or cancel.",
                    },
                ],
            }

        except Exception as e:
            logger.error(f"Reminder setup failed: {e}")
            return {"success": False, "error": str(e)}

    def get_appointment_reminders(self, appointment_id: str) -> dict:
        try:
            from database.db import get_reminders

            rows = get_reminders(appointment_id)
            return {"appointment_id": appointment_id, "reminders": rows}
        except Exception as e:
            logger.warning(f"Get reminders failed: {e}")
            return {"appointment_id": appointment_id, "reminders": []}

    def mark_reminder_sent(self, appointment_id: str, reminder_id: str) -> bool:
        try:
            from database.db import get_connection

            conn = get_connection()
            cur = conn.cursor()
            cur.execute(
                """
                UPDATE reminders
                SET sent=TRUE, sent_at=NOW()
                WHERE reminder_id=%s
            """,
                (reminder_id,),
            )
            conn.commit()
            cur.close()
            conn.close()
            return True
        except Exception as e:
            logger.warning(f"Mark reminder sent failed: {e}")
            return False

    def check_form_completion(self, appointment_id: str) -> dict:
        try:
            from database.db import get_form

            form = get_form(appointment_id)
            if not form:
                return {"success": False, "error": "Form not found"}
            return {
                "success": True,
                "completed": form.get("completed", False),
                "form_type": form.get("form_type"),
                "completed_at": str(form.get("completed_at", "")),
                "sent_at": str(form.get("sent_at", "")),
            }
        except Exception as e:
            logger.error(f"Form check failed: {e}")
            return {"success": False, "error": str(e)}

    def send_form_reminder(self, appointment_id: str) -> dict:
        try:
            from database.db import get_form

            form = get_form(appointment_id)
            if not form:
                return {"success": False, "error": "Form not found"}
            if form.get("completed"):
                return {
                    "success": True,
                    "message": "Already completed",
                    "reminder_sent": False,
                }
            # Mock send
            logger.info(f"Form reminder sent for {appointment_id}")
            return {"success": True, "message": "Reminder sent", "reminder_sent": True}
        except Exception as e:
            logger.error(f"Form reminder failed: {e}")
            return {"success": False, "error": str(e), "reminder_sent": False}


# Module-level instance for direct import
reminder_service = ReminderService()
