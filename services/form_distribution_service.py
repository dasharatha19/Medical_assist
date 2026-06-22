"""
Form Distribution Service Layer
Handles comprehensive form lifecycle management

Responsibilities:
- Generate unique form URLs with tokens
- Create forms for appointments
- Send forms to patients via email
- Track form delivery and completion
- Handle form data persistence
- Retry failed deliveries
- Generate form reminders
"""

import json
import logging
import os
import uuid
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)


class FormDistributionService:
    """Service for managing form distribution workflow"""

    def __init__(
        self,
        forms_filepath: str = "forms.json",
        delivery_log_filepath: str = "form_delivery_log.json",
    ):
        """
        Initialize form distribution service

        Args:
            forms_filepath: Path to forms.json storage file
            delivery_log_filepath: Path to delivery log file
        """
        self.forms_filepath = forms_filepath
        self.delivery_log_filepath = delivery_log_filepath
        self.forms = self._load_forms()
        self.delivery_log = self._load_delivery_log()
        logger.info("FormDistributionService initialized")

    # =========================================================================
    # FORM CREATION & URL GENERATION
    # =========================================================================

    def create_form_for_appointment(
        self,
        appointment_id: str,
        patient_id: str,
        patient_name: str,
        patient_email: str,
        doctor: str,
        appointment_date: str,
        is_new_patient: bool,
    ) -> dict:
        """
        Create a new form for an appointment with unique URL token

        Args:
            appointment_id: Unique appointment ID
            patient_id: Patient ID
            patient_name: Patient full name
            patient_email: Patient email
            doctor: Doctor name
            appointment_date: Appointment date (YYYY-MM-DD HH:MM)
            is_new_patient: True if new patient

        Returns:
            Dict with form creation result including form_url and form_token
        """
        try:
            # Check if form already exists
            if appointment_id in self.forms:
                logger.warning(f"Form already exists for appointment {appointment_id}")
                return {
                    "success": True,
                    "appointment_id": appointment_id,
                    "form_token": self.forms[appointment_id].get("form_token", ""),
                    "form_url": self.forms[appointment_id].get("form_url", ""),
                    "status": "already_created",
                }

            # Generate unique form token
            form_token = str(uuid.uuid4())

            # Determine form type
            form_type = "Comprehensive Intake Form" if is_new_patient else "Patient Update Form"

            # Create form structure
            form_data = {
                "form_token": form_token,
                "appointment_id": appointment_id,
                "patient_id": patient_id,
                "patient_name": patient_name,
                "patient_email": patient_email,
                "doctor": doctor,
                "appointment_date": appointment_date,
                "form_type": form_type,
                "is_new_patient": is_new_patient,
                "created_at": datetime.now().isoformat(),
                "form_url": self._generate_form_url(form_token),
                "fields": self._get_form_fields(is_new_patient),
                "status": {
                    "created": True,
                    "sent": False,
                    "sent_at": None,
                    "delivery_attempts": 0,
                    "completed": False,
                    "completed_at": None,
                    "completion_data": None,
                },
            }

            # Store form
            self.forms[appointment_id] = form_data
            self._save_forms()

            logger.info(
                f"Created form for appointment {appointment_id} with token {form_token[:8]}..."
            )

            return {
                "success": True,
                "appointment_id": appointment_id,
                "form_token": form_token,
                "form_url": form_data["form_url"],
                "form_type": form_type,
            }

        except Exception as e:
            logger.error(f"Error creating form: {str(e)}")
            return {"success": False, "error": f"Failed to create form: {str(e)}"}

    def _generate_form_url(self, form_token: str) -> str:
        """
        Generate unique form URL with token

        Args:
            form_token: Unique form token

        Returns:
            str: Complete form URL with token
        """
        base_url = os.getenv("FORM_BASE_URL", "https://forms.medical-scheduler.com")
        return f"{base_url}/patient-form/{form_token}"

    def _get_form_fields(self, is_new_patient: bool) -> list[dict]:
        """
        Get form fields based on patient type

        Args:
            is_new_patient: True if new patient

        Returns:
            List of form field definitions
        """
        common_fields = [
            {
                "name": "current_medications",
                "label": "Current Medications",
                "type": "textarea",
                "required": False,
            },
            {
                "name": "allergies",
                "label": "Known Allergies",
                "type": "textarea",
                "required": False,
            },
            {
                "name": "reason_for_visit",
                "label": "Reason for Visit",
                "type": "textarea",
                "required": True,
            },
        ]

        new_patient_fields = [
            {
                "name": "emergency_contact",
                "label": "Emergency Contact Name",
                "type": "text",
                "required": True,
            },
            {
                "name": "emergency_contact_phone",
                "label": "Emergency Contact Phone",
                "type": "text",
                "required": True,
            },
            {
                "name": "medical_history",
                "label": "Medical History (surgeries, hospitalizations, etc.)",
                "type": "textarea",
                "required": False,
            },
            {
                "name": "family_history",
                "label": "Family Medical History",
                "type": "textarea",
                "required": False,
            },
            {
                "name": "lifestyle",
                "label": "Lifestyle Information (smoking, alcohol, exercise)",
                "type": "textarea",
                "required": False,
            },
        ] + common_fields

        return new_patient_fields if is_new_patient else common_fields

    # =========================================================================
    # FORM DELIVERY
    # =========================================================================

    def send_form_email(
        self, appointment_id: str, patient_email: str, patient_name: str
    ) -> tuple[bool, str]:
        """
        Send form to patient via email

        Args:
            appointment_id: Appointment ID
            patient_email: Patient email address
            patient_name: Patient name

        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            form = self.forms.get(appointment_id)
            if not form:
                return False, f"Form not found for appointment {appointment_id}"

            # Import email service
            from services.email_service import get_email_service

            email_service = get_email_service()

            # Generate email content
            subject, body, html_body = self._generate_form_email(form, patient_name)

            # Send email
            success, message = email_service.send_email(patient_email, subject, body, html_body)

            # Update form status
            if success:
                self.forms[appointment_id]["status"]["sent"] = True
                self.forms[appointment_id]["status"]["sent_at"] = datetime.now().isoformat()
                self.forms[appointment_id]["status"]["delivery_attempts"] += 1
                self._save_forms()

                # Log delivery
                self._log_delivery(
                    appointment_id, patient_email, "sent", f"Form delivered to {patient_email}"
                )

                logger.info(f"Form sent successfully for appointment {appointment_id}")
            else:
                # Still update delivery attempt count
                self.forms[appointment_id]["status"]["delivery_attempts"] += 1
                self._save_forms()

                logger.warning(f"Failed to send form for appointment {appointment_id}: {message}")

            return success, message

        except Exception as e:
            logger.error(f"Error sending form: {str(e)}")
            return False, str(e)

    def _generate_form_email(self, form: dict, patient_name: str) -> tuple[str, str, str]:
        """
        Generate form email subject, plain text, and HTML content

        Args:
            form: Form data dictionary
            patient_name: Patient name

        Returns:
            Tuple[str, str, str]: (subject, body, html_body)
        """
        form_url = form["form_url"]
        appointment_date = form["appointment_date"]
        doctor = form["doctor"]
        form_type = form["form_type"]

        subject = f"Action Required: Complete Your {form_type}"

        body = f"""
Dear {patient_name},

Thank you for scheduling your appointment with us! To ensure we provide you with the best possible care, we need you to complete a form before your visit.

APPOINTMENT DETAILS:
- Date & Time: {appointment_date}
- Doctor: {doctor}
- Form Type: {form_type}

NEXT STEPS:
1. Click the link below to complete your form
2. Fill in all required information
3. Submit your form before your appointment

FORM LINK:
{form_url}

The form typically takes 5-10 minutes to complete. If you have any questions, please reply to this email.

Best regards,
Medical Appointment Scheduler
        """

        html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #2c3e50; color: white; padding: 20px; border-radius: 5px; }}
        .content {{ padding: 20px; background-color: #f9f9f9; margin-top: 20px; border-radius: 5px; }}
        .button {{ display: inline-block; background-color: #3498db; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
        .details {{ background-color: #ecf0f1; padding: 15px; border-left: 4px solid #3498db; margin: 15px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Complete Your Appointment Form</h1>
        </div>
        
        <div class="content">
            <p>Dear {patient_name},</p>
            
            <p>Thank you for scheduling your appointment with us! To ensure we provide you with the best possible care, we need you to complete a form before your visit.</p>
            
            <div class="details">
                <h3>📋 Appointment Details</h3>
                <p><strong>Date & Time:</strong> {appointment_date}</p>
                <p><strong>Doctor:</strong> {doctor}</p>
                <p><strong>Form Type:</strong> {form_type}</p>
            </div>
            
            <h3>📝 Next Steps</h3>
            <ol>
                <li>Click the button below to complete your form</li>
                <li>Fill in all required information (*)</li>
                <li>Submit your form before your appointment</li>
            </ol>
            
            <center>
                <a href="{form_url}" class="button">Complete Your Form</a>
            </center>
            
            <p><em>The form typically takes 5-10 minutes to complete. If you have any questions, please reply to this email.</em></p>
            
            <p>Best regards,<br>Medical Appointment Scheduler</p>
        </div>
    </div>
</body>
</html>
        """

        return subject, body, html_body

    # =========================================================================
    # FORM COMPLETION TRACKING
    # =========================================================================

    def mark_form_completed(
        self, appointment_id: str, form_data: dict | None = None
    ) -> tuple[bool, str]:
        """
        Mark form as completed and store submission data

        Args:
            appointment_id: Appointment ID
            form_data: Submitted form data (optional)

        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            form = self.forms.get(appointment_id)
            if not form:
                return False, f"Form not found for appointment {appointment_id}"

            completion_time = datetime.now().isoformat()

            self.forms[appointment_id]["status"]["completed"] = True
            self.forms[appointment_id]["status"]["completed_at"] = completion_time
            if form_data:
                self.forms[appointment_id]["status"]["completion_data"] = form_data

            self._save_forms()

            self._log_delivery(
                appointment_id,
                form["patient_email"],
                "completed",
                f"Form completed at {completion_time}",
            )

            logger.info(f"Form marked as completed for appointment {appointment_id}")
            return True, "Form completed successfully"

        except Exception as e:
            logger.error(f"Error marking form completed: {str(e)}")
            return False, str(e)

    def is_form_sent(self, appointment_id: str) -> bool:
        """Check if form has been sent"""
        form = self.forms.get(appointment_id)
        return form and form["status"]["sent"] if form else False

    def is_form_completed(self, appointment_id: str) -> bool:
        """Check if form has been completed"""
        form = self.forms.get(appointment_id)
        return form and form["status"]["completed"] if form else False

    def get_form_status(self, appointment_id: str) -> dict | None:
        """
        Get complete form status

        Args:
            appointment_id: Appointment ID

        Returns:
            Dict with form status or None if not found
        """
        form = self.forms.get(appointment_id)
        if not form:
            return None

        return {
            "appointment_id": appointment_id,
            "form_type": form["form_type"],
            "created_at": form["created_at"],
            "status": form["status"],
            "form_url": form["form_url"],
            "patient_email": form["patient_email"],
        }

    # =========================================================================
    # FOLLOW-UP REMINDERS
    # =========================================================================

    def get_pending_form_reminders(self, hours_since_sent: int = 24) -> list[dict]:
        """
        Get list of forms that should be reminded (sent but not completed)

        Args:
            hours_since_sent: Only remind if form was sent more than X hours ago

        Returns:
            List of forms needing reminders
        """
        pending_reminders = []
        now = datetime.now()
        cutoff_time = now - timedelta(hours=hours_since_sent)

        for appointment_id, form in self.forms.items():
            status = form.get("status", {})

            # Check if form was sent but not completed
            if status.get("sent") and not status.get("completed"):
                sent_at_str = status.get("sent_at")
                if sent_at_str:
                    sent_at = datetime.fromisoformat(sent_at_str)

                    # Check if enough time has passed
                    if sent_at <= cutoff_time:
                        pending_reminders.append(
                            {
                                "appointment_id": appointment_id,
                                "patient_email": form["patient_email"],
                                "patient_name": form["patient_name"],
                                "form_url": form["form_url"],
                                "form_type": form["form_type"],
                                "sent_at": sent_at_str,
                            }
                        )

        logger.info(f"Found {len(pending_reminders)} forms pending reminders")
        return pending_reminders

    def send_form_reminder(self, appointment_id: str) -> tuple[bool, str]:
        """
        Send reminder email to patient about incomplete form

        Args:
            appointment_id: Appointment ID

        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            form = self.forms.get(appointment_id)
            if not form:
                return False, f"Form not found for appointment {appointment_id}"

            from services.email_service import get_email_service

            email_service = get_email_service()

            # Generate reminder email
            subject, body, html_body = self._generate_form_reminder_email(form)

            # Send email
            success, message = email_service.send_email(
                form["patient_email"], subject, body, html_body
            )

            if success:
                self._log_delivery(
                    appointment_id,
                    form["patient_email"],
                    "reminder_sent",
                    f"Form reminder sent to {form['patient_email']}",
                )
                logger.info(f"Form reminder sent for appointment {appointment_id}")
            else:
                logger.warning(f"Failed to send form reminder: {message}")

            return success, message

        except Exception as e:
            logger.error(f"Error sending form reminder: {str(e)}")
            return False, str(e)

    def _generate_form_reminder_email(self, form: dict) -> tuple[str, str, str]:
        """Generate reminder email for incomplete form"""
        form_url = form["form_url"]
        patient_name = form["patient_name"]
        appointment_date = form["appointment_date"]

        subject = "Reminder: Please Complete Your Appointment Form"

        body = f"""
Hi {patient_name},

We noticed you haven't completed your appointment form yet. Your appointment is coming up on {appointment_date}, and we need your form to be submitted before then.

Please complete your form using the link below:
{form_url}

If you have any questions, please don't hesitate to reach out.

Thank you!
Medical Appointment Scheduler
        """

        html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #e74c3c; color: white; padding: 20px; border-radius: 5px; }}
        .content {{ padding: 20px; background-color: #f9f9f9; margin-top: 20px; border-radius: 5px; }}
        .button {{ display: inline-block; background-color: #e74c3c; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>⚠️ Form Reminder</h1>
        </div>
        
        <div class="content">
            <p>Hi {patient_name},</p>
            
            <p>We noticed you haven't completed your appointment form yet. Your appointment is coming up on <strong>{appointment_date}</strong>, and we need your form to be submitted before then.</p>
            
            <center>
                <a href="{form_url}" class="button">Complete Your Form Now</a>
            </center>
            
            <p>If you have any questions, please don't hesitate to reach out.</p>
            
            <p>Thank you!<br>Medical Appointment Scheduler</p>
        </div>
    </div>
</body>
</html>
        """

        return subject, body, html_body

    # =========================================================================
    # STORAGE & PERSISTENCE
    # =========================================================================

    def _load_forms(self) -> dict:
        """Load forms from JSON file"""
        try:
            if os.path.exists(self.forms_filepath):
                with open(self.forms_filepath) as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Error loading forms: {e}")

        return {}

    def _save_forms(self):
        """Save forms to JSON file"""
        try:
            # Create directory if needed
            Path(self.forms_filepath).parent.mkdir(parents=True, exist_ok=True)

            with open(self.forms_filepath, "w") as f:
                json.dump(self.forms, f, indent=2)
            logger.debug(f"Forms saved to {self.forms_filepath}")
        except Exception as e:
            logger.error(f"Error saving forms: {e}")

    def _load_delivery_log(self) -> dict:
        """Load delivery log from JSON file"""
        try:
            if os.path.exists(self.delivery_log_filepath):
                with open(self.delivery_log_filepath) as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Error loading delivery log: {e}")

        return {}

    def _save_delivery_log(self):
        """Save delivery log to JSON file"""
        try:
            Path(self.delivery_log_filepath).parent.mkdir(parents=True, exist_ok=True)

            with open(self.delivery_log_filepath, "w") as f:
                json.dump(self.delivery_log, f, indent=2)
            logger.debug(f"Delivery log saved to {self.delivery_log_filepath}")
        except Exception as e:
            logger.error(f"Error saving delivery log: {e}")

    def _log_delivery(self, appointment_id: str, email: str, event_type: str, message: str):
        """
        Log form delivery event

        Args:
            appointment_id: Appointment ID
            email: Patient email
            event_type: Type of event (sent, completed, failed, reminder_sent)
            message: Event message
        """
        if appointment_id not in self.delivery_log:
            self.delivery_log[appointment_id] = []

        self.delivery_log[appointment_id].append(
            {
                "timestamp": datetime.now().isoformat(),
                "email": email,
                "event_type": event_type,
                "message": message,
            }
        )

        self._save_delivery_log()

    def get_delivery_log(self, appointment_id: str) -> list[dict]:
        """
        Get delivery log for an appointment

        Args:
            appointment_id: Appointment ID

        Returns:
            List of delivery events
        """
        return self.delivery_log.get(appointment_id, [])


# Global service instance
_form_distribution_service: FormDistributionService | None = None


def get_form_distribution_service() -> FormDistributionService:
    """Get or create global form distribution service"""
    global _form_distribution_service
    if _form_distribution_service is None:
        _form_distribution_service = FormDistributionService()
    return _form_distribution_service
