"""
Configuration Loader
Manages environment variables and configuration for the scheduling agent

Supports:
- API keys (Gemini, etc.)
- LLM settings
- Feature flags
- Fallback modes
"""
import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any


logger = logging.getLogger(__name__)


class Config:
    """
    Configuration management for the scheduling agent.
    Loads settings from environment variables with sensible defaults.
    """
    
    # LLM Configuration
    GEMINI_API_KEY: Optional[str] = os.getenv('GEMINI_API_KEY', None)
    LLM_ENABLED: bool = os.getenv('LLM_ENABLED', 'true').lower() == 'true'
    LLM_MODEL: str = os.getenv('LLM_MODEL', 'gemini-pro')
    LLM_TEMPERATURE: float = float(os.getenv('LLM_TEMPERATURE', '0.3'))
    LLM_MAX_TOKENS: int = int(os.getenv('LLM_MAX_TOKENS', '500'))
    LLM_TIMEOUT: int = int(os.getenv('LLM_TIMEOUT', '10'))  # seconds
    
    # Feature Flags
    USE_LLM_FOR_PARSING: bool = os.getenv('USE_LLM_FOR_PARSING', 'true').lower() == 'true'
    USE_LLM_FOR_DOCTOR_SELECTION: bool = os.getenv('USE_LLM_FOR_DOCTOR_SELECTION', 'true').lower() == 'true'
    USE_LLM_FOR_INSURANCE: bool = os.getenv('USE_LLM_FOR_INSURANCE', 'true').lower() == 'true'
    
    # Fallback Behavior
    FALLBACK_TO_RULE_BASED: bool = os.getenv('FALLBACK_TO_RULE_BASED', 'true').lower() == 'true'
    REQUIRE_LLM_SUCCESS: bool = os.getenv('REQUIRE_LLM_SUCCESS', 'false').lower() == 'true'
    
    # Logging
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    LOG_LLM_CALLS: bool = os.getenv('LOG_LLM_CALLS', 'true').lower() == 'true'
    
    @classmethod
    def is_llm_enabled(cls) -> bool:
        """
        Check if LLM is properly configured and enabled.
        
        Returns:
            True if LLM_ENABLED=true and GEMINI_API_KEY is set
        """
        if not cls.LLM_ENABLED:
            return False
        
        if not cls.GEMINI_API_KEY:
            logger.warning("LLM_ENABLED=true but GEMINI_API_KEY not set. LLM features disabled.")
            return False
        
        return True
    
    @classmethod
    def get_summary(cls) -> Dict[str, Any]:
        """
        Get a summary of configuration (safe to log, excludes sensitive data).
        
        Returns:
            Dictionary of safe config values
        """
        return {
            'LLM_ENABLED': cls.LLM_ENABLED,
            'LLM_MODEL': cls.LLM_MODEL,
            'LLM_TEMPERATURE': cls.LLM_TEMPERATURE,
            'LLM_MAX_TOKENS': cls.LLM_MAX_TOKENS,
            'LLM_TIMEOUT': cls.LLM_TIMEOUT,
            'USE_LLM_FOR_PARSING': cls.USE_LLM_FOR_PARSING,
            'USE_LLM_FOR_DOCTOR_SELECTION': cls.USE_LLM_FOR_DOCTOR_SELECTION,
            'USE_LLM_FOR_INSURANCE': cls.USE_LLM_FOR_INSURANCE,
            'FALLBACK_TO_RULE_BASED': cls.FALLBACK_TO_RULE_BASED,
            'REQUIRE_LLM_SUCCESS': cls.REQUIRE_LLM_SUCCESS,
            'GEMINI_API_KEY_SET': bool(cls.GEMINI_API_KEY),
        }
    
    @classmethod
    def validate(cls) -> tuple[bool, str]:
        """
        Validate configuration for consistency.
        
        Returns:
            Tuple of (is_valid, message)
        """
        if cls.USE_LLM_FOR_PARSING and not cls.is_llm_enabled():
            return False, "USE_LLM_FOR_PARSING=true but LLM not properly configured"
        
        if cls.REQUIRE_LLM_SUCCESS and not cls.FALLBACK_TO_RULE_BASED:
            return False, "REQUIRE_LLM_SUCCESS=true but FALLBACK_TO_RULE_BASED=false (needs fallback)"
        
        if cls.LLM_TEMPERATURE < 0 or cls.LLM_TEMPERATURE > 2:
            return False, "LLM_TEMPERATURE must be between 0 and 2"
        
        if cls.LLM_MAX_TOKENS < 100:
            return False, "LLM_MAX_TOKENS must be at least 100"
        
        return True, "Configuration valid"
    
    @classmethod
    def get_diagnostic_info(cls) -> str:
        """
        Get detailed diagnostic information about LLM configuration.
        Useful for troubleshooting issues.
        
        Returns:
            Formatted diagnostic report
        """
        lines = [
            "=" * 70,
            "LLM CONFIGURATION DIAGNOSTICS",
            "=" * 70,
        ]
        
        # Core LLM Status
        lines.append("\n[LLM Status]")
        lines.append(f"  LLM Enabled: {cls.LLM_ENABLED}")
        lines.append(f"  API Key Configured: {bool(cls.GEMINI_API_KEY)}")
        lines.append(f"  Can Use LLM: {cls.is_llm_enabled()}")
        
        # Model Settings
        lines.append("\n[Model Configuration]")
        lines.append(f"  Model Name: {cls.LLM_MODEL}")
        lines.append(f"  Temperature: {cls.LLM_TEMPERATURE} (creativity, 0-2)")
        lines.append(f"  Max Tokens: {cls.LLM_MAX_TOKENS}")
        lines.append(f"  Timeout: {cls.LLM_TIMEOUT}s")
        
        # Feature Flags
        lines.append("\n[Feature Flags]")
        lines.append(f"  Use LLM for Parsing: {cls.USE_LLM_FOR_PARSING}")
        lines.append(f"  Use LLM for Doctor Selection: {cls.USE_LLM_FOR_DOCTOR_SELECTION}")
        lines.append(f"  Use LLM for Insurance: {cls.USE_LLM_FOR_INSURANCE}")
        
        # Fallback Settings
        lines.append("\n[Fallback Behavior]")
        lines.append(f"  Fallback to Rule-Based: {cls.FALLBACK_TO_RULE_BASED}")
        lines.append(f"  Require LLM Success: {cls.REQUIRE_LLM_SUCCESS}")
        
        # Logging
        lines.append("\n[Logging]")
        lines.append(f"  Log Level: {cls.LOG_LEVEL}")
        lines.append(f"  Log LLM Calls: {cls.LOG_LLM_CALLS}")
        
        # Validation
        lines.append("\n[Validation]")
        is_valid, msg = cls.validate()
        lines.append(f"  Configuration Valid: {is_valid}")
        lines.append(f"  Message: {msg}")
        
        lines.append("\n" + "=" * 70)
        
        return "\n".join(lines)


def log_config_summary() -> None:
    """Log safe configuration summary at startup."""
    is_valid, msg = Config.validate()
    logger.info(f"Configuration validation: {msg}")
    
    if Config.is_llm_enabled():
        logger.info(f"LLM Integration Enabled: {Config.LLM_MODEL}")
    else:
        logger.info("LLM Integration Disabled or Not Configured")
    
    if Config.LOG_LEVEL == 'DEBUG':
        logger.info(f"Configuration Summary: {Config.get_summary()}")
