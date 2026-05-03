"""FastAPI backend for the Devil's Advocate browser extension.

Provides endpoints for article analysis and counter-argument generation.
Run with: uvicorn research_agent.api:app --host 0.0.0.0 --port 8000
"""

from __future__ import annotations

import os
import traceback
from dataclasses import asdict

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, HTTPException  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from pydantic import BaseModel  # noqa: E402

from research_agent.devils_advocate import analyze_article  # noqa: E402

app = FastAPI(
    title="Devil's Advocate API",
    description="Analyzes articles and generates well-sourced counter-arguments",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AnalyzeRequest(BaseModel):
    """Request body for article analysis."""

    title: str
    url: str = ""
    text: str


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    provider: str
    version: str = "1.0.0"


@app.get("/api/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Check if the API is running and which LLM provider is configured."""
    provider = os.environ.get("LLM_PROVIDER", "auto")
    if provider == "auto":
        if os.environ.get("OPENAI_API_KEY"):
            provider = "openai"
        elif os.environ.get("GOOGLE_API_KEY"):
            provider = "gemini"
        else:
            provider = "ollama"
    return HealthResponse(status="ok", provider=provider)


@app.post("/api/analyze")
async def analyze(request: AnalyzeRequest) -> dict:
    """Analyze an article and generate counter-arguments.

    Takes the article title, URL, and extracted text. Returns:
    - Original argument summary and claims
    - Counter-arguments with evidence and sources
    - Bias assessment
    """
    if not request.text or len(request.text.strip()) < 100:
        raise HTTPException(
            status_code=400,
            detail="Article text is too short. Please provide at least 100 characters.",
        )

    try:
        result = analyze_article(
            title=request.title,
            url=request.url,
            text=request.text,
        )
        return asdict(result)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {e}",
        ) from e
