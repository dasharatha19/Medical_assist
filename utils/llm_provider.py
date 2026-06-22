"""
Universal LLM Provider
Auto-detects available API keys and uses the right provider.
Set LLM_PROVIDER=auto in .env to auto-detect, or force a specific one.
"""

import logging
import os

logger = logging.getLogger(__name__)


class LLMProvider:
    """Universal LLM provider — works with Gemini, Groq, OpenAI, Anthropic."""

    def __init__(self):
        self.provider = None
        self.client = None
        self.model = None
        self.enabled = False
        self._initialize()

    def _initialize(self):
        """Auto-detect or use forced provider from env."""
        forced = os.getenv("LLM_PROVIDER", "auto").lower()

        if forced == "auto":
            # Try in order: Groq → Gemini → OpenAI → Anthropic
            for provider in ["groq", "gemini", "openai", "anthropic"]:
                if self._try_init(provider):
                    break
        else:
            self._try_init(forced)

        if self.enabled:
            logger.info(f"✅ LLM Provider: {self.provider} ({self.model})")
        else:
            logger.warning("⚠️ No LLM provider available — using rule-based fallback")

    def _try_init(self, provider: str) -> bool:
        """Try to initialize a specific provider."""
        try:
            if provider == "groq":
                api_key = os.getenv("GROQ_API_KEY")
                if not api_key:
                    return False
                from groq import Groq

                self.client = Groq(api_key=api_key)
                self.provider = "groq"
                self.model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
                self.enabled = True
                return True

            elif provider == "gemini":
                api_key = os.getenv("GEMINI_API_KEY")
                if not api_key:
                    return False
                from google import genai

                self.client = genai.Client(api_key=api_key)
                self.provider = "gemini"
                self.model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
                self.enabled = True
                return True

            elif provider == "openai":
                api_key = os.getenv("OPENAI_API_KEY")
                if not api_key:
                    return False
                from openai import OpenAI

                self.client = OpenAI(api_key=api_key)
                self.provider = "openai"
                self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
                self.enabled = True
                return True

            elif provider == "anthropic":
                api_key = os.getenv("ANTHROPIC_API_KEY")
                if not api_key:
                    return False
                import anthropic

                self.client = anthropic.Anthropic(api_key=api_key)
                self.provider = "anthropic"
                self.model = os.getenv("ANTHROPIC_MODEL", "claude-3-5-haiku-20241022")
                self.enabled = True
                return True

        except ImportError as e:
            logger.debug(f"{provider} package not installed: {e}")
        except Exception as e:
            logger.debug(f"{provider} init failed: {e}")

        return False

    def generate(self, prompt: str, max_tokens: int = 1000) -> str | None:
        """Generate text using whichever provider is active."""
        if not self.enabled:
            return None

        try:
            if self.provider == "groq":
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=max_tokens,
                    temperature=0.3,
                )
                return response.choices[0].message.content

            elif self.provider == "gemini":
                response = self.client.models.generate_content(model=self.model, contents=prompt)
                return response.text

            elif self.provider == "openai":
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=max_tokens,
                    temperature=0.3,
                )
                return response.choices[0].message.content

            elif self.provider == "anthropic":
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=max_tokens,
                    messages=[{"role": "user", "content": prompt}],
                )
                return response.content[0].text

        except Exception as e:
            logger.error(f"LLM generation failed ({self.provider}): {e}")
            return None

    def is_enabled(self) -> bool:
        return self.enabled


# Singleton
_provider_instance: LLMProvider | None = None


def get_llm_provider() -> LLMProvider:
    global _provider_instance
    if _provider_instance is None:
        _provider_instance = LLMProvider()
    return _provider_instance
