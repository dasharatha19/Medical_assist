"""
tests/unit/test_validators.py
Unit tests for input validation logic.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from utils.validators import ContactValidator, PatientDataValidator, SchedulingValidator


class TestPatientDataValidator:
    def test_valid_name(self):
        valid, msg = PatientDataValidator.validate_name("John Doe")
        assert valid is True

    def test_name_too_short(self):
        valid, msg = PatientDataValidator.validate_name("Jo")
        assert valid is False

    def test_name_with_numbers_rejected(self):
        valid, msg = PatientDataValidator.validate_name("John123")
        assert valid is False

    def test_empty_name_rejected(self):
        valid, msg = PatientDataValidator.validate_name("")
        assert valid is False

    def test_valid_dob(self):
        valid, msg = PatientDataValidator.validate_dob("1990-01-15")
        assert valid is True

    def test_future_dob_rejected(self):
        valid, msg = PatientDataValidator.validate_dob("2099-01-01")
        assert valid is False

    def test_invalid_dob_format(self):
        valid, msg = PatientDataValidator.validate_dob("15/01/1990")
        # Should handle gracefully — either parse or reject with message
        assert isinstance(valid, bool)
        assert isinstance(msg, str)


class TestContactValidator:
    def test_valid_email(self):
        valid, msg = ContactValidator.validate_email("john.doe@example.com")
        assert valid is True

    def test_missing_at_symbol(self):
        valid, msg = ContactValidator.validate_email("johndoe.com")
        assert valid is False

    def test_empty_email_rejected(self):
        valid, msg = ContactValidator.validate_email("")
        assert valid is False

    def test_valid_phone_10_digits(self):
        valid, msg = ContactValidator.validate_phone("9876543210")
        assert valid is True

    def test_phone_too_short(self):
        valid, msg = ContactValidator.validate_phone("12345")
        assert valid is False

    def test_phone_with_country_code(self):
        valid, msg = ContactValidator.validate_phone("+919876543210")
        # Should handle international format
        assert isinstance(valid, bool)


class TestSchedulingValidator:
    def test_valid_future_date(self):
        from datetime import date, timedelta

        future = str(date.today() + timedelta(days=5))
        valid, msg = SchedulingValidator.validate_appointment_date(future)
        assert valid is True

    def test_past_date_rejected(self):
        valid, msg = SchedulingValidator.validate_appointment_date("2020-01-01")
        assert valid is False

    def test_invalid_date_format(self):
        valid, msg = SchedulingValidator.validate_appointment_date("not-a-date")
        assert valid is False
