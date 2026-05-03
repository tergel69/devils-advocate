"""Content extraction tool for reading web pages."""

from __future__ import annotations

import httpx
from rich.console import Console

console = Console()

MAX_CONTENT_LENGTH = 15000


def extract_content(url: str, timeout: float = 15.0) -> dict[str, str]:
    """Extract main content from a web page.

    Uses trafilatura for high-quality content extraction, with fallback
    to basic HTML parsing.

    Args:
        url: The URL to extract content from.
        timeout: Request timeout in seconds.

    Returns:
        Dict with 'url', 'title', 'content', and 'success' keys.
    """
    result: dict[str, str] = {
        "url": url,
        "title": "",
        "content": "",
        "success": "false",
    }

    try:
        html = _fetch_page(url, timeout)
        if not html:
            result["content"] = "Failed to fetch page"
            return result

        content, title = _extract_with_trafilatura(html, url)

        if not content:
            content, title = _extract_with_fallback(html)

        if content:
            if len(content) > MAX_CONTENT_LENGTH:
                content = content[:MAX_CONTENT_LENGTH] + "\n\n[Content truncated...]"
            result["content"] = content
            result["title"] = title or url
            result["success"] = "true"
        else:
            result["content"] = "Could not extract meaningful content from page"

    except Exception as e:
        result["content"] = f"Error extracting content: {e}"
        console.print(f"[yellow]Extraction error for {url}: {e}[/yellow]")

    return result


def _fetch_page(url: str, timeout: float) -> str | None:
    """Fetch HTML content from a URL."""
    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
        }
        with httpx.Client(follow_redirects=True, timeout=timeout) as client:
            response = client.get(url, headers=headers)
            response.raise_for_status()
            return response.text
    except Exception as e:
        console.print(f"[yellow]Fetch error for {url}: {e}[/yellow]")
        return None


def _extract_with_trafilatura(html: str, url: str) -> tuple[str, str]:
    """Extract content using trafilatura."""
    try:
        import trafilatura

        result = trafilatura.extract(
            html,
            url=url,
            include_comments=False,
            include_tables=True,
            favor_precision=True,
        )
        metadata = trafilatura.extract_metadata(html, default_url=url)
        title = metadata.title if metadata and metadata.title else ""
        return result or "", title
    except Exception:
        return "", ""


def _extract_with_fallback(html: str) -> tuple[str, str]:
    """Basic HTML content extraction fallback."""
    try:
        import re

        title_match = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
        title = title_match.group(1).strip() if title_match else ""

        text = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"\s+", " ", text).strip()

        return text[:MAX_CONTENT_LENGTH], title
    except Exception:
        return "", ""
