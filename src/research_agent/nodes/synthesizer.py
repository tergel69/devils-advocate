"""Synthesis node - combines findings into coherent research insights."""

from __future__ import annotations

import json

from langchain_core.messages import HumanMessage
from rich.console import Console

from research_agent.config import get_llm
from research_agent.prompts import SYNTHESIZER_PROMPT
from research_agent.state import AgentState

console = Console()


def synthesize_findings(state: AgentState) -> AgentState:
    """Synthesize all gathered information into coherent findings."""
    console.print("\n[bold blue]Synthesizing findings...[/bold blue]")

    sources = state.get("sources", [])
    if not sources:
        console.print("  [yellow]No sources to synthesize[/yellow]")
        errors = state.get("errors", [])
        errors.append("No sources available for synthesis")
        return {**state, "errors": errors, "status": "error"}

    findings_text = _format_findings(sources)
    sources_text = _format_sources(sources)

    llm = get_llm()
    prompt = SYNTHESIZER_PROMPT.format(
        research_question=state["research_question"],
        findings_text=findings_text,
        sources_text=sources_text,
    )

    try:
        response = llm.invoke([HumanMessage(content=prompt)])
        content = response.content
        assert isinstance(content, str)
        parsed = _parse_json_response(content)

        findings = parsed.get("synthesized_findings", [])
        gaps = parsed.get("knowledge_gaps", [])

        console.print(f"  [green]Synthesized {len(findings)} key findings[/green]")
        if gaps:
            console.print(f"  [yellow]Identified {len(gaps)} knowledge gaps[/yellow]")

        return {
            **state,
            "findings": findings,
            "status": "synthesized",
        }
    except Exception as e:
        console.print(f"[red]Synthesis error: {e}[/red]")
        errors = state.get("errors", [])
        errors.append(f"Synthesis error: {e}")
        return {**state, "errors": errors, "status": "error"}


def _format_findings(sources: list[dict]) -> str:
    """Format source findings for the synthesis prompt."""
    parts = []
    for i, source in enumerate(sources, 1):
        part = f"\n--- Source {i}: {source.get('title', 'Unknown')} ({source['url']}) ---\n"
        key_findings = source.get("key_findings", [])
        if isinstance(key_findings, list):
            for finding in key_findings:
                part += f"- {finding}\n"
        quotes = source.get("important_quotes", [])
        if isinstance(quotes, list):
            for quote in quotes:
                part += f'  Quote: "{quote}"\n'
        parts.append(part)
    return "\n".join(parts)


def _format_sources(sources: list[dict]) -> str:
    """Format source list for prompts."""
    return "\n".join(
        f"[Source {i}] {s.get('title', 'Unknown')} - {s['url']}" for i, s in enumerate(sources, 1)
    )


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
