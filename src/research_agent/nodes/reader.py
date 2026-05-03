"""Content reading node - extracts and analyzes content from web pages."""

from __future__ import annotations

import json
import os

from langchain_core.messages import HumanMessage
from rich.console import Console

from research_agent.config import get_llm
from research_agent.prompts import READER_PROMPT
from research_agent.state import AgentState
from research_agent.tools.scraper import extract_content

console = Console()


def read_sources(state: AgentState) -> AgentState:
    """Read and analyze content from search results."""
    console.print("\n[bold blue]Reading and analyzing sources...[/bold blue]")

    search_results = state.get("search_results", [])
    existing_sources = state.get("sources", [])
    existing_urls = {s["url"] for s in existing_sources}

    max_pages = int(os.environ.get("MAX_PAGES_TO_READ", "3"))

    candidates = [r for r in search_results if r["url"] not in existing_urls]
    to_read = candidates[:max_pages]

    llm = get_llm()
    new_sources = list(existing_sources)

    for result in to_read:
        url = result["url"]
        console.print(f"  [cyan]Reading: {url}[/cyan]")

        extracted = extract_content(url)
        if extracted["success"] != "true":
            console.print("    [yellow]Skipped (extraction failed)[/yellow]")
            continue

        analysis = _analyze_content(
            llm,
            extracted["content"],
            url,
            state["research_question"],
            state.get("sub_questions", []),
        )

        if analysis and analysis.get("relevance_score", 0) > 0.3:
            source = {
                "url": url,
                "title": extracted["title"],
                "content": extracted["content"][:5000],
                "key_findings": analysis.get("key_findings", []),
                "important_quotes": analysis.get("important_quotes", []),
                "relevance_score": analysis.get("relevance_score", 0),
            }
            new_sources.append(source)
            console.print(f"    [green]Relevant (score: {analysis['relevance_score']:.1f})[/green]")
        else:
            console.print("    [dim]Low relevance, skipped[/dim]")

    console.print(f"  [green]Total analyzed sources: {len(new_sources)}[/green]")

    return {
        **state,
        "sources": new_sources,
        "status": "read",
    }


def _analyze_content(
    llm, content: str, url: str, research_question: str, sub_questions: list[str]
) -> dict | None:
    """Use LLM to analyze content relevance and extract key findings."""
    try:
        prompt = READER_PROMPT.format(
            research_question=research_question,
            sub_questions=json.dumps(sub_questions),
            url=url,
            content=content[:8000],
        )
        response = llm.invoke([HumanMessage(content=prompt)])
        response_text = response.content
        assert isinstance(response_text, str)
        return _parse_json_response(response_text)
    except Exception as e:
        console.print(f"    [yellow]Analysis error: {e}[/yellow]")
        return None


def _parse_json_response(content: str) -> dict:
    """Parse JSON from LLM response."""
    content = content.strip()
    if content.startswith("```"):
        lines = content.split("\n")
        json_lines = []
        in_block = False
        for line in lines:
            if line.startswith("```") and not in_block:
                in_block = True
                continue
            elif line.startswith("```") and in_block:
                break
            elif in_block:
                json_lines.append(line)
        content = "\n".join(json_lines)
    return json.loads(content)
