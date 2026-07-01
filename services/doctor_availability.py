"""
Doctor Availability Module — fully DB-backed.
PostgreSQL is the single source of truth.
doctors.json is no longer needed.
"""

import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class DoctorAvailability:
    """Manages doctor schedules using PostgreSQL as sole source of truth."""

    def __init__(self, filepath: str = "doctors.json"):
        # filepath kept for signature compatibility but no longer used
        pass

    def _get_all_doctors_from_db(self) -> dict:
        """Fetch all doctors from PostgreSQL and return as name-keyed dict."""
        try:
            from database.db import get_all_doctors

            db_doctors = get_all_doctors()
            result = {}
            for d in db_doctors:
                wh = d.get("working_hours", "09:00 - 17:00")
                bt = d.get("break_time", "12:00 - 13:00")
                wh_parts = [x.strip() for x in wh.split("-")]
                bt_parts = [x.strip() for x in bt.split("-")]
                result[d["name"]] = {
                    "location": d.get("location", "Main Clinic"),
                    "specialization": d.get("specialization", "General"),
                    "conditions": d.get("conditions", ""),
                    "working_hours": {
                        "start": wh_parts[0] if len(wh_parts) > 0 else "09:00",
                        "end": wh_parts[1] if len(wh_parts) > 1 else "17:00",
                    },
                    "break_time": {
                        "start": bt_parts[0] if len(bt_parts) > 0 else "12:00",
                        "end": bt_parts[1] if len(bt_parts) > 1 else "13:00",
                    },
                }
            return result
        except Exception as e:
            logger.error(f"Failed to load doctors from DB: {e}")
            return {}

    def get_doctor_info(self, doctor_name: str) -> dict | None:
        doctors = self._get_all_doctors_from_db()
        return doctors.get(doctor_name)

    def get_available_doctors(self) -> list[str]:
        doctors = self._get_all_doctors_from_db()
        return list(doctors.keys())

    def validate_date(self, date_str: str) -> bool:
        try:
            return datetime.strptime(date_str, "%Y-%m-%d").date() >= datetime.now().date()
        except ValueError:
            return False

    def get_available_slots(self, doctor_name: str, date: str, duration: int) -> list[str]:
        """Get available slots using DB as source of truth."""
        doctors = self._get_all_doctors_from_db()
        if doctor_name not in doctors:
            logger.warning(f"Doctor not found in DB: {doctor_name}")
            return []

        doctor = doctors[doctor_name]

        # ── Load DB slots for this doctor+date ────────────────────────────────
        try:
            from database.db import get_available_slots as db_get_slots

            db_slots = set(db_get_slots(doctor_name, date))
        except Exception as e:
            logger.warning(f"DB slot fetch failed: {e}")
            db_slots = None

        # ── Load booked appointments for overlap check ─────────────────────────
        booked_appointments = self._get_db_booked_appointments(doctor_name, date)

        # ── Parse working hours ────────────────────────────────────────────────
        start_time = datetime.strptime(doctor["working_hours"]["start"], "%H:%M")
        end_time = datetime.strptime(doctor["working_hours"]["end"], "%H:%M")
        break_start = datetime.strptime(doctor["break_time"]["start"], "%H:%M")
        break_end = datetime.strptime(doctor["break_time"]["end"], "%H:%M")

        base_date = datetime.strptime(date, "%Y-%m-%d")
        start_dt = base_date.replace(hour=start_time.hour, minute=start_time.minute)
        end_dt = base_date.replace(hour=end_time.hour, minute=end_time.minute)
        break_s_dt = base_date.replace(hour=break_start.hour, minute=break_start.minute)
        break_e_dt = base_date.replace(hour=break_end.hour, minute=break_end.minute)

        available = []
        current = start_dt

        while current < end_dt:
            slot_str = current.strftime("%H:%M")
            slot_end = current + timedelta(minutes=duration)

            # Skip if DB says not available
            if db_slots is not None and slot_str not in db_slots:
                current += timedelta(minutes=30)
                continue

            # Skip break time
            if current >= break_s_dt and current < break_e_dt:
                current += timedelta(minutes=30)
                continue

            # Skip if slot runs into break
            if current < break_s_dt and slot_end > break_s_dt:
                current += timedelta(minutes=30)
                continue

            # Skip if slot runs past end of day
            if slot_end > end_dt:
                current += timedelta(minutes=30)
                continue

            # Skip if overlaps existing appointment
            if self._overlaps_existing(current, slot_end, booked_appointments, base_date):
                current += timedelta(minutes=30)
                continue

            available.append(slot_str)
            current += timedelta(minutes=30)

        return available

    def _get_db_booked_appointments(self, doctor_name: str, date: str) -> list[dict]:
        """Fetch booked appointments from DB for overlap checking."""
        try:
            import psycopg2.extras

            from database.db import get_connection

            conn = get_connection()
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute(
                """
                SELECT appointment_time, duration_minutes
                FROM appointments
                WHERE doctor_name = %s
                  AND appointment_date = %s
                  AND booking_success = TRUE
                  AND status != 'cancelled'
            """,
                (doctor_name, date),
            )
            rows = cur.fetchall()
            cur.close()
            conn.close()
            return [dict(r) for r in rows]
        except Exception as e:
            logger.warning(f"Could not fetch booked appointments: {e}")
            return []

    def _overlaps_existing(
        self, slot_start: datetime, slot_end: datetime, booked: list[dict], base_date: datetime
    ) -> bool:
        """Return True if proposed slot overlaps any existing booking."""
        for appt in booked:
            try:
                t = datetime.strptime(appt["appointment_time"], "%H:%M")
                a_start = base_date.replace(hour=t.hour, minute=t.minute)
                a_end = a_start + timedelta(minutes=appt.get("duration_minutes", 30))
                if slot_start < a_end and slot_end > a_start:
                    return True
            except Exception:
                continue
        return False

    def book_slot(
        self, doctor_name: str, date: str, time: str, patient_id: str, duration: int
    ) -> bool:
        """Book a slot — DB only, no json write."""
        doctors = self._get_all_doctors_from_db()
        if doctor_name not in doctors:
            return False

        # Re-verify slot is still free
        booked = self._get_db_booked_appointments(doctor_name, date)
        base = datetime.strptime(date, "%Y-%m-%d")
        t = datetime.strptime(time, "%H:%M")
        s_start = base.replace(hour=t.hour, minute=t.minute)
        s_end = s_start + timedelta(minutes=duration)

        if self._overlaps_existing(s_start, s_end, booked, base):
            logger.warning(f"Overlap detected: {doctor_name} {date} {time}")
            return False

        # Mark slot as booked in DB only
        try:
            from database.db import book_slot as db_book_slot

            db_book_slot(doctor_name, date, time)
            logger.info(f"Slot booked in DB: {doctor_name} {date} {time}")
            return True
        except Exception as e:
            logger.warning(f"DB slot booking failed: {e}")
            return False
