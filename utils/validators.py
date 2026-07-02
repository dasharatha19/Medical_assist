"""
Advanced Validators Module
Enhanced validation functions with comprehensive edge case handling
Designed for medical appointment scheduling system

Provides:
- Input validation with detailed error messages
- Edge case detection
- Business logic validation
- Formatting utilities
"""

import re
from datetime import datetime, timedelta


class ValidationError:
    """Represents a validation error with helpful context"""

    def __init__(self, message: str, error_code: str = "", suggestion: str = ""):
        """
        Initialize validation error

        Args:
            message: User-friendly error message
            error_code: Internal error code for debugging
            suggestion: Helpful suggestion to fix the error
        """
        self.message = message
        self.error_code = error_code
        self.suggestion = suggestion

    def __str__(self) -> str:
        """Return formatted error message"""
        if self.suggestion:
            return f"{self.message}\n💡 Suggestion: {self.suggestion}"
        return self.message


class PatientDataValidator:
    """Validators for patient biographical information"""

    @staticmethod
    def validate_name(name: str) -> tuple[bool, str]:
        """
        Validate patient name

        Args:
            name: Patient name string

        Returns:
            Tuple of (is_valid: bool, cleaned_name_or_error: str)
        """
        name = name.strip()

        # Check empty
        if not name:
            return False, "Name cannot be empty"

        # Check length
        if len(name) < 2:
            return False, "Name must be at least 2 characters (e.g., 'Jo' for Jo Smith)"

        if len(name) > 100:
            return False, "Name must not exceed 100 characters"

        # Check characters - allow letters, spaces, hyphens, apostrophes
        allowed_pattern = r"^[a-zA-Z\s\-']+$"
        if not re.match(allowed_pattern, name):
            invalid_chars = [c for c in name if not re.match(r"[a-zA-Z\s\-']", c)]
            return (
                False,
                f"Name contains invalid characters: {', '.join(set(invalid_chars))}. Only letters, spaces, hyphens, and apostrophes allowed.",
            )

        # Clean up multiple spaces
        cleaned = " ".join(name.split())

        return True, cleaned

    @staticmethod
    def validate_dob(dob_str: str, allow_future: bool = False) -> tuple[bool, str]:
        """
        Validate date of birth

        Args:
            dob_str: Date of birth string (expected format: YYYY-MM-DD)
            allow_future: Whether to allow future dates (useful for testing)

        Returns:
            Tuple of (is_valid: bool, formatted_dob_or_error: str)
        """
        dob_str = dob_str.strip()

        # Try different date formats
        date_formats = ["%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%m-%d-%Y"]
        dob_obj = None

        for fmt in date_formats:
            try:
                dob_obj = datetime.strptime(dob_str, fmt)
                break
            except ValueError:
                continue

        if dob_obj is None:
            return (
                False,
                "Invalid date format. Please use YYYY-MM-DD (e.g., 1990-05-15). Other formats accepted: MM/DD/YYYY or DD/MM/YYYY",
            )

        today = datetime.now()

        # Check if future date (unless testing)
        if not allow_future and dob_obj > today:
            return False, "Date of birth cannot be in the future"

        # Check age reasonableness
        age = today.year - dob_obj.year
        if (today.month, today.day) < (dob_obj.month, dob_obj.day):
            age -= 1

        if age < 0:
            return False, "Date of birth cannot be in the future"

        if age > 150:
            return False, f"Age ({age}) seems invalid. Is your date of birth correct?"

        if age < 0:
            return False, "Invalid date of birth (negative age)"

        # Return in standard format
        return True, dob_obj.strftime("%Y-%m-%d")


class ContactValidator:
    """Validators for contact information"""

    @staticmethod
    def validate_email(email: str) -> tuple[bool, str]:
        """
        Validate email address

        Args:
            email: Email address string

        Returns:
            Tuple of (is_valid: bool, cleaned_email_or_error: str)
        """
        email = email.strip().lower()

        if not email:
            return False, "Email cannot be empty"

        # Basic email pattern
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"

        if not re.match(pattern, email):
            return False, "Invalid email format. Example: john.doe@example.com"

        # Check for common mistakes
        if email.endswith(".c"):
            return False, "Email ends with '.c' - did you mean '.com'?"

        if email.count("@@") > 0:
            return False, "Email contains multiple @ symbols"

        return True, email

    @staticmethod
    def validate_phone(phone_str: str) -> tuple[bool, str]:
        """
        Validate phone number

        Args:
            phone_str: Phone number string (accepts various formats)

        Returns:
            Tuple of (is_valid: bool, formatted_phone_or_error: str)
        """
        phone_str = phone_str.strip()

        if not phone_str:
            return False, "Phone number cannot be empty"

        # Extract only digits
        digits_only = re.sub(r"\D", "", phone_str)

        # Check length (10 digits for US, allow 7-15 for international)
        if len(digits_only) < 7:
            return False, "Phone number too short. Must be at least 7 digits"

        if len(digits_only) > 15:
            return False, "Phone number too long. Maximum 15 digits"

        # Format as (XXX) XXX-XXXX for 10-digit numbers
        if len(digits_only) == 10:
            return True, f"({digits_only[:3]}) {digits_only[3:6]}-{digits_only[6:]}"

        # For other lengths, just return digits with dashes
        return True, "-".join(
            [digits_only[i : i + 3] for i in range(0, len(digits_only), 3)]
        )


class SchedulingValidator:
    """Validators for appointment scheduling"""

    @staticmethod
    def validate_appointment_date(date_str: str) -> tuple[bool, str]:
        """
        Validate appointment date

        Args:
            date_str: Date string (expected format: YYYY-MM-DD)

        Returns:
            Tuple of (is_valid: bool, formatted_date_or_error: str)
        """
        date_str = date_str.strip()

        if not date_str:
            return False, "Date cannot be empty"

        # Try parsing
        date_formats = ["%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y"]
        apt_date = None

        for fmt in date_formats:
            try:
                apt_date = datetime.strptime(date_str, fmt)
                break
            except ValueError:
                continue

        if apt_date is None:
            return (
                False,
                "Invalid date format. Please use YYYY-MM-DD (e.g., 2026-04-15). Accepts MM/DD/YYYY or DD/MM/YYYY",
            )

        today = datetime.now().date()
        apt_date_only = apt_date.date()

        # Check if past
        if apt_date_only < today:
            days_in_past = (today - apt_date_only).days
            return (
                False,
                f"That date is {days_in_past} days in the past. Please select a future date",
            )

        # Check if too far in future (>365 days)
        if apt_date_only > today + timedelta(days=365):
            return False, "Appointments can only be scheduled up to 1 year in advance"

        return True, apt_date.strftime("%Y-%m-%d")

    @staticmethod
    def validate_time_slot(time_str: str) -> tuple[bool, str]:
        """
        Validate appointment time slot
        Accepts formats: HH:MM, H:MM, HH:MM AM/PM

        Args:
            time_str: Time string

        Returns:
            Tuple of (is_valid: bool, formatted_time_or_error: str)
        """
        time_str = time_str.strip().upper()

        if not time_str:
            return False, "Time cannot be empty"

        # Try 24-hour format first (HH:MM)
        try:
            time_obj = datetime.strptime(time_str, "%H:%M")
            return True, time_obj.strftime("%H:%M")
        except ValueError:
            pass

        # Try 12-hour format (HH:MM AM/PM)
        try:
            time_obj = datetime.strptime(time_str, "%I:%M %p")
            return True, time_obj.strftime("%H:%M")
        except ValueError:
            pass

        # Try short format (H:MM)
        try:
            time_obj = datetime.strptime(time_str, "%H:%M")
            return True, time_obj.strftime("%H:%M")
        except ValueError:
            pass

        return (
            False,
            "Invalid time format. Please use HH:MM (24-hour, e.g., 14:30) or HH:MM AM/PM (e.g., 2:30 PM)",
        )

    @staticmethod
    def validate_doctor_name(
        doctor_name: str, available_doctors: list[str]
    ) -> tuple[bool, str]:
        """
        Validate doctor name against available doctors

        Args:
            doctor_name: Doctor name to validate
            available_doctors: List of valid doctor names

        Returns:
            Tuple of (is_valid: bool, doctor_name_or_error: str)
        """
        doctor_name = doctor_name.strip()

        if not doctor_name:
            return False, "Doctor name cannot be empty"

        # Case-insensitive exact match
        for doc in available_doctors:
            if doc.lower() == doctor_name.lower():
                return True, doc

        # Check for partial matches or typos
        matches = [
            doc for doc in available_doctors if doctor_name.lower() in doc.lower()
        ]
        if matches:
            return False, f"Did you mean: {', '.join(matches)}?"

        return (
            False,
            f"Doctor '{doctor_name}' not found. Available doctors: {', '.join(available_doctors)}",
        )

    @staticmethod
    def validate_duration_match(
        appointment_duration: int, duration_options: list[int] = None
    ) -> tuple[bool, str]:
        """
        Validate appointment duration

        Args:
            appointment_duration: Duration in minutes
            duration_options: List of valid durations (default: [30, 60])

        Returns:
            Tuple of (is_valid: bool, message: str)
        """
        if duration_options is None:
            duration_options = [30, 60]

        if appointment_duration in duration_options:
            return True, f"Appointment duration: {appointment_duration} minutes"

        return (
            False,
            f"Invalid duration {appointment_duration}. Valid durations: {', '.join(str(d) for d in duration_options)} minutes",
        )


class InsuranceValidator:
    """Validators for insurance information"""

    @staticmethod
    def validate_insurance_carrier(
        carrier: str, valid_carriers: list[str]
    ) -> tuple[bool, str]:
        """
        Validate insurance carrier

        Args:
            carrier: Carrier name
            valid_carriers: List of valid carriers

        Returns:
            Tuple of (is_valid: bool, carrier_name_or_error: str)
        """
        carrier = carrier.strip()

        if not carrier:
            return False, "Insurance carrier cannot be empty"

        # Case-insensitive match
        for valid in valid_carriers:
            if valid.lower() == carrier.lower():
                return True, valid

        # Check for partial matches
        matches = [c for c in valid_carriers if carrier.lower() in c.lower()]
        if matches:
            return False, f"Did you mean: {', '.join(matches)}?"

        return (
            False,
            f"Carrier '{carrier}' not recognized. Valid carriers: {', '.join(valid_carriers)}",
        )

    @staticmethod
    def validate_member_id(member_id: str) -> tuple[bool, str]:
        """
        Validate insurance member ID

        Args:
            member_id: Member ID string

        Returns:
            Tuple of (is_valid: bool, member_id_or_error: str)
        """
        member_id = member_id.strip()

        if not member_id:
            return False, "Member ID cannot be empty"

        if len(member_id) < 3:
            return (
                False,
                f"Member ID too short ({len(member_id)} chars). Minimum 3 characters required",
            )

        if len(member_id) > 50:
            return (
                False,
                f"Member ID too long ({len(member_id)} chars). Maximum 50 characters",
            )

        return True, member_id.upper()

    @staticmethod
    def validate_group_id(group_id: str) -> tuple[bool, str]:
        """
        Validate insurance group ID

        Args:
            group_id: Group ID string

        Returns:
            Tuple of (is_valid: bool, group_id_or_error: str)
        """
        group_id = group_id.strip()

        if not group_id:
            return False, "Group ID cannot be empty"

        if len(group_id) < 2:
            return (
                False,
                f"Group ID too short ({len(group_id)} chars). Minimum 2 characters",
            )

        if len(group_id) > 50:
            return (
                False,
                f"Group ID too long ({len(group_id)} chars). Maximum 50 characters",
            )

        return True, group_id.upper()

    @staticmethod
    def validate_all_insurance_fields(
        carrier: str, member_id: str, group_id: str, valid_carriers: list[str]
    ) -> tuple[bool, dict]:
        """
        Validate all insurance fields together

        Args:
            carrier: Insurance carrier
            member_id: Member ID
            group_id: Group ID
            valid_carriers: List of valid carriers

        Returns:
            Tuple of (all_valid: bool, results_dict: Dict)
        """
        results = {
            "carrier_valid": False,
            "member_id_valid": False,
            "group_id_valid": False,
            "all_valid": False,
            "errors": [],
        }

        # Validate each field
        carrier_valid, carrier_msg = InsuranceValidator.validate_insurance_carrier(
            carrier, valid_carriers
        )
        if carrier_valid:
            results["carrier_valid"] = True
        else:
            results["errors"].append(f"Carrier: {carrier_msg}")

        member_valid, member_msg = InsuranceValidator.validate_member_id(member_id)
        if member_valid:
            results["member_id_valid"] = True
        else:
            results["errors"].append(f"Member ID: {member_msg}")

        group_valid, group_msg = InsuranceValidator.validate_group_id(group_id)
        if group_valid:
            results["group_id_valid"] = True
        else:
            results["errors"].append(f"Group ID: {group_msg}")

        results["all_valid"] = carrier_valid and member_valid and group_valid

        return results["all_valid"], results


class ConfirmationValidator:
    """Validators for user confirmation responses"""

    @staticmethod
    def validate_yes_no_response(response: str) -> tuple[bool, bool]:
        """
        Validate yes/no response

        Args:
            response: User's response string

        Returns:
            Tuple of (is_valid: bool, is_affirmative: bool)
        """
        response = response.strip().lower()

        if response in [
            "yes",
            "y",
            "1",
            "ok",
            "okay",
            "correct",
            "true",
            "affirmative",
        ]:
            return True, True
        elif response in ["no", "n", "0", "nope", "false", "negative", "incorrect"]:
            return True, False
        else:
            return False, None

    @staticmethod
    def validate_cancellation_reason(reason: str) -> tuple[bool, str]:
        """
        Validate cancellation reason

        Args:
            reason: Reason for cancellation

        Returns:
            Tuple of (is_valid: bool, cleaned_reason: str)
        """
        reason = reason.strip()

        if not reason:
            return True, "No reason provided"

        if len(reason) > 500:
            return False, "Reason too long (max 500 characters)"

        return True, reason


class EdgeCaseValidator:
    """Validators for edge cases and special scenarios"""

    @staticmethod
    def check_slot_availability(available_slots: list[str]) -> tuple[bool, str]:
        """
        Check if any slots are available

        Args:
            available_slots: List of available time slots

        Returns:
            Tuple of (slots_available: bool, message: str)
        """
        if not available_slots or len(available_slots) == 0:
            return False, "No appointment slots available for this date"

        return True, f"{len(available_slots)} slots available"

    @staticmethod
    def check_overlapping_bookings(
        new_date: str,
        new_time: str,
        new_duration: int,
        existing_appointments: list[dict],
    ) -> tuple[bool, str]:
        """
        Check for overlapping bookings

        Args:
            new_date: New appointment date (YYYY-MM-DD)
            new_time: New appointment time (HH:MM)
            new_duration: Duration in minutes
            existing_appointments: List of existing appointment dicts
                                 with 'date', 'time', 'duration' keys

        Returns:
            Tuple of (no_overlap: bool, message: str)
        """
        if not existing_appointments:
            return True, "Slot is available"

        # Convert new appointment times to minutes for comparison
        new_start_str = f"{new_date} {new_time}"
        try:
            new_start = datetime.strptime(new_start_str, "%Y-%m-%d %H:%M")
            new_end = new_start + timedelta(minutes=new_duration)
        except ValueError:
            return False, "Invalid date/time format for overlap check"

        # Check each existing appointment
        for apt in existing_appointments:
            try:
                existing_start_str = f"{apt['date']} {apt['time']}"
                existing_start = datetime.strptime(existing_start_str, "%Y-%m-%d %H:%M")
                existing_end = existing_start + timedelta(
                    minutes=apt.get("duration", 30)
                )

                # Check if there's overlap
                if (new_start < existing_end) and (new_end > existing_start):
                    # existing_duration removed (unused)
                    return (
                        False,
                        f"Slot conflicts with existing appointment ({existing_start.strftime('%H:%M')} - {existing_end.strftime('%H:%M')})",
                    )
            except ValueError:
                continue

        return True, "Slot is available"

    @staticmethod
    def check_patient_found(patient_id: str) -> tuple[bool, str]:
        """
        Check if patient was found in database

        Args:
            patient_id: Patient ID result

        Returns:
            Tuple of (found: bool, status: str)
        """
        if not patient_id or patient_id.startswith("NEW"):
            return False, "New patient - creating profile"

        return True, "Existing patient found"

    @staticmethod
    def check_appointment_completeness(
        state_dict: dict[str, str]
    ) -> tuple[bool, list[str]]:
        """
        Check if all required appointment fields are filled

        Args:
            state_dict: Dictionary of state values

        Returns:
            Tuple of (complete: bool, missing_fields: List[str])
        """
        required_fields = [
            ("patient_name", "Patient name"),
            ("patient_dob", "Date of birth"),
            ("patient_email", "Email address"),
            ("patient_phone", "Phone number"),
            ("preferred_doctor", "Doctor"),
            ("appointment_date", "Appointment date"),
            ("selected_time", "Appointment time"),
            ("insurance_carrier", "Insurance carrier"),
        ]

        missing = []
        for field, label in required_fields:
            if not state_dict.get(field):
                missing.append(label)

        return len(missing) == 0, missing


# Convenience functions for quick validation usage
def is_valid_name(name: str) -> bool:
    """Quick name validation"""
    valid, _ = PatientDataValidator.validate_name(name)
    return valid


def is_valid_email(email: str) -> bool:
    """Quick email validation"""
    valid, _ = ContactValidator.validate_email(email)
    return valid


def is_valid_phone(phone: str) -> bool:
    """Quick phone validation"""
    valid, _ = ContactValidator.validate_phone(phone)
    return valid


def is_valid_date(date_str: str) -> bool:
    """Quick date validation"""
    valid, _ = SchedulingValidator.validate_appointment_date(date_str)
    return valid


def is_valid_time(time_str: str) -> bool:
    """Quick time validation"""
    valid, _ = SchedulingValidator.validate_time_slot(time_str)
    return valid
