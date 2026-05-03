"""Configuration and LLM initialization.

Supports multiple LLM providers:
- Google Gemini (default, free tier available)
- OpenAI (optional, requires pip install research-agent[openai])
"""

from __future__ import annotations

import os

from langchain_core.language_models.chat_models import BaseChatModel


def get_llm() -> BaseChatModel:
    """Get the configured LLM instance.

    Provider selection:
    - If GOOGLE_API_KEY is set, uses Google Gemini (free tier)
    - If OPENAI_API_KEY is set, uses OpenAI (requires 'openai' extra)
    - Raises an error if no API key is configured
    """
    provider = os.environ.get("LLM_PROVIDER", "").lower()

    if provider == "openai" or (not provider and os.environ.get("OPENAI_API_KEY")):
        return _get_openai_llm()

    if provider == "gemini" or (not provider and os.environ.get("GOOGLE_API_KEY")):
        return _get_gemini_llm()

    if os.environ.get("GOOGLE_API_KEY"):
        return _get_gemini_llm()

    if os.environ.get("OPENAI_API_KEY"):
        return _get_openai_llm()

    msg = (
        "No LLM API key found. Set one of:\n"
        "  GOOGLE_API_KEY  - Google Gemini (free tier, recommended)\n"
        "  OPENAI_API_KEY  - OpenAI (requires: pip install research-agent[openai])\n"
        "\nGet a free Gemini API key at: https://aistudio.google.com/apikey"
    )
    raise RuntimeError(msg)


def _get_gemini_llm() -> BaseChatModel:
    """Create a Google Gemini LLM instance."""
    from langchain_google_genai import ChatGoogleGenerativeAI

    model = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")
    return ChatGoogleGenerativeAI(
        model=model,
        temperature=0.3,
    )


def _get_openai_llm() -> BaseChatModel:
    """Create an OpenAI LLM instance."""
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
