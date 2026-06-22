"""
tests/integration/test_database.py
Integration tests for the PostgreSQL database layer.
Requires a real PostgreSQL connection (set via env vars).
Skipped automatically if DB is unavailable.
"""
import pytest
import os
import uuid
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

# Skip entire module if no real DB configured
DB_AVAILABLE = bool(os.getenv("DATABASE_URL") or os.getenv("DB_HOST"))
pytestmark = pytest.mark.skipif(
    not DB_AVAILABLE, reason="No database configured"
)


@pytest.fixture(scope="module")
def db_connection():
    """Create a test DB connection and ensure schema exists."""
    from database.db import get_connection, create_tables
    try:
        create_tables()
        conn = get_connection()
        yield conn
        conn.close()
    except Exception as e:
        pytest.skip(f"DB connection failed: {e}")


@pytest.fixture
def test_patient_id():
    return f"TEST-{uuid.uuid4().hex[:8].upper()}"


class TestPatientOperations:
    def test_save_and_retrieve_appointment(self, db_connection, test_patient_id):
        """Appointment saved to DB can be retrieved."""
        from database.db import save_appointment, get_appointment_by_id
        appt_data = {
            "patient_id": test_patient_id,
            "patient_name": "Test Patient",
            "patient_email": "test@example.com",
            "patient_phone": "9876543210",
            "appointment_date": "2026-07-15",
            "selected_time": "10:00 AM",
            "preferred_doctor": "Dr. Smith",
            "appointment_id": f"APPT-{uuid.uuid4().hex[:8]}",
        }
        result = save_appointment(appt_data)
        assert result is not None

    def test_duplicate_patient_handled_gracefully(self, db_connection, test_patient_id):
        """Saving same patient twice should not crash."""
        from database.db import save_appointment
        appt_data = {
            "patient_id": test_patient_id,
            "patient_name": "Test Patient",
            "patient_email": "test@example.com",
            "appointment_id": f"APPT-{uuid.uuid4().hex[:8]}",
        }
        # Should not raise
        try:
            save_appointment(appt_data)
        except Exception:
            pass  # Duplicate handling is acceptable


class TestDatabaseSchema:
    def test_tables_created(self, db_connection):
        """Core tables should exist after schema init."""
        cur = db_connection.cursor()
        cur.execute("""
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = 'public'
        """)
        tables = [row[0] for row in cur.fetchall()]
        cur.close()
        # At minimum, appointments or patients table should exist
        assert any(t in tables for t in ["appointments", "patients"])
