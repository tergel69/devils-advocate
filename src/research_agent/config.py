"""Configuration and LLM initialization."""

from __future__ import annotations

import os

from langchain_openai import ChatOpenAI


def get_llm() -> ChatOpenAI:
    """Get the configured LLM instance."""
    model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
    return ChatOpenAI(
        model=model,
        temperature=0.3,
    )
