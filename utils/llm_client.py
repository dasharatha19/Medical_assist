"""
LLM Client — Multi-provider support.
Supports: Groq, Gemini, OpenAI
Auto-selects based on LLM_PROVIDER env var.
"""
import json
import logging
import os
from typing import Dict, Any, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class LLMClient:
    """Universal LLM client supporting multiple providers."""

    def __init__(self):
        from utils.config import Config
        self.config = Config
        self.provider = Config.get_active_provider()
        self.model = Config.get_active_model()
        self.enabled = False
        self.client = None
        self._init_client()

    def _init_client(self):
        """Initialize the appropriate LLM client."""
        try:
            if self.provider == 'groq':
                from groq import Groq
                self.client = Groq(api_key=self.config.GROQ_API_KEY)
                self.enabled = True
                logger.info(f"LLM: Groq initialized with model {self.model}")

            elif self.provider == 'gemini':
                from google import genai
                self.client = genai.Client(api_key=self.config.GEMINI_API_KEY)
                self.enabled = True
                logger.info(f"LLM: Gemini initialized with model {self.model}")

            elif self.provider == 'openai':
                from openai import OpenAI
                self.client = OpenAI(api_key=self.config.OPENAI_API_KEY)
                self.enabled = True
                logger.info(f"LLM: OpenAI initialized with model {self.model}")

            else:
                logger.warning("No LLM provider configured.")
                self.enabled = False

        except ImportError as e:
            logger.error(f"LLM provider package not installed: {e}")
            self.enabled = False
        except Exception as e:
            logger.error(f"LLM client init failed: {e}")
            self.enabled = False

    def chat(self, prompt: str, system: str = "") -> Optional[str]:
        """
        Send a chat message and get response text.
        Works with any provider.
        """
        if not self.enabled or not self.client:
            return None

        try:
            if self.provider == 'groq':
                messages = []
                if system:
                    messages.append({"role": "system", "content": system})
                messages.append({"role": "user", "content": prompt})
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=self.config.LLM_TEMPERATURE,
                    max_tokens=self.config.LLM_MAX_TOKENS
                )
                return response.choices[0].message.content

            elif self.provider == 'gemini':
                full = f"{system}\n\n{prompt}" if system else prompt
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=full
                )
                return response.text

            elif self.provider == 'openai':
                messages = []
                if system:
                    messages.append({"role": "system", "content": system})
                messages.append({"role": "user", "content": prompt})
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=self.config.LLM_TEMPERATURE,
                    max_tokens=self.config.LLM_MAX_TOKENS
                )
                return response.choices[0].message.content

        except Exception as e:
            logger.error(f"LLM call failed ({self.provider}): {e}")
            return None

    def chat_json(self, prompt: str, system: str = "") -> Optional[Dict]:
        """Send prompt and parse JSON response."""
        response_text = self.chat(prompt, system)
        if not response_text:
            return None
        try:
            # Clean markdown code blocks
            text = response_text.strip()
            if "```" in text:
                parts = text.split("```")
                text = parts[1] if len(parts) > 1 else text
                if text.startswith("json"):
                    text = text[4:]
            return json.loads(text.strip())
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse failed: {e}\nResponse: {response_text[:200]}")
            return None

    def is_enabled(self) -> bool:
        return self.enabled


# Singleton
_client: Optional[LLMClient] = None


def get_llm_client() -> LLMClient:
    global _client
    if _client is None:
        _client = LLMClient()
    return _client