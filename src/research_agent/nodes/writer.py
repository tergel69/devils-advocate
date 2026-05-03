"""Report writing node - generates the final structured research report."""

from __future__ import annotations

import json

from langchain_core.messages import HumanMessage
from rich.console import Console

from research_agent.config import get_llm
from research_agent.prompts import REVIEWER_PROMPT, WRITER_PROMPT
from research_agent.state import AgentState

console = Console()


def write_report(state: AgentState) -> AgentState:
    """Generate the final research report."""
    console.print("\n[bold blue]Writing research report...[/bold blue]")

    findings = state.get("findings", [])
    sources = state.get("sources", [])

    if not findings:
        console.print("  [yellow]No findings to write about[/yellow]")
        errors = state.get("errors", [])
        errors.append("No findings available for report writing")
        return {**state, "errors": errors, "status": "error"}

    findings_text = _format_findings_for_report(findings)
    sources_text = _format_sources_for_report(sources)

    llm = get_llm()
    prompt = WRITER_PROMPT.format(
        research_question=state["research_question"],
        findings_text=findings_text,
        sources_text=sources_text,
    )

    response = llm.invoke([HumanMessage(content=prompt)])
    report = response.content
    assert isinstance(report, str)

    console.print("  [green]Draft report generated[/green]")

    quality = _review_report(llm, state["research_question"], report)

    iteration = state.get("iteration", 0) + 1
    max_iterations = state.get("max_iterations", 2)

    if quality and not quality.get("is_sufficient", True) and iteration < max_iterations:
        console.print(
            f"  [yellow]Report needs improvement (score: {quality.get('quality_score', 'N/A')})"
            f", iteration {iteration}/{max_iterations}[/yellow]"
        )
        return {
            **state,
            "report": report,
            "iteration": iteration,
            "status": "needs_improvement",
        }

    console.print(
        f"  [green]Report finalized"
        f" (quality: {quality.get('quality_score', 'N/A') if quality else 'N/A'})[/green]"
    )

    return {
        **state,
        "report": report,
        "iteration": iteration,
        "status": "complete",
    }


def _review_report(llm, research_question: str, report: str) -> dict | None:
    """Use LLM to review report quality."""
    try:
        prompt = REVIEWER_PROMPT.format(
            research_question=research_question,
            report=report,
        )
        response = llm.invoke([HumanMessage(content=prompt)])
        content = response.content
        assert isinstance(content, str)
        return _parse_json_response(content)
    except Exception as e:
        console.print(f"  [yellow]Review error: {e}[/yellow]")
        return None


def _format_findings_for_report(findings: list[dict]) -> str:
    """Format synthesized findings for the report writer."""
    parts = []
    for i, finding in enumerate(findings, 1):
        part = f"\nFinding {i}:\n"
        part += f"  Claim: {finding.get('claim', '')}\n"
        part += f"  Evidence: {finding.get('evidence', '')}\n"
        source_urls = finding.get("source_urls", [])
        if source_urls:
            part += f"  Sources: {', '.join(source_urls)}\n"
        parts.append(part)
    return "\n".join(parts)


def _format_sources_for_report(sources: list[dict]) -> str:
    """Format sources for the report writer."""
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
