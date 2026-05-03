"""Web search tool using DuckDuckGo (free, no API key) with optional Tavily support."""

from __future__ import annotations

import os
from typing import Any

from rich.console import Console

console = Console()


def search_duckduckgo(query: str, max_results: int = 5) -> list[dict[str, str]]:
    """Search the web using DuckDuckGo."""
    from duckduckgo_search import DDGS

    results: list[dict[str, str]] = []
    try:
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                results.append(
                    {
                        "title": r.get("title", ""),
                        "url": r.get("href", r.get("link", "")),
                        "snippet": r.get("body", r.get("snippet", "")),
                    }
                )
    except Exception as e:
        console.print(f"[yellow]DuckDuckGo search error: {e}[/yellow]")
    return results


def search_tavily(query: str, max_results: int = 5) -> list[dict[str, str]]:
    """Search the web using Tavily API (requires TAVILY_API_KEY)."""
    try:
        from langchain_community.tools.tavily_search import TavilySearchResults

        tool = TavilySearchResults(max_results=max_results)
        raw_results: Any = tool.invoke(query)

        results: list[dict[str, str]] = []
        if isinstance(raw_results, list):
            for r in raw_results:
                if isinstance(r, dict):
                    results.append(
                        {
                            "title": r.get("title", ""),
                            "url": r.get("url", ""),
                            "snippet": r.get("content", ""),
                        }
                    )
        return results
    except Exception as e:
        console.print(f"[yellow]Tavily search error: {e}, falling back to DuckDuckGo[/yellow]")
        return search_duckduckgo(query, max_results)


def search_web(query: str, max_results: int = 5) -> list[dict[str, str]]:
    """Search the web using the best available search provider.

    Uses Tavily if TAVILY_API_KEY is set, otherwise falls back to DuckDuckGo.

    Args:
        query: The search query string.
        max_results: Maximum number of results to return.

    Returns:
        List of search result dicts with 'title', 'url', and 'snippet' keys.
    """
    if os.environ.get("TAVILY_API_KEY"):
        return search_tavily(query, max_results)
    return search_duckduckgo(query, max_results)
