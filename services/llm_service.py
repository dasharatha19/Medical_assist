"""
LLM Service Layer
Coordinates between Gemini LLM and rule-based parsing with fallback support

Features:
- Intelligent fallback to rule-based parsing
- Metric tracking and logging
- Graceful degradation on errors
- Configurable behavior
"""

import logging
from typing import Any

from utils.config import Config
from utils.gemini_parser import parse_with_gemini

# Import rule-based parsers
from utils.nl_parser import NLParser

logger = logging.getLogger(__name__)


class LLMService:
    """
    Unified LLM service that attempts Gemini first, falls back to rule-based parsing
    """

    def __init__(self):
        """Initialize LLM service with configuration"""
        self.use_llm = Config.USE_LLM_FOR_PARSING and Config.is_llm_enabled()
        self.fallback_enabled = Config.FALLBACK_TO_RULE_BASED
        self.require_llm = Config.REQUIRE_LLM_SUCCESS

        # Metrics
        self.llm_attempts = 0
        self.llm_successes = 0
        self.fallback_uses = 0

        logger.info(
            f"LLMService initialized: "
            f"use_llm={self.use_llm}, "
            f"fallback_enabled={self.fallback_enabled}, "
            f"require_llm={self.require_llm}"
        )

    def parse_patient_info(self, user_input: str) -> tuple[bool, dict[str, Any]]:
        """
        Parse patient information (name, DOB, phone, email) from user input

        Uses Gemini first, falls back to rule-based parsing if needed

        Args:
            user_input: User's conversational input

        Returns:
            Tuple of (success, parsed_fields)

        Example:
            success, data = service.parse_patient_info("My name is John, born 1990-05-15")
            if success:
                name = data.get('name')
                dob = data.get('date_of_birth')
        """
        if not user_input or not user_input.strip():
            return False, {}

        # Try Gemini if enabled
        if self.use_llm:
            self.llm_attempts += 1

            try:
                success, fields = parse_with_gemini(user_input)

                if success and self._has_patient_fields(fields):
                    self.llm_successes += 1
                    logger.info("Gemini successfully extracted patient fields from input")
                    return True, fields

            except Exception as e:
                logger.error(f"Gemini parsing failed: {str(e)}")

        # Fallback to rule-based parsing
        if not self.require_llm:
            if self.use_llm:
                self.fallback_uses += 1
                logger.info("Falling back to rule-based parsing")

            return self._parse_patient_info_rulebased(user_input)

        # LLM required but failed
        logger.error("LLM parsing required but failed, and fallback disabled")
        return False, {}

    def parse_doctor_preference(self, user_input: str) -> tuple[bool, dict[str, Any]]:
        """
        Parse doctor preference from user input

        Args:
            user_input: User's input about doctor preference

        Returns:
            Tuple of (success, parsed_fields with 'doctor_preference')
        """
        if not user_input or not user_input.strip():
            return False, {}

        if Config.USE_LLM_FOR_DOCTOR_SELECTION and self.use_llm:
            self.llm_attempts += 1

            try:
                success, fields = parse_with_gemini(user_input)

                if success and fields.get("doctor_preference"):
                    self.llm_successes += 1
                    logger.info("Gemini extracted doctor preference")
                    return True, {"doctor_preference": fields["doctor_preference"]}

            except Exception as e:
                logger.error(f"Gemini doctor parsing failed: {str(e)}")

        # Fallback
        if not self.require_llm:
            if Config.USE_LLM_FOR_DOCTOR_SELECTION and self.use_llm:
                self.fallback_uses += 1

            # Simple rule-based extraction for doctor names
            doctor_keywords = ["dr", "doctor", "specialist", "prefer"]
            for keyword in doctor_keywords:
                if keyword.lower() in user_input.lower():
                    # Extract text after keyword
                    idx = user_input.lower().find(keyword)
                    potential_name = user_input[idx:].split(",")[0].strip()
                    if len(potential_name) > 3:
                        return True, {"doctor_preference": potential_name}

        return False, {}

    def parse_insurance_info(self, user_input: str) -> tuple[bool, dict[str, Any]]:
        """
        Parse insurance information from user input

        Args:
            user_input: User's input about insurance

        Returns:
            Tuple of (success, parsed_fields with 'insurance_provider', 'insurance_id')
        """
        if not user_input or not user_input.strip():
            return False, {}

        if Config.USE_LLM_FOR_INSURANCE and self.use_llm:
            self.llm_attempts += 1

            try:
                success, fields = parse_with_gemini(user_input)

                insurance_fields = {}
                if fields.get("insurance_provider"):
                    insurance_fields["insurance_provider"] = fields["insurance_provider"]
                if fields.get("insurance_id"):
                    insurance_fields["insurance_id"] = fields["insurance_id"]

                if success and insurance_fields:
                    self.llm_successes += 1
                    logger.info("Gemini extracted insurance info")
                    return True, insurance_fields

            except Exception as e:
                logger.error(f"Gemini insurance parsing failed: {str(e)}")

        # Fallback
        if not self.require_llm:
            if Config.USE_LLM_FOR_INSURANCE and self.use_llm:
                self.fallback_uses += 1

            # Simple rule-based extraction
            insurance_keywords = ["insurance", "provider", "aetna", "blue cross", "anthem", "cigna"]
            for keyword in insurance_keywords:
                if keyword.lower() in user_input.lower():
                    # Extract context around keyword
                    idx = user_input.lower().find(keyword)
                    potential_info = user_input[max(0, idx - 10) : idx + 40].strip()
                    if len(potential_info) > 3:
                        return True, {"insurance_provider": potential_info}

        return False, {}

    def _parse_patient_info_rulebased(self, user_input: str) -> tuple[bool, dict[str, Any]]:
        """
        Rule-based patient information parsing (fallback)

        Args:
            user_input: User's input

        Returns:
            Tuple of (success, parsed_fields)
        """
        parsed_fields = {}

        # Try to extract name
        name = NLParser.extract_name(user_input)
        if name:
            parsed_fields["name"] = name

        # Try to extract DOB
        dob = NLParser.extract_dob(user_input)
        if dob:
            parsed_fields["date_of_birth"] = dob

        # Try to extract phone
        phone = NLParser.extract_phone(user_input)
        if phone:
            parsed_fields["phone"] = phone

        # Try to extract email
        email = NLParser.extract_email(user_input)
        if email:
            parsed_fields["email"] = email

        return len(parsed_fields) > 0, parsed_fields

    def _has_patient_fields(self, fields: dict[str, Any]) -> bool:
        """
        Check if parsed fields contain at least some patient information

        Args:
            fields: Parsed fields from LLM

        Returns:
            True if has meaningful patient data
        """
        patient_keys = {"name", "date_of_birth", "phone", "email", "age"}
        return any(key in fields and fields[key] is not None for key in patient_keys)

    def get_metrics(self) -> dict[str, Any]:
        """
        Get LLM service metrics for monitoring and debugging

        Returns:
            Dictionary with detailed usage metrics
        """
        success_rate = 0.0
        if self.llm_attempts > 0:
            success_rate = (self.llm_successes / self.llm_attempts) * 100

        return {
            "llm_attempts": self.llm_attempts,
            "llm_successes": self.llm_successes,
            "llm_success_rate_percent": round(success_rate, 2),
            "fallback_uses": self.fallback_uses,
            "llm_enabled": self.use_llm,
            "fallback_enabled": self.fallback_enabled,
        }

    def get_summary(self) -> str:
        """
        Get human-readable summary of LLM service status

        Returns:
            Formatted summary string suitable for logging/display
        """
        metrics = self.get_metrics()

        status = "ENABLED" if metrics["llm_enabled"] else "DISABLED"

        summary_lines = [
            f"LLMService Status: {status}",
            f"  Fallback to rule-based: {metrics['fallback_enabled']}",
            f"  Total LLM attempts: {metrics['llm_attempts']}",
            f"  Successful parses: {metrics['llm_successes']}",
            f"  Success rate: {metrics['llm_success_rate_percent']}%",
            f"  Fallback uses: {metrics['fallback_uses']}",
        ]

        return "\n".join(summary_lines)


# Singleton instance
_llm_service_instance: LLMService | None = None


def get_llm_service() -> LLMService:
    """
    Get singleton LLM service instance

    Returns:
        LLMService instance
    """
    global _llm_service_instance
    if _llm_service_instance is None:
        _llm_service_instance = LLMService()
    return _llm_service_instance


def reset_llm_service() -> None:
    """Reset LLM service instance (useful for testing)"""
    global _llm_service_instance
    _llm_service_instance = None
