"""LLM provider configuration and a provider-agnostic client.

Reads LLM_PROVIDER / MODEL_NAME / <PROVIDER>_API_KEY from the environment
(and .env, if present) and exposes two construction points, deliberately
kept separate because they return different, incompatible objects:

- get_llm(): CrewAI-facing. Returns a `crewai.LLM` instance (what
  `Agent(llm=...)` expects) when CrewAI is installed. Agent code should
  depend only on this, never on provider specifics, so swapping
  OPENAI <-> OPENROUTER never touches agent code.
- get_llm_client(): low-level. Always returns our own `LLMClient`
  (`.complete(prompt) -> str`), regardless of whether CrewAI is
  installed. Used by the standalone connectivity check and anything
  else that wants a plain, provider-agnostic completion call rather
  than a CrewAI-specific object.
"""

import os
from dataclasses import dataclass, field
from typing import Literal, Optional

import requests
from dotenv import load_dotenv

load_dotenv()

LLMProvider = Literal["openai", "openrouter"]

_PROVIDER_BASE_URLS: dict[str, str] = {
    "openai": "https://api.openai.com/v1",
    "openrouter": "https://openrouter.ai/api/v1",
}

_PROVIDER_API_KEY_ENV: dict[str, str] = {
    "openai": "OPENAI_API_KEY",
    "openrouter": "OPENROUTER_API_KEY",
}


class LLMConfigError(RuntimeError):
    """Raised when LLM_PROVIDER / MODEL_NAME / the provider's API key cannot be resolved."""


class LLMRequestError(RuntimeError):
    """Raised when a request to the configured LLM provider fails or returns no content."""


def _scrub(text: str, secret: Optional[str]) -> str:
    if not secret:
        return text
    return text.replace(secret, "***REDACTED***")


@dataclass(frozen=True)
class LLMConfig:
    provider: LLMProvider
    model: str
    api_key: str = field(repr=False)
    base_url: str


def load_llm_config() -> LLMConfig:
    """Resolve and validate the configured provider/model/API key from the environment."""
    provider_raw = os.getenv("LLM_PROVIDER")
    if not provider_raw or not provider_raw.strip():
        raise LLMConfigError(
            "LLM_PROVIDER is not set. Set it to one of: "
            f"{', '.join(sorted(_PROVIDER_BASE_URLS))}."
        )

    provider = provider_raw.strip().lower()
    if provider not in _PROVIDER_BASE_URLS:
        raise LLMConfigError(
            f"Unsupported LLM_PROVIDER '{provider}'. Supported providers: "
            f"{', '.join(sorted(_PROVIDER_BASE_URLS))}."
        )

    model = os.getenv("MODEL_NAME")
    if not model or not model.strip():
        raise LLMConfigError("MODEL_NAME is not set.")

    api_key_env = _PROVIDER_API_KEY_ENV[provider]
    api_key = os.getenv(api_key_env)
    if not api_key or not api_key.strip():
        raise LLMConfigError(f"{api_key_env} is not set for LLM_PROVIDER='{provider}'.")

    return LLMConfig(
        provider=provider,  # type: ignore[arg-type]
        model=model.strip(),
        api_key=api_key,
        base_url=_PROVIDER_BASE_URLS[provider],
    )


class LLMClient:
    """Minimal OpenAI-compatible chat-completions client, provider-agnostic by construction."""

    def __init__(self, config: LLMConfig):
        self._config = config

    def complete(self, prompt: str, *, max_tokens: int = 16, timeout: float = 30.0) -> str:
        """Send a single user prompt and return the model's text response."""
        url = f"{self._config.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self._config.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self._config.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
        }

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=timeout)
        except requests.RequestException as exc:
            message = _scrub(str(exc), self._config.api_key)
            raise LLMRequestError(
                f"Request to {self._config.provider} ({self._config.model}) failed: {message}"
            ) from None

        if response.status_code != 200:
            body = _scrub(response.text, self._config.api_key)[:500]
            raise LLMRequestError(
                f"{self._config.provider} request failed with HTTP {response.status_code}: {body}"
            )

        try:
            data = response.json()
            content = data["choices"][0]["message"]["content"]
        except (ValueError, KeyError, IndexError, TypeError):
            raise LLMRequestError(
                f"Unexpected response shape from {self._config.provider}."
            ) from None

        if not content or not content.strip():
            raise LLMRequestError(f"{self._config.provider} returned an empty response.")

        return content


def get_llm(config: Optional[LLMConfig] = None):
    """CrewAI-facing helper that constructs the configured LLM.

    Returns a `crewai.LLM` instance when CrewAI is installed (what
    `Agent(llm=...)` expects), otherwise falls back to the same `LLMClient`
    `get_llm_client()` returns. Agent code should call only this function
    and never inspect LLM_PROVIDER / MODEL_NAME / API keys directly, so it
    never needs to know whether the backend is OpenAI or OpenRouter.

    The object this returns is CrewAI-specific (e.g. exposes `.call(...)`,
    not `.complete(...)`) — for a plain provider-agnostic completion call,
    use `get_llm_client()` instead.
    """
    config = config or load_llm_config()

    try:
        from crewai import LLM as CrewAILLM
    except ImportError:
        return LLMClient(config)

    return CrewAILLM(model=f"{config.provider}/{config.model}", api_key=config.api_key, base_url=config.base_url)


def get_llm_client(config: Optional[LLMConfig] = None) -> LLMClient:
    """Low-level helper that always returns our own provider-agnostic
    `LLMClient` (`.complete(prompt) -> str`), regardless of whether CrewAI
    is installed.

    Use this — not `get_llm()` — for anything that wants a plain
    completion call rather than a CrewAI-specific object: the standalone
    connectivity check, scripts, or any future non-CrewAI LLM usage.
    """
    return LLMClient(config or load_llm_config())
