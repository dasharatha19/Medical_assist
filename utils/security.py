"""
utils/security.py
Security utilities for MediBook.

Covers:
  - Prompt injection detection and sanitization
  - Input length limits
  - PII redaction for logs
"""

import logging
import re

logger = logging.getLogger(__name__)

# ── Prompt Injection Patterns ─────────────────────────────────────────────────
_INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?previous\s+instructions",
    r"forget\s+(everything|all|your\s+instructions)",
    r"you\s+are\s+now\s+(a|an)",
    r"act\s+as\s+(a|an|if)",
    r"pretend\s+(you\s+are|to\s+be)",
    r"jailbreak",
    r"DAN\b",  # "Do Anything Now" jailbreak
    r"<\s*script",  # XSS attempt
    r"system\s*prompt",
    r"reveal\s+(your\s+)?(system\s+)?prompt",
    r"repeat\s+everything\s+above",
    r"output\s+your\s+(full\s+)?instructions",
]

_COMPILED_PATTERNS = [re.compile(p, re.IGNORECASE) for p in _INJECTION_PATTERNS]

MAX_INPUT_LENGTH = 1000  # Characters — reasonable for a scheduling chatbot


def sanitize_user_input(text: str) -> tuple[str, bool]:
    """
    Sanitize user input. Returns (sanitized_text, was_flagged).

    Steps:
    1. Length truncation
    2. Strip control characters
    3. Detect prompt injection attempts
    4. Strip HTML/script tags

    Returns the original text (truncated/cleaned) and a flag if injection was detected.
    """
    if not text:
        return "", False

    # 1. Truncate
    if len(text) > MAX_INPUT_LENGTH:
        logger.warning(f"Input truncated from {len(text)} to {MAX_INPUT_LENGTH} chars")
        text = text[:MAX_INPUT_LENGTH]

    # 2. Strip control characters (except newlines which are valid)
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)

    # 3. Strip HTML/script tags
    text = re.sub(r"<[^>]+>", "", text)

    # 4. Check for injection patterns
    flagged = False
    for pattern in _COMPILED_PATTERNS:
        if pattern.search(text):
            logger.warning(
                "Potential prompt injection detected",
                extra={"pattern": pattern.pattern, "input_snippet": text[:100]},
            )
            flagged = True
            break

    return text.strip(), flagged


def redact_pii_for_log(data: dict) -> dict:
    """
    Return a copy of dict with PII fields redacted.
    Safe to pass to loggers.
    """
    REDACT_FIELDS = {
        "patient_email",
        "patient_phone",
        "patient_dob",
        "insurance_member_id",
        "insurance_group_id",
        "patient_id",
        "groq_api_key",
        "gemini_api_key",
        "openai_api_key",
        "api_key",
        "password",
    }
    return {k: "***" if k in REDACT_FIELDS else v for k, v in data.items()}


def validate_api_key_format(key: str, provider: str) -> bool:
    """Basic format validation for API keys (not cryptographic)."""
    if not key:
        return False
    patterns = {
        "groq": r"^gsk_[a-zA-Z0-9]{40,}$",
        "gemini": r"^AIza[a-zA-Z0-9_\-]{35}$",
        "openai": r"^sk-[a-zA-Z0-9]{48}$",
    }
    pattern = patterns.get(provider)
    if not pattern:
        return len(key) > 10  # Minimal check for unknown providers
    return bool(re.match(pattern, key))
