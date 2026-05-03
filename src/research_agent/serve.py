"""CLI entry point for the Devil's Advocate API server."""

from __future__ import annotations

import argparse


def main() -> None:
    """Start the Devil's Advocate API server."""
    parser = argparse.ArgumentParser(description="Devil's Advocate API Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to (default: 8000)")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload for development")
    args = parser.parse_args()

    import uvicorn

    print("\n  Devil's Advocate API Server")
    print(f"  Running on http://{args.host}:{args.port}")
    print(f"  Health check: http://localhost:{args.port}/api/health")
    print(f"  Docs: http://localhost:{args.port}/docs\n")

    uvicorn.run(
        "research_agent.api:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
    )


if __name__ == "__main__":
    main()
