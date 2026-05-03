"""Agent state definitions for the research workflow."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TypedDict


@dataclass
class Source:
    """A web source with its extracted content."""

    url: str
    title: str
    snippet: str
    content: str = ""
    relevance_score: float = 0.0


@dataclass
class SearchResult:
    """A single search result."""

    title: str
    url: str
    snippet: str


@dataclass
class ResearchFinding:
    """A synthesized finding with supporting sources."""

    claim: str
    evidence: str
    source_urls: list[str] = field(default_factory=list)


class AgentState(TypedDict, total=False):
    """State passed between nodes in the LangGraph research workflow."""

    research_question: str
    sub_questions: list[str]
    search_queries: list[str]
    search_results: list[dict[str, str]]
    sources: list[dict[str, str]]
    findings: list[dict[str, str | list[str]]]
    report: str
    iteration: int
    max_iterations: int
    status: str
    errors: list[str]
