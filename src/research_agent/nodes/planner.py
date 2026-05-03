"""Research planning node - breaks down questions into search queries."""

from __future__ import annotations

import json

from langchain_core.messages import HumanMessage
from rich.console import Console

from research_agent.config import get_llm
from research_agent.prompts import PLANNER_PROMPT
from research_agent.state import AgentState

console = Console()


def plan_research(state: AgentState) -> AgentState:
    """Break down the research question into sub-questions and search queries."""
    console.print("\n[bold blue]Planning research strategy...[/bold blue]")

    llm = get_llm()
    previous_queries = state.get("search_queries", [])

    prompt = PLANNER_PROMPT.format(
        research_question=state["research_question"],
        previous_queries=json.dumps(previous_queries) if previous_queries else "None",
    )

    response = llm.invoke([HumanMessage(content=prompt)])
    content = response.content
    assert isinstance(content, str)

    try:
        parsed = _parse_json_response(content)
        sub_questions: list[str] = parsed.get("sub_questions", [])
        new_queries: list[str] = parsed.get("search_queries", [])

        console.print(f"  [green]Generated {len(sub_questions)} sub-questions[/green]")
        for sq in sub_questions:
            console.print(f"    - {sq}")
        console.print(f"  [green]Generated {len(new_queries)} search queries[/green]")

        all_queries = previous_queries + new_queries

        return {
            **state,
            "sub_questions": sub_questions,
            "search_queries": all_queries,
            "status": "planned",
        }
    except Exception as e:
        console.print(f"[red]Planning error: {e}[/red]")
        errors = state.get("errors", [])
        errors.append(f"Planning error: {e}")
        return {**state, "errors": errors, "status": "error"}


def _parse_json_response(content: str) -> dict:
    """Parse JSON from LLM response, handling markdown code blocks."""
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
