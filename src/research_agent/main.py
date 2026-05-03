"""CLI entry point for the autonomous research agent."""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from research_agent.agent import create_agent
from research_agent.state import AgentState

console = Console()


def save_report(report: str, question: str, output_dir: str) -> str:
    """Save the research report to a markdown file."""
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(tz=timezone.utc).strftime("%Y%m%d_%H%M%S")
    safe_name = "".join(c if c.isalnum() or c in " -_" else "" for c in question[:50]).strip()
    safe_name = safe_name.replace(" ", "_").lower()
    filename = f"{timestamp}_{safe_name}.md"

    filepath = out_path / filename
    filepath.write_text(report, encoding="utf-8")
    return str(filepath)


def run_research(
    question: str,
    max_iterations: int = 2,
    output_dir: str = "reports",
) -> str | None:
    """Run the research agent on a question and return the report."""
    console.print(
        Panel(
            Text(question, style="bold white"),
            title="[bold green]Research Question[/bold green]",
            border_style="green",
        )
    )

    agent = create_agent()

    initial_state: AgentState = {
        "research_question": question,
        "sub_questions": [],
        "search_queries": [],
        "search_results": [],
        "sources": [],
        "findings": [],
        "report": "",
        "iteration": 0,
        "max_iterations": max_iterations,
        "status": "starting",
        "errors": [],
    }

    console.print("\n[bold]Starting research workflow...[/bold]\n")

    final_state: AgentState | None = None
    for step in agent.stream(initial_state):
        for node_name, node_state in step.items():
            final_state = node_state
            status = node_state.get("status", "unknown")
            console.print(f"  [dim]Step: {node_name} -> {status}[/dim]")

    if final_state is None:
        console.print("[red]Research agent produced no output[/red]")
        return None

    report = final_state.get("report", "")
    errors = final_state.get("errors", [])

    if errors:
        console.print("\n[yellow]Warnings/Errors encountered:[/yellow]")
        for error in errors:
            console.print(f"  [yellow]- {error}[/yellow]")

    if report:
        filepath = save_report(report, question, output_dir)
        console.print(f"\n[bold green]Report saved to: {filepath}[/bold green]")

        sources = final_state.get("sources", [])
        console.print(
            Panel(
                f"Sources analyzed: {len(sources)}\n"
                f"Iterations: {final_state.get('iteration', 0)}\n"
                f"Report length: {len(report)} characters",
                title="[bold]Research Summary[/bold]",
                border_style="blue",
            )
        )
        return report

    console.print("[red]No report was generated. Check errors above.[/red]")
    return None


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Autonomous Research Agent - Search, analyze, and synthesize research reports.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  research-agent "Latest trends in quantum computing startups"
  research-agent "Impact of AI on healthcare diagnostics" --iterations 3
  research-agent "Comparison of Rust vs Go for web services" -o ./my-reports
        """,
    )
    parser.add_argument("question", help="The research question to investigate")
    parser.add_argument(
        "--iterations",
        "-i",
        type=int,
        default=2,
        help="Maximum research iterations for quality improvement (default: 2)",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default="reports",
        help="Output directory for reports (default: reports/)",
    )

    args = parser.parse_args()

    load_dotenv()

    llm_provider = os.environ.get("LLM_PROVIDER", "").lower()
    if llm_provider == "openai":
        provider_label = "OpenAI"
    elif llm_provider == "gemini":
        provider_label = "Gemini"
    elif os.environ.get("OPENAI_API_KEY"):
        provider_label = "OpenAI"
    elif os.environ.get("GOOGLE_API_KEY"):
        provider_label = "Gemini"
    else:
        provider_label = "Ollama (Local)"

    console.print(
        Panel(
            f"[bold]Autonomous Research Agent[/bold]\nPowered by LangGraph + {provider_label}",
            border_style="bright_blue",
        )
    )

    report = run_research(
        question=args.question,
        max_iterations=args.iterations,
        output_dir=args.output,
    )

    if not report:
        sys.exit(1)


if __name__ == "__main__":
    main()
