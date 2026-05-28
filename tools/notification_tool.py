"""
Notification Tool — PostgreSQL only.
Removes form_manager and insurance_manager dependencies.
"""
import logging

logger = logging.getLogger(__name__)

VALID_CARRIERS = [
    "Aetna", "Anthem", "Blue Cross Blue Shield", "Cigna",
    "Humana", "UnitedHealthcare", "Medicaid", "Medicare", "Self-Pay"
]


class NotificationTool:

    def collect_insurance(self, patient_id: str, carrier: str,
                          member_id: str, group_id: str) -> dict:
        """Validate and save insurance to PostgreSQL."""
        # Validate
        errors = []
        if carrier not in VALID_CARRIERS:
            errors.append(f"Carrier must be one of: {', '.join(VALID_CARRIERS)}")
        if len(member_id.strip()) < 3:
            errors.append("Member ID must be at least 3 characters")
        if len(group_id.strip()) < 2:
            errors.append("Group ID must be at least 2 characters")

        if errors:
            return {'success': False, 'errors': errors}

        # Save to PostgreSQL
        try:
            from database.db import get_connection
            conn = get_connection()
            cur  = conn.cursor()
            cur.execute("""
                UPDATE patients
                SET insurance_carrier=%s, member_id=%s, group_id=%s
                WHERE patient_id=%s
            """, (carrier, member_id, group_id, patient_id))
            conn.commit()
            cur.close()
            conn.close()
            logger.info(f"Insurance saved for {patient_id}")
            return {
                'success':    True,
                'patient_id': patient_id,
                'carrier':    carrier
            }
        except Exception as e:
            logger.error(f"Insurance save failed: {e}")
            return {'success': False, 'errors': [str(e)]}

    def send_forms(self, appointment_id: str, patient_id: str,
                   email: str, is_new_patient: bool) -> dict:
        """Create and mark form as sent in PostgreSQL."""
        try:
            from database.db import save_form, update_form_sent
            import uuid

            form_token = str(uuid.uuid4())
            form_id    = f"FORM{uuid.uuid4().hex[:6].upper()}"
            form_type  = ("Comprehensive Intake Form"
                          if is_new_patient else "Patient Update Form")
            form_url   = (f"https://forms.medical-scheduler.com"
                          f"/patient-form/{form_token}")

            save_form({
                'form_id':        form_id,
                'appointment_id': appointment_id,
                'patient_id':     patient_id,
                'patient_email':  email,
                'form_type':      form_type,
                'form_token':     form_token,
                'form_url':       form_url,
                'is_new_patient': is_new_patient
            })
            update_form_sent(appointment_id)
            logger.info(f"Form created and sent: {form_url}")

            return {
                'success':        True,
                'appointment_id': appointment_id,
                'form_type':      form_type,
                'sent_to':        email,
                'form_url':       form_url
            }
        except Exception as e:
            logger.error(f"Form send failed: {e}")
            return {'success': False, 'error': str(e)}

    def get_valid_carriers(self) -> list:
        return VALID_CARRIERS


# Global tool instance
notification_tool = NotificationTool()