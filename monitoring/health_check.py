"""
monitoring/health_check.py
Health check utilities for MediBook.
Checks DB connectivity, LLM availability, and config validity.

Can be called from:
  - A background thread in the Streamlit app
  - A FastAPI /health endpoint (if added later)
  - A CLI script: python -m monitoring.health_check
"""

import logging
import os
import time
from typing import Any

logger = logging.getLogger(__name__)


def check_database() -> dict[str, Any]:
    """Check PostgreSQL connectivity."""
    start = time.time()
    try:
        from database.db import get_connection

        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.close()
        conn.close()
        return {
            "status": "healthy",
            "latency_ms": round((time.time() - start) * 1000, 2),
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "latency_ms": round((time.time() - start) * 1000, 2),
        }


def check_llm() -> dict[str, Any]:
    """Check LLM client initialization."""
    start = time.time()
    try:
        from utils.llm_client import get_llm_client

        client = get_llm_client()
        return {
            "status": "healthy" if client.is_enabled() else "disabled",
            "provider": client.provider,
            "model": client.model,
            "latency_ms": round((time.time() - start) * 1000, 2),
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "latency_ms": round((time.time() - start) * 1000, 2),
        }


def check_config() -> dict[str, Any]:
    """Validate essential configuration."""
    issues = []
    try:
        from utils.config import Config

        if not Config.GROQ_API_KEY and not Config.GEMINI_API_KEY and not Config.OPENAI_API_KEY:
            issues.append("No LLM API key configured")

        db_url = os.getenv("DATABASE_URL") or os.getenv("DB_HOST")
        if not db_url:
            issues.append("No database configuration found")

        return {
            "status": "healthy" if not issues else "degraded",
            "issues": issues,
            "provider": Config.get_active_provider(),
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


def full_health_check() -> dict[str, Any]:
    """Run all health checks and return combined status."""
    results = {
        "database": check_database(),
        "llm": check_llm(),
        "config": check_config(),
    }

    # Overall status: healthy only if all are healthy/disabled
    statuses = [v["status"] for v in results.values()]
    if "unhealthy" in statuses:
        overall = "unhealthy"
    elif "degraded" in statuses:
        overall = "degraded"
    else:
        overall = "healthy"

    return {
        "status": overall,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "checks": results,
    }


if __name__ == "__main__":
    import json

    result = full_health_check()
    print(json.dumps(result, indent=2))
    exit(0 if result["status"] in ("healthy", "degraded") else 1)
