"""
monitoring/logging_setup.py
Structured JSON logging for production.
Replaces bare print() and basic logging.basicConfig() calls.

Usage:
    from monitoring.logging_setup import get_logger
    logger = get_logger(__name__)
    logger.info("appointment_booked", patient_id="P-001", doctor="Dr. Smith")
"""
import logging
import sys
import os
import json
from datetime import datetime, timezone


class StructuredFormatter(logging.Formatter):
    """JSON log formatter for production observability."""

    SENSITIVE_KEYS = {
        "password", "api_key", "groq_api_key", "gemini_api_key",
        "openai_api_key", "insurance_member_id", "insurance_group_id",
        "patient_dob", "patient_phone", "patient_email"
    }

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add extra fields (from logger.info("msg", extra={...}))
        for key, val in record.__dict__.items():
            if key not in {
                "msg", "args", "levelname", "levelno", "pathname",
                "filename", "module", "exc_info", "exc_text", "stack_info",
                "lineno", "funcName", "created", "msecs", "relativeCreated",
                "thread", "threadName", "processName", "process", "name",
                "message", "asctime"
            }:
                # Redact sensitive fields
                if key.lower() in self.SENSITIVE_KEYS:
                    log_entry[key] = "***REDACTED***"
                else:
                    log_entry[key] = val

        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry, default=str)


def setup_logging(log_level: str = None) -> None:
    """
    Configure application-wide structured logging.
    Call once at application startup (e.g., in app/main.py).
    """
    level = log_level or os.getenv("LOG_LEVEL", "INFO")
    numeric_level = getattr(logging, level.upper(), logging.INFO)

    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # Remove existing handlers
    root_logger.handlers.clear()

    # Console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(numeric_level)

    # Use JSON in production, human-readable in dev
    if os.getenv("ENVIRONMENT", "development") == "production":
        handler.setFormatter(StructuredFormatter())
    else:
        handler.setFormatter(logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        ))

    root_logger.addHandler(handler)

    # Suppress noisy third-party loggers
    for noisy_lib in ["urllib3", "httpx", "httpcore", "streamlit", "watchdog"]:
        logging.getLogger(noisy_lib).setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a named logger. Call after setup_logging()."""
    return logging.getLogger(name)


# ── LLM Call Logger ──────────────────────────────────────────────────────────
class LLMCallLogger:
    """Tracks LLM usage for cost monitoring."""

    def __init__(self):
        self.logger = get_logger("llm.usage")
        self.total_calls = 0
        self.total_tokens_est = 0  # Estimated from response length

    def log_call(
        self,
        provider: str,
        model: str,
        prompt_len: int,
        response_len: int,
        success: bool,
        duration_ms: float,
        session_id: str = None,
    ):
        self.total_calls += 1
        # Rough token estimate: 1 token ≈ 4 chars
        tokens_est = (prompt_len + response_len) // 4
        self.total_tokens_est += tokens_est

        self.logger.info(
            "llm_call",
            extra={
                "provider": provider,
                "model": model,
                "prompt_chars": prompt_len,
                "response_chars": response_len,
                "tokens_estimate": tokens_est,
                "success": success,
                "duration_ms": round(duration_ms, 2),
                "session_id": session_id,
                "total_calls_session": self.total_calls,
            }
        )


# Singleton
_llm_call_logger = None

def get_llm_call_logger() -> LLMCallLogger:
    global _llm_call_logger
    if _llm_call_logger is None:
        _llm_call_logger = LLMCallLogger()
    return _llm_call_logger
