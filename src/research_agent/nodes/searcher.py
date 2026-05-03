"""Search execution node - runs web searches for each query."""

from __future__ import annotations

import os

from rich.console import Console

from research_agent.state import AgentState
from research_agent.tools.search import search_web

console = Console()


def execute_search(state: AgentState) -> AgentState:
    """Execute web searches for all pending queries."""
    console.print("\n[bold blue]Searching the web...[/bold blue]")

    queries = state.get("search_queries", [])
    existing_results = state.get("search_results", [])
    existing_urls = {r["url"] for r in existing_results}

    max_results = int(os.environ.get("MAX_SEARCH_RESULTS", "5"))

    searched_count = len(existing_results)
    new_queries = queries[searched_count:]

    all_results = list(existing_results)

    for query in new_queries:
        console.print(f"  [cyan]Searching: {query}[/cyan]")
        results = search_web(query, max_results=max_results)

        for r in results:
            if r["url"] and r["url"] not in existing_urls:
                all_results.append(r)
                existing_urls.add(r["url"])
                console.print(f"    [dim]Found: {r['title'][:80]}[/dim]")

    console.print(f"  [green]Total unique sources: {len(all_results)}[/green]")

    return {
        **state,
        "search_results": all_results,
        "status": "searched",
    }
