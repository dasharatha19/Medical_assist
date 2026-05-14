"""
Doctor Availability Module — DB-backed version.
Uses PostgreSQL doctor_slots as single source of truth.
Drops doctors.json dependency for availability/booking.
"""
import json
import os
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class DoctorAvailability:
    """Manages doctor schedules using DB as source of truth."""

    def __init__(self, filepath: str = "doctors.json"):
        self.filepath = filepath
        self.doctors = self._load_doctors()

    def _load_doctors(self) -> Dict:
        if os.path.exists(self.filepath):
            with open(self.filepath, 'r') as f:
                return json.load(f)
        return self._create_sample_doctors()

    def _create_sample_doctors(self) -> Dict:
        doctors = {
            "Dr. John Smith": {
                "location": "Downtown Clinic",
                "specialization": "General Practice",
                "working_hours": {"start": "09:00", "end": "17:00"},
                "break_time": {"start": "12:00", "end": "13:00"},
                "appointments": []
            },
            "Dr. Sarah Johnson": {
                "location": "Westside Medical Center",
                "specialization": "Cardiology",
                "working_hours": {"start": "08:00", "end": "16:00"},
                "break_time": {"start": "12:00", "end": "13:00"},
                "appointments": []
            },
            "Dr. Michael Brown": {
                "location": "Downtown Clinic",
                "specialization": "Orthopedics",
                "working_hours": {"start": "10:00", "end": "18:00"},
                "break_time": {"start": "13:00", "end": "14:00"},
                "appointments": []
            }
        }
        self._save_doctors(doctors)
        return doctors

    def _save_doctors(self, doctors: Dict):
        with open(self.filepath, 'w') as f:
            json.dump(doctors, f, indent=2)

    def get_doctor_info(self, doctor_name: str) -> Optional[Dict]:
        return self.doctors.get(doctor_name)

    def get_available_doctors(self) -> List[str]:
        return list(self.doctors.keys())

    def validate_date(self, date_str: str) -> bool:
        try:
            return datetime.strptime(date_str, "%Y-%m-%d").date() >= datetime.now().date()
        except ValueError:
            return False

    def get_available_slots(self, doctor_name: str, date: str,
                            duration: int) -> List[str]:
        """
        Get available slots using DB as source of truth.
        Filters out slots where:
        - DB status != 'available'
        - A booked appointment would overlap (accounting for duration)
        """
        if doctor_name not in self.doctors:
            return []

        doctor = self.doctors[doctor_name]

        # ── Load DB slots for this doctor+date ────────────────────────────────
        try:
            from database.db import get_available_slots as db_get_slots
            db_slots = set(db_get_slots(doctor_name, date))
        except Exception as e:
            logger.warning(f"DB slot fetch failed, falling back to time generation: {e}")
            db_slots = None

        # ── Load existing booked appointments for overlap check ────────────────
        booked_appointments = self._get_db_booked_appointments(doctor_name, date)

        # ── Parse doctor schedule ──────────────────────────────────────────────
        start_time  = datetime.strptime(doctor['working_hours']['start'], "%H:%M")
        end_time    = datetime.strptime(doctor['working_hours']['end'],   "%H:%M")
        break_start = datetime.strptime(doctor['break_time']['start'],    "%H:%M")
        break_end   = datetime.strptime(doctor['break_time']['end'],      "%H:%M")

        base_date   = datetime.strptime(date, "%Y-%m-%d")
        start_dt    = base_date.replace(hour=start_time.hour,  minute=start_time.minute)
        end_dt      = base_date.replace(hour=end_time.hour,    minute=end_time.minute)
        break_s_dt  = base_date.replace(hour=break_start.hour, minute=break_start.minute)
        break_e_dt  = base_date.replace(hour=break_end.hour,   minute=break_end.minute)

        available = []
        current   = start_dt

        while current < end_dt:
            slot_str  = current.strftime("%H:%M")
            slot_end  = current + timedelta(minutes=duration)

            # ── Skip if DB says not available ──────────────────────────────────
            if db_slots is not None and slot_str not in db_slots:
                current += timedelta(minutes=30)
                continue

            # ── Skip if slot falls in break ────────────────────────────────────
            if current >= break_s_dt and current < break_e_dt:
                current += timedelta(minutes=30)
                continue

            # ── Skip if slot would run INTO break ──────────────────────────────
            if current < break_s_dt and slot_end > break_s_dt:
                current += timedelta(minutes=30)
                continue

            # ── Skip if slot would run past end of day ─────────────────────────
            if slot_end > end_dt:
                current += timedelta(minutes=30)
                continue

            # ── Skip if overlaps with any existing appointment ─────────────────
            if self._overlaps_existing(current, slot_end, booked_appointments, base_date):
                current += timedelta(minutes=30)
                continue

            available.append(slot_str)
            current += timedelta(minutes=30)

        return available

    def _get_db_booked_appointments(self, doctor_name: str, date: str) -> List[Dict]:
        """Fetch booked appointments from DB for overlap checking."""
        try:
            from database.db import get_connection
            import psycopg2.extras
            conn = get_connection()
            cur  = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute("""
                SELECT appointment_time, duration_minutes
                FROM appointments
                WHERE doctor_name = %s
                  AND appointment_date = %s
                  AND booking_success = TRUE
                  AND status != 'cancelled'
            """, (doctor_name, date))
            rows = cur.fetchall()
            cur.close()
            conn.close()
            return [dict(r) for r in rows]
        except Exception as e:
            logger.warning(f"Could not fetch booked appointments: {e}")
            return []

    def _overlaps_existing(self, slot_start: datetime, slot_end: datetime,
                           booked: List[Dict], base_date: datetime) -> bool:
        """Return True if proposed slot overlaps any existing booking."""
        for appt in booked:
            try:
                t     = datetime.strptime(appt['appointment_time'], "%H:%M")
                a_start = base_date.replace(hour=t.hour, minute=t.minute)
                a_end   = a_start + timedelta(minutes=appt.get('duration_minutes', 30))
                # Overlap condition
                if slot_start < a_end and slot_end > a_start:
                    return True
            except Exception:
                continue
        return False

    def book_slot(self, doctor_name: str, date: str, time: str,
                  patient_id: str, duration: int) -> bool:
        """
        Book a slot — write to BOTH doctors.json and DB doctor_slots table.
        Also verifies no overlap before booking.
        """
        if doctor_name not in self.doctors:
            return False

        # ── Re-verify slot is still free (overlap check against DB) ───────────
        booked = self._get_db_booked_appointments(doctor_name, date)
        base   = datetime.strptime(date, "%Y-%m-%d")
        t      = datetime.strptime(time, "%H:%M")
        s_start = base.replace(hour=t.hour, minute=t.minute)
        s_end   = s_start + timedelta(minutes=duration)

        if self._overlaps_existing(s_start, s_end, booked, base):
            logger.warning(f"Overlap detected: {doctor_name} {date} {time}")
            return False

        # ── Write to doctors.json ──────────────────────────────────────────────
        datetime_str = f"{date} {time}"
        self.doctors[doctor_name]['appointments'].append({
            'patient_id': patient_id,
            'datetime':   datetime_str,
            'duration':   duration,
            'booked_at':  datetime.now().isoformat()
        })
        self._save_doctors(self.doctors)

        # ── Mark slot as booked in DB doctor_slots ─────────────────────────────
        try:
            from database.db import book_slot as db_book_slot
            db_book_slot(doctor_name, date, time)
        except Exception as e:
            logger.warning(f"DB slot update failed: {e}")

        return True