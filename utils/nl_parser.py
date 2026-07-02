"""
Natural Language Parser Module
Extracts structured data from unstructured user input
Enables flexible, conversational input handling

Supports:
- Name extraction from various formats
- Date of birth parsing from multiple formats
- Phone number parsing and normalization
- Email address extraction
"""

import re
from datetime import datetime


class NLParser:
    """
    Natural Language Parser for appointment scheduling
    Extracts fields from conversational user input
    """

    @staticmethod
    def extract_name(user_input: str) -> str | None:
        if not user_input or not user_input.strip():
            return None

        text = user_input.strip()

        # Pattern 1: "My name is ..." or "I am ..." or "call me ..."
        patterns = [
            r"(?:my name is|i am|call me|i\'m|im)\s+([A-Za-z][a-zA-Z\s\.\-\']+)",
            r"(?:name:?|called:?)\s+([A-Za-z][a-zA-Z\s\.\-\']+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                # Stop at punctuation or common stop words
                name = re.split(
                    r"[,\.\!\?]|\b(and|or|my|the|is|was)\b", name, flags=re.IGNORECASE
                )[0].strip()
                if name and len(name) >= 2:
                    return name

        # Pattern 2: FIX — allow single-letter words (initials like "R")
        # Matches "Dasharatha R" or "John Smith" or "Mary J. Blige"
        if re.match(r"^[A-Za-z][a-zA-Z]*(?:\s+[A-Za-z][a-zA-Z\.]*)*$", text):
            return text.strip()

        # Pattern 3: First word is capitalized and input is short (likely a name response)
        words = text.split()
        if len(words) <= 4:
            # Check if it looks like a name (mostly letters, maybe initials)
            name_words = []
            for w in words:
                cleaned = re.sub(r"[^a-zA-Z\.\-\']", "", w)
                if cleaned and re.match(r"^[A-Za-z]", cleaned):
                    name_words.append(cleaned)
                else:
                    break  # stop at first non-name word
            if name_words and len(" ".join(name_words)) >= 2:
                return " ".join(name_words)

        return None

    @staticmethod
    def extract_dob(user_input: str) -> str | None:
        """
        Extract date of birth from various formats

        Handles:
        - "1990-05-15" (YYYY-MM-DD)
        - "05/15/1990" (MM/DD/YYYY)
        - "May 15, 1990" (Month DD, YYYY)
        - "15 May 1990" (DD Month YYYY)
        - "1990/05/15"
        - Birth year with age context

        Returns date in YYYY-MM-DD format or None

        Args:
            user_input: User's date input

        Returns:
            Date string in YYYY-MM-DD format or None if parsing fails
        """
        if not user_input or not user_input.strip():
            return None

        text = user_input.strip()

        # Try multiple date formats
        # Date format patterns with regex and parsing lambdas
        # Each tuple contains (pattern, lambda_formatter) where lambda returns YYYY-MM-DD
        date_formats = [
            # YYYY-MM-DD format (standard ISO 8601)
            (
                r"(\d{4})-(\d{1,2})-(\d{1,2})",
                lambda m: f"{m.group(1)}-{m.group(2).zfill(2)}-{m.group(3).zfill(2)}",
            ),
            # MM/DD/YYYY or DD/MM/YYYY format (context-dependent, handled below)
            (r"(\d{1,2})/(\d{1,2})/(\d{4})", None),
            # YYYY/MM/DD format
            (
                r"(\d{4})/(\d{1,2})/(\d{1,2})",
                lambda m: f"{m.group(1)}-{m.group(2).zfill(2)}-{m.group(3).zfill(2)}",
            ),
            # Month DD, YYYY format (e.g., "May 15, 1990")
            (r"([A-Z][a-z]+)\s+(\d{1,2}),?\s+(\d{4})", None),
            # DD Month YYYY format (e.g., "15 May 1990")
            (r"(\d{1,2})\s+([A-Z][a-z]+)\s+(\d{4})", None),
        ]

        for pattern, formatter in date_formats:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                groups = match.groups()

                if formatter:
                    return formatter(match)

                # Handle month-based formats
                if len(groups) == 3:
                    # Check if first or last group is month name
                    month_map = {
                        "jan": 1,
                        "january": 1,
                        "feb": 2,
                        "february": 2,
                        "mar": 3,
                        "march": 3,
                        "apr": 4,
                        "april": 4,
                        "may": 5,
                        "jun": 6,
                        "june": 6,
                        "jul": 7,
                        "july": 7,
                        "aug": 8,
                        "august": 8,
                        "sep": 9,
                        "september": 9,
                        "oct": 10,
                        "october": 10,
                        "nov": 11,
                        "november": 11,
                        "dec": 12,
                        "december": 12,
                    }

                    # Try to parse as Month DD, YYYY
                    month_str = groups[0].lower() if not groups[0].isdigit() else None
                    if month_str in month_map:
                        month_num = month_map[month_str]
                        day = int(groups[1])
                        year = int(groups[2])
                        return f"{year:04d}-{month_num:02d}-{day:02d}"

                    # Try to parse as DD, MM, YYYY
                    try:
                        # Assume MM/DD/YYYY format (common in US)
                        month = int(groups[0])
                        day = int(groups[1])
                        year = int(groups[2])

                        # Validate month
                        if 1 <= month <= 12 and 1 <= day <= 31:
                            return f"{year:04d}-{month:02d}-{day:02d}"
                    except (ValueError, IndexError):
                        pass

        return None

    @staticmethod
    def extract_phone(user_input: str) -> str | None:
        """
        Extract and normalize phone number

        Handles:
        - "555-123-4567"
        - "(555) 123-4567"
        - "555.123.4567"
        - "5551234567"
        - "+1-555-123-4567"
        - "1 (555) 123-4567"

        Returns:
            Normalized phone number (no formatting) or None

        Args:
            user_input: User's phone input

        Returns:
            10-digit phone number string or None if invalid
        """
        if not user_input or not user_input.strip():
            return None

        # Extract digits only
        digits = re.sub(r"\D", "", user_input.strip())

        # Handle US format with leading 1
        if len(digits) == 11 and digits[0] == "1":
            digits = digits[1:]

        # Validate 10-digit phone number
        if len(digits) == 10 and digits.isdigit():
            # Format as XXX-XXX-XXXX
            return f"{digits[:3]}-{digits[3:6]}-{digits[6:]}"

        return None

    @staticmethod
    def extract_email(user_input: str) -> str | None:
        """
        Extract email address from user input

        Handles:
        - "john@example.com"
        - "My email is john@example.com"
        - "Email: john@example.com"
        - "john.smith@domain.co.uk"

        Args:
            user_input: User's email input

        Returns:
            Valid email address or None if not found/invalid
        """
        if not user_input or not user_input.strip():
            return None

        # Simple email regex
        email_pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"

        match = re.search(email_pattern, user_input)
        if match:
            return match.group(0)

        return None


def parse_user_input(field_type: str, user_input: str) -> tuple[bool, str | None, str]:
    """
    Parse user input for a specific field type

    Args:
        field_type: 'name', 'dob', 'phone', 'email'
        user_input: Raw user input

    Returns:
        Tuple of (success: bool, parsed_value: str or None, message: str)
    """
    if field_type == "name":
        parsed = NLParser.extract_name(user_input)
        if parsed:
            return True, parsed, f"Got it, {parsed}!"
        else:
            return False, None, "Sorry, I couldn't extract a name. Please try again."

    elif field_type == "dob":
        parsed = NLParser.extract_dob(user_input)
        if parsed:
            # Verify it's a valid date
            try:
                datetime.strptime(parsed, "%Y-%m-%d")
                return True, parsed, f"Your DOB is {parsed}."
            except ValueError:
                return (
                    False,
                    None,
                    "Invalid date. Please enter in YYYY-MM-DD format or describe the date.",
                )
        else:
            return (
                False,
                None,
                "I couldn't parse that date. Try YYYY-MM-DD format (e.g., 1990-05-15).",
            )

    elif field_type == "phone":
        parsed = NLParser.extract_phone(user_input)
        if parsed:
            return True, parsed, f"Got your phone: {parsed}"
        else:
            return False, None, "Please enter a valid 10-digit phone number."

    elif field_type == "email":
        parsed = NLParser.extract_email(user_input)
        if parsed:
            return True, parsed, f"Email saved: {parsed}"
        else:
            return False, None, "Please enter a valid email address."

    return False, None, "Unknown field type."
