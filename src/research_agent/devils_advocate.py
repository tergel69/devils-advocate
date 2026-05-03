"""Devil's Advocate engine.

Analyzes an article's arguments and generates well-sourced counter-arguments
using LLM reasoning and web search for counter-evidence.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field

from langchain_core.messages import HumanMessage, SystemMessage

from research_agent.config import get_llm
from research_agent.tools.scraper import extract_content
from research_agent.tools.search import search_web

MAX_ARTICLE_LENGTH = 12000
MAX_SOURCES_TO_READ = 5


@dataclass
class CounterArgument:
    """A single counter-argument with supporting evidence."""

    title: str
    argument: str
    evidence: str
    source_urls: list[str] = field(default_factory=list)


@dataclass
class AnalysisResult:
    """Complete Devil's Advocate analysis result."""

    original_summary: str
    original_claims: list[str]
    counter_arguments: list[CounterArgument]
    sources: list[dict[str, str]]
    bias_assessment: dict[str, object]


def _parse_json_response(text: str) -> dict:
    """Extract JSON from an LLM response that may contain markdown fences."""
    text = text.strip()
    # Remove <think>...</think> blocks (some models like qwen3 emit these)
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()
    fence = re.search(r"```(?:json)?\s*\n?(.*?)```", text, re.DOTALL)
    if fence:
        text = fence.group(1).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        brace = text.find("{")
        bracket = text.find("[")
        if brace == -1 and bracket == -1:
            return {}
        start = min(p for p in (brace, bracket) if p >= 0)
        return json.loads(text[start:])


def analyze_article(title: str, url: str, text: str) -> AnalysisResult:
    """Run the full Devil's Advocate pipeline on an article.

    Steps:
    1. Summarize the article and extract main claims
    2. Generate counter-search queries
    3. Search for counter-evidence
    4. Read and analyze counter-sources
    5. Synthesize counter-arguments
    6. Assess bias/balance
    """
    if len(text) > MAX_ARTICLE_LENGTH:
        text = text[:MAX_ARTICLE_LENGTH]

    llm = get_llm()

    # Step 1: Extract claims
    claims_data = _extract_claims(llm, title, text)
    summary = claims_data.get("summary", "")
    claims = claims_data.get("claims", [])

    # Step 2: Generate counter-search queries
    search_queries = _generate_counter_queries(llm, summary, claims)

    # Step 3: Search for counter-evidence
    all_search_results: list[dict[str, str]] = []
    for query in search_queries[:6]:
        results = search_web(query, max_results=3)
        all_search_results.extend(results)

    # Deduplicate by URL
    seen_urls: set[str] = set()
    unique_results: list[dict[str, str]] = []
    for r in all_search_results:
        if r["url"] and r["url"] not in seen_urls:
            seen_urls.add(r["url"])
            unique_results.append(r)

    # Step 4: Read top sources
    source_contents: list[dict[str, str]] = []
    for result in unique_results[:MAX_SOURCES_TO_READ]:
        content = extract_content(result["url"])
        if content.get("success") == "true":
            source_contents.append(
                {
                    "url": result["url"],
                    "title": content.get("title", result.get("title", "")),
                    "content": content.get("content", "")[:5000],
                }
            )

    # Step 5: Synthesize counter-arguments
    counter_args = _synthesize_counter_arguments(llm, summary, claims, source_contents)

    # Step 6: Bias assessment
    bias = _assess_bias(llm, summary, claims, counter_args)

    # Build sources list
    sources = [{"url": s["url"], "title": s["title"]} for s in source_contents]

    return AnalysisResult(
        original_summary=summary,
        original_claims=claims,
        counter_arguments=[
            CounterArgument(
                title=ca.get("title", "Counter-point"),
                argument=ca.get("argument", ""),
                evidence=ca.get("evidence", ""),
                source_urls=ca.get("source_urls", []),
            )
            for ca in counter_args
        ],
        sources=sources,
        bias_assessment=bias,
    )


def _extract_claims(llm, title: str, text: str) -> dict:
    """Extract the main claims and summary from an article."""
    messages = [
        SystemMessage(
            content=(
                "You are an expert argument analyst. Analyze the article and extract its "
                "main thesis and key claims. Be objective and precise."
            )
        ),
        HumanMessage(
            content=f"""Analyze this article and extract its main argument and key claims.

Title: {title}

Article text:
{text}

Respond in JSON format:
{{
    "summary": "A 2-3 sentence objective summary of the article's main argument",
    "claims": ["claim 1", "claim 2", "claim 3", ...]
}}

Extract 3-6 specific, arguable claims the author makes. Focus on claims that are debatable, not pure facts."""
        ),
    ]
    response = llm.invoke(messages)
    return _parse_json_response(response.content)


def _generate_counter_queries(llm, summary: str, claims: list[str]) -> list[str]:
    """Generate search queries to find counter-evidence."""
    claims_text = "\n".join(f"- {c}" for c in claims)
    messages = [
        SystemMessage(
            content=(
                "You are a research assistant specializing in finding opposing viewpoints "
                "and counter-evidence. Generate effective search queries."
            )
        ),
        HumanMessage(
            content=f"""Given this article's argument and claims, generate search queries to find counter-evidence and opposing viewpoints.

Summary: {summary}

Claims:
{claims_text}

Generate 4-6 specific search queries designed to find:
- Counter-arguments to the main thesis
- Evidence that contradicts the claims
- Alternative perspectives from credible sources
- Data or research that challenges the conclusions

Respond in JSON format:
{{
    "queries": ["query 1", "query 2", ...]
}}

Make queries specific and targeted. Use terms like "criticism of", "against", "problems with", "counter-evidence", "opposing view"."""
        ),
    ]
    response = llm.invoke(messages)
    data = _parse_json_response(response.content)
    return data.get("queries", [])


def _synthesize_counter_arguments(
    llm, summary: str, claims: list[str], sources: list[dict[str, str]]
) -> list[dict]:
    """Synthesize counter-arguments from gathered evidence."""
    claims_text = "\n".join(f"{i + 1}. {c}" for i, c in enumerate(claims))
    sources_text = "\n\n".join(
        f"Source: {s['title']} ({s['url']})\n{s['content'][:3000]}" for s in sources
    )

    messages = [
        SystemMessage(
            content=(
                "You are the Devil's Advocate — an expert debater who constructs compelling, "
                "evidence-based counter-arguments. You are intellectually honest, cite sources, "
                "and never use straw-man fallacies. Your goal is to present the strongest "
                "possible opposing case."
            )
        ),
        HumanMessage(
            content=f"""The original article argues:
{summary}

Its key claims are:
{claims_text}

Here is counter-evidence gathered from various sources:
{sources_text}

Now construct 3-5 strong counter-arguments. Each should:
1. Directly address one or more of the original claims
2. Present specific evidence from the sources provided
3. Be intellectually honest — acknowledge where the original has merit
4. Use credible reasoning, not emotional appeals

Respond in JSON format:
{{
    "counter_arguments": [
        {{
            "title": "Brief title for this counter-point",
            "argument": "The full counter-argument (2-4 sentences)",
            "evidence": "Specific evidence supporting this counter-argument",
            "source_urls": ["url1", "url2"]
        }}
    ]
}}"""
        ),
    ]
    response = llm.invoke(messages)
    data = _parse_json_response(response.content)
    return data.get("counter_arguments", [])


def _assess_bias(
    llm, summary: str, claims: list[str], counter_args: list[dict]
) -> dict:
    """Assess the bias level of the original article."""
    claims_text = "\n".join(f"- {c}" for c in claims)
    counter_text = "\n".join(f"- {ca.get('title', '')}: {ca.get('argument', '')}" for ca in counter_args)

    messages = [
        SystemMessage(
            content=(
                "You are a media bias analyst. Assess the balance and objectivity "
                "of arguments fairly and without your own bias."
            )
        ),
        HumanMessage(
            content=f"""Assess the bias level of this article's argument.

Original argument: {summary}
Original claims:
{claims_text}

Counter-arguments found:
{counter_text}

Provide a bias assessment:
- score: 0-100 where 0 = extremely biased, 50 = moderately biased, 100 = well-balanced
- explanation: 2-3 sentences explaining the assessment

Respond in JSON format:
{{
    "score": 50,
    "explanation": "Assessment explanation here"
}}"""
        ),
    ]
    response = llm.invoke(messages)
    return _parse_json_response(response.content)
