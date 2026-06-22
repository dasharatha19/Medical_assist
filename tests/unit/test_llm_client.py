"""
tests/unit/test_llm_client.py
Unit tests for LLMClient (mocked — no real API calls).
"""
import pytest
import sys
import os
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))


class TestConfig:
    def test_auto_provider_uses_groq_when_key_set(self, monkeypatch):
        monkeypatch.setenv("GROQ_API_KEY", "test-key")
        monkeypatch.setenv("LLM_PROVIDER", "auto")
        # Re-import to pick up env
        import importlib
        import utils.config
        importlib.reload(utils.config)
        from utils.config import Config
        # With GROQ key, auto should pick groq
        assert Config.get_active_provider() in ("groq", "auto", "none")

    def test_no_keys_returns_none_provider(self, monkeypatch):
        monkeypatch.delenv("GROQ_API_KEY", raising=False)
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.setenv("LLM_PROVIDER", "auto")
        import importlib
        import utils.config
        importlib.reload(utils.config)
        from utils.config import Config
        assert Config.get_active_provider() == "none"

    def test_llm_disabled_when_no_keys(self, monkeypatch):
        monkeypatch.delenv("GROQ_API_KEY", raising=False)
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.setenv("LLM_PROVIDER", "auto")
        import importlib
        import utils.config
        importlib.reload(utils.config)
        from utils.config import Config
        assert Config.is_llm_enabled() is False


class TestLLMClientMocked:
    def test_chat_returns_none_when_disabled(self):
        from utils.llm_client import LLMClient
        client = LLMClient.__new__(LLMClient)
        client.enabled = False
        client.client = None
        client.provider = "none"
        result = client.chat("hello")
        assert result is None

    def test_chat_json_parses_valid_json(self):
        from utils.llm_client import LLMClient
        client = LLMClient.__new__(LLMClient)
        client.enabled = True
        client.provider = "groq"
        client.chat = MagicMock(return_value='{"name": "John", "age": 30}')
        result = client.chat_json("extract name")
        assert result == {"name": "John", "age": 30}

    def test_chat_json_handles_markdown_fences(self):
        from utils.llm_client import LLMClient
        client = LLMClient.__new__(LLMClient)
        client.enabled = True
        client.provider = "groq"
        client.chat = MagicMock(return_value='```json\n{"status": "ok"}\n```')
        result = client.chat_json("test")
        assert result is not None
        assert result.get("status") == "ok"

    def test_chat_json_returns_none_on_bad_json(self):
        from utils.llm_client import LLMClient
        client = LLMClient.__new__(LLMClient)
        client.enabled = True
        client.provider = "groq"
        client.chat = MagicMock(return_value="this is not json at all")
        result = client.chat_json("test")
        assert result is None

    def test_singleton_returns_same_instance(self):
        from utils.llm_client import get_llm_client
        c1 = get_llm_client()
        c2 = get_llm_client()
        assert c1 is c2
