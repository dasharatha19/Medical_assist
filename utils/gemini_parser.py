"""
Gemini LLM Parser
Leverages Google Gemini API for natural language understanding and field extraction

Features:
- Parse free-form user input into structured fields
- Extract name, DOB, phone, email, doctor preference, insurance info
- Graceful error handling and fallback support
- Production-ready with safe import and initialization
- Logging and monitoring

Dependencies:
- google-generativeai>=0.7.0 (optional - falls back to rule-based parsing if missing)
"""

import json
import logging
import os
from datetime import datetime
from typing import Any

# Safe import with graceful fallback
try:
    from google import genai

    GENAI_AVAILABLE = True
except ImportError:
    genai = None
    GENAI_AVAILABLE = False


logger = logging.getLogger(__name__)


class GeminiParser:
    """
    Natural Language Parser using Google Gemini API
    Extracts structured information from conversational user input
    """

    # Extraction template for consistent output
    EXTRACTION_TEMPLATE = """
You are a helpful assistant for a medical appointment scheduling system.
Extract the following information from the user input if available.
Return ONLY valid JSON, nothing else.

Fields to extract (use null if not found):
- name: Patient full name
- date_of_birth: Date of birth in YYYY-MM-DD format
- age: Age if mentioned
- phone: Phone number
- email: Email address
- location: Location/city mentioned
- doctor_preference: Preferred doctor name or specialty
- insurance_provider: Insurance company name
- insurance_id: Insurance member ID
- intent: Primary intent (e.g., "schedule_appointment", "check_availability")

User input: "{user_input}"

IMPORTANT RULES:
- Extract ONLY the actual value, NOT the full sentence
- For name: return "John Smith" NOT "my name is John Smith"
- For date_of_birth: return "1990-03-15" NOT "born in March 1990"
- If a field is not mentioned, return null

Return valid JSON response:
"""

    def __init__(self, api_key: str | None = None):
        from utils.config import Config

        self.api_key = api_key or os.getenv("GEMINI_API_KEY") or Config.GEMINI_API_KEY
        self.model_name = Config.LLM_MODEL
        self.enabled = False
        self.client = None
        self.init_error = None

        if not GENAI_AVAILABLE:
            self.init_error = "google-genai not installed"
            return

        if not self.api_key or not self.api_key.strip():
            self.init_error = "GEMINI_API_KEY not set"
            return

        try:
            self.client = genai.Client(api_key=self.api_key.strip())
            self.enabled = True
            logger.info(f"Gemini Parser initialized with model: {self.model_name}")
        except Exception as e:
            self.init_error = str(e)
            self.enabled = False

    def parse_user_input(self, user_input: str) -> tuple[bool, dict[str, Any]]:
        if not self.enabled or not self.client:
            return False, {}

        if not user_input or not user_input.strip():
            return False, {}

        try:
            prompt = self.EXTRACTION_TEMPLATE.format(user_input=user_input.strip())
            response = self.client.models.generate_content(
                model=self.model_name, contents=prompt
            )

            if not response or not response.text:
                return False, {}

            response_text = response.text.strip()
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
            response_text = response_text.strip()

            parsed_fields = json.loads(response_text)
            cleaned_fields = self._validate_fields(parsed_fields)
            return True, cleaned_fields

        except Exception as e:
            logger.error(f"Gemini API call failed: {e}")
            return False, {}

    def _validate_fields(self, fields: dict[str, Any]) -> dict[str, Any]:
        """
        Validate and clean extracted fields

        Args:
            fields: Raw extracted fields from Gemini

        Returns:
            Cleaned and validated fields
        """
        cleaned = {}

        # Name validation
        if fields.get("name") and isinstance(fields["name"], str):
            name = fields["name"].strip()
            if len(name) >= 2:
                cleaned["name"] = name

        # DOB validation and formatting
        if fields.get("date_of_birth"):
            dob = self._parse_date(fields["date_of_birth"])
            if dob:
                cleaned["date_of_birth"] = dob

        # Age validation
        if fields.get("age"):
            try:
                age = int(fields["age"])
                if 0 < age < 150:
                    cleaned["age"] = age
            except (ValueError, TypeError):
                pass

        # Phone validation
        if fields.get("phone"):
            phone = (
                fields["phone"]
                .replace(" ", "")
                .replace("-", "")
                .replace("(", "")
                .replace(")", "")
            )
            if len(phone) >= 10 and phone.isdigit():
                cleaned["phone"] = phone

        # Email validation
        if fields.get("email") and isinstance(fields["email"], str):
            email = fields["email"].strip()
            if "@" in email and "." in email:
                cleaned["email"] = email

        # Location (keep as-is if valid)
        if fields.get("location") and isinstance(fields["location"], str):
            location = fields["location"].strip()
            if location:
                cleaned["location"] = location

        # Doctor preference
        if fields.get("doctor_preference") and isinstance(
            fields["doctor_preference"], str
        ):
            doc_pref = fields["doctor_preference"].strip()
            if doc_pref:
                cleaned["doctor_preference"] = doc_pref

        # Insurance info
        if fields.get("insurance_provider") and isinstance(
            fields["insurance_provider"], str
        ):
            provider = fields["insurance_provider"].strip()
            if provider:
                cleaned["insurance_provider"] = provider

        if fields.get("insurance_id") and isinstance(fields["insurance_id"], str):
            ins_id = fields["insurance_id"].strip()
            if ins_id:
                cleaned["insurance_id"] = ins_id

        # Intent
        if fields.get("intent") and isinstance(fields["intent"], str):
            intent = fields["intent"].strip().lower()
            if intent:
                cleaned["intent"] = intent

        return cleaned

    def _parse_date(self, date_str: Any) -> str | None:
        """
        Parse date string from various formats to YYYY-MM-DD

        Args:
            date_str: Date in various formats

        Returns:
            Date in YYYY-MM-DD format or None
        """
        if not isinstance(date_str, str):
            return None

        date_str = date_str.strip()

        # Try common formats
        formats = [
            "%Y-%m-%d",
            "%Y/%m/%d",
            "%m/%d/%Y",
            "%d/%m/%Y",
            "%m-%d-%Y",
            "%d-%m-%Y",
            "%B %d, %Y",
            "%b %d, %Y",
            "%d %B %Y",
            "%d %b %Y",
        ]

        for fmt in formats:
            try:
                parsed = datetime.strptime(date_str, fmt)
                return parsed.strftime("%Y-%m-%d")
            except ValueError:
                continue

        # If year is provided alone, estimate DOB
        if date_str.isdigit() and len(date_str) == 4:
            try:
                year = int(date_str)
                if 1900 <= year <= 2025:
                    return f"{year}-01-01"
            except ValueError:
                pass

        return None

    def is_enabled(self) -> bool:
        """Check if Gemini parser is properly enabled"""
        return self.enabled


# Singleton instance
_gemini_parser_instance: GeminiParser | None = None


def get_gemini_parser() -> GeminiParser:
    """
    Get singleton Gemini parser instance

    Returns:
        GeminiParser instance
    """
    global _gemini_parser_instance
    if _gemini_parser_instance is None:
        _gemini_parser_instance = GeminiParser()
    return _gemini_parser_instance


def parse_with_gemini(user_input: str) -> tuple[bool, dict[str, Any]]:
    """
    Convenience function to parse user input with Gemini

    Args:
        user_input: User's conversational input

    Returns:
        Tuple of (success, parsed_fields)
    """
    parser = get_gemini_parser()
    return parser.parse_user_input(user_input)
