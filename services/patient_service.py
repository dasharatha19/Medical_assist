"""
Patient Service Layer — PostgreSQL only.
Replaces patient_database.py dependency.
"""
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class PatientService:

    def lookup_patient(self, name: str, dob: str) -> dict:
        try:
            from database.db import lookup_patient, register_new_patient
            row = lookup_patient(name, dob)
            if row:
                ptype = row.get('patient_type', 'returning')
                return {
                    'found':            True,
                    'patient_id':       row['patient_id'],
                    'is_new':           ptype == 'new',
                    'status':           ptype,
                    'appointment_count': 0,
                    'duration_minutes': 60 if ptype == 'new' else 30
                }
            # Not found — register new
            pid = register_new_patient({'name': name, 'dob': dob})
            return {
                'found':            False,
                'patient_id':       pid,
                'is_new':           True,
                'status':           'new',
                'appointment_count': 0,
                'duration_minutes': 60
            }
        except Exception as e:
            logger.error(f"Patient lookup failed: {e}")
            return {
                'found':            False,
                'patient_id':       f"P{datetime.now().strftime('%Y%m%d%H%M%S')}",
                'is_new':           True,
                'status':           'new',
                'appointment_count': 0,
                'duration_minutes': 60
            }

    def update_patient_preferences(self, patient_id: str,
                                   doctor: str, location: str) -> bool:
        try:
            from database.db import get_connection
            conn = get_connection()
            cur  = conn.cursor()
            cur.execute("""
                UPDATE patients
                SET preferred_doctor=%s, location=%s
                WHERE patient_id=%s
            """, (doctor, location, patient_id))
            conn.commit()
            cur.close()
            conn.close()
            return True
        except Exception as e:
            logger.warning(f"Update preferences failed: {e}")
            return False

    def get_patient_info(self, patient_id: str) -> dict:
        try:
            from database.db import get_connection
            import psycopg2.extras
            conn = get_connection()
            cur  = conn.cursor(
                cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute(
                "SELECT * FROM patients WHERE patient_id=%s",
                (patient_id,))
            row = cur.fetchone()
            cur.close()
            conn.close()
            return dict(row) if row else None
        except Exception as e:
            logger.warning(f"Get patient failed: {e}")
            return None

    def record_appointment(self, patient_id: str,
                           appointment_data: dict) -> bool:
        try:
            from database.db import get_connection
            conn = get_connection()
            cur  = conn.cursor()
            cur.execute("""
                UPDATE patients
                SET patient_type='returning', last_visit=%s
                WHERE patient_id=%s
            """, (appointment_data.get('date', ''), patient_id))
            conn.commit()
            cur.close()
            conn.close()
            return True
        except Exception as e:
            logger.warning(f"Record appointment failed: {e}")
            return False


# Singleton
_patient_service = None

def get_patient_service():
    global _patient_service
    if _patient_service is None:
        _patient_service = PatientService()
    return _patient_service

# Module-level instance for direct import
patient_service = PatientService()