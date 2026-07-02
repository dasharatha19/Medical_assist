"""Configuration Loader — Multi-provider LLM support"""

import logging
import os
from typing import Any

from dotenv import load_dotenv

load_dotenv()  # ← loads .env file into os.environ BEFORE any os.getenv() calls

logger = logging.getLogger(__name__)


class Config:
    # Provider selection
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "auto")  # gemini|groq|openai|auto

    # API Keys
    GEMINI_API_KEY: str | None = os.getenv("GEMINI_API_KEY")
    GROQ_API_KEY: str | None = os.getenv("GROQ_API_KEY")
    OPENAI_API_KEY: str | None = os.getenv("OPENAI_API_KEY")
    ANTHROPIC_API_KEY: str | None = os.getenv("ANTHROPIC_API_KEY")

    # LLM Settings
    LLM_ENABLED: bool = os.getenv("LLM_ENABLED", "true").lower() == "true"
    LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0.3"))
    LLM_MAX_TOKENS: int = int(os.getenv("LLM_MAX_TOKENS", "1000"))
    LLM_TIMEOUT: int = int(os.getenv("LLM_TIMEOUT", "30"))

    # Model names per provider
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    # Feature flags
    USE_LLM_FOR_PARSING: bool = (
        os.getenv("USE_LLM_FOR_PARSING", "true").lower() == "true"
    )
    USE_LLM_FOR_DOCTOR_SELECTION: bool = (
        os.getenv("USE_LLM_FOR_DOCTOR_SELECTION", "true").lower() == "true"
    )
    USE_LLM_FOR_INSURANCE: bool = (
        os.getenv("USE_LLM_FOR_INSURANCE", "true").lower() == "true"
    )
    FALLBACK_TO_RULE_BASED: bool = (
        os.getenv("FALLBACK_TO_RULE_BASED", "true").lower() == "true"
    )
    REQUIRE_LLM_SUCCESS: bool = (
        os.getenv("REQUIRE_LLM_SUCCESS", "false").lower() == "true"
    )

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_LLM_CALLS: bool = os.getenv("LOG_LLM_CALLS", "true").lower() == "true"

    @classmethod
    def get_active_provider(cls) -> str:
        """Determine which LLM provider to use."""
        if cls.LLM_PROVIDER != "auto":
            return cls.LLM_PROVIDER
        # Auto-detect based on available keys
        if cls.GROQ_API_KEY:
            return "groq"
        if cls.GEMINI_API_KEY:
            return "gemini"
        if cls.OPENAI_API_KEY:
            return "openai"
        return "none"

    @classmethod
    def get_active_model(cls) -> str:
        provider = cls.get_active_provider()
        return {
            "groq": cls.GROQ_MODEL,
            "gemini": cls.GEMINI_MODEL,
            "openai": cls.OPENAI_MODEL,
        }.get(provider, cls.GROQ_MODEL)

    @classmethod
    def is_llm_enabled(cls) -> bool:
        if not cls.LLM_ENABLED:
            return False
        provider = cls.get_active_provider()
        if provider == "none":
            logger.warning("No LLM API key found. LLM features disabled.")
            return False
        return True

    @classmethod
    def get_summary(cls) -> dict[str, Any]:
        return {
            "provider": cls.get_active_provider(),
            "model": cls.get_active_model(),
            "llm_enabled": cls.is_llm_enabled(),
            "groq_key_set": bool(cls.GROQ_API_KEY),
            "gemini_key_set": bool(cls.GEMINI_API_KEY),
        }
