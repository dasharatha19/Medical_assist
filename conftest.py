# conftest.py — root-level pytest configuration
import os
import sys

# Ensure project root is on the path for all tests
sys.path.insert(0, os.path.dirname(__file__))

import pytest


@pytest.fixture(autouse=True)
def isolate_env(monkeypatch):
    """
    Prevent tests from accidentally using real API keys.
    Unsets all production secrets during testing unless explicitly provided.
    """
    # Only clear if NOT explicitly set for integration testing
    if not os.getenv("ALLOW_REAL_API_CALLS"):
        monkeypatch.delenv("GROQ_API_KEY", raising=False)
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.setenv("LLM_ENABLED", "false")
        monkeypatch.setenv("LLM_PROVIDER", "none")


@pytest.fixture
def sample_patient_state():
    """Reusable complete patient state for testing."""
    return {
        "patient_name": "Jane Doe",
        "patient_dob": "1990-05-15",
        "patient_email": "jane.doe@example.com",
        "patient_phone": "9876543210",
        "patient_id": "P-TEST-001",
        "patient_type": "new",
        "preferred_doctor": "Dr. Smith",
        "appointment_date": "2026-07-20",
        "selected_time": "10:00 AM",
        "selected_slot": "10:00 AM",
        "insurance_carrier": "BlueCross",
        "insurance_member_id": "BC123456",
        "insurance_group_id": "GRP789",
        "insurance_valid": True,
        "booking_confirmed": False,
        "booking_success": False,
        "workflow_complete": False,
        "session_id": "test-session-001",
        "conversation_context": [],
        "user_input": "",
    }
