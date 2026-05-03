"""Configuration and LLM initialization.

Supports multiple LLM providers:
- Ollama (default, free, runs locally - no API key needed)
- Google Gemini (free tier, requires pip install research-agent[gemini])
- OpenAI (paid, requires pip install research-agent[openai])
"""

from __future__ import annotations

import os

from langchain_core.language_models.chat_models import BaseChatModel


def get_llm() -> BaseChatModel:
    """Get the configured LLM instance.

    Provider selection (in order of priority):
    1. If LLM_PROVIDER is explicitly set, uses that provider
    2. If OPENAI_API_KEY is set, uses OpenAI
    3. If GOOGLE_API_KEY is set, uses Google Gemini
    4. Falls back to Ollama (local, free, no API key)
    """
    provider = os.environ.get("LLM_PROVIDER", "").lower()

    if provider == "openai":
        return _get_openai_llm()
    if provider == "gemini":
        return _get_gemini_llm()
    if provider == "ollama":
        return _get_ollama_llm()

    if os.environ.get("OPENAI_API_KEY"):
        return _get_openai_llm()
    if os.environ.get("GOOGLE_API_KEY"):
        return _get_gemini_llm()

    return _get_ollama_llm()


def _get_ollama_llm() -> BaseChatModel:
    """Create an Ollama LLM instance (free, local)."""
    from langchain_ollama import ChatOllama

    model = os.environ.get("OLLAMA_MODEL", "qwen3:1.7b")
    base_url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
    return ChatOllama(
        model=model,
        base_url=base_url,
        temperature=0.3,
    )


def _get_gemini_llm() -> BaseChatModel:
    """Create a Google Gemini LLM instance (free tier)."""
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
    except ImportError:
        msg = (
            "Gemini provider requires the 'gemini' extra.\n"
            "Install with: pip install research-agent[gemini]"
        )
        raise RuntimeError(msg) from None

    model = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")
    return ChatGoogleGenerativeAI(
        model=model,
        temperature=0.3,
    )


def _get_openai_llm() -> BaseChatModel:
    """Create an OpenAI LLM instance (paid)."""
    try:
        from langchain_openai import ChatOpenAI
    except ImportError:
        msg = (
            "OpenAI provider requires the 'openai' extra.\n"
            "Install with: pip install research-agent[openai]"
        )
        raise RuntimeError(msg) from None

    model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
    return ChatOpenAI(
        model=model,
        temperature=0.3,
    )
