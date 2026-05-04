---
name: testing-devils-advocate
description: Test the Devil's Advocate Chrome extension end-to-end. Use when verifying extension UI, popup behavior, FAB injection, or backend API changes.
---

# Testing Devil's Advocate Extension

## Prerequisites

1. **Ollama** must be running with a model pulled (e.g. `qwen3:1.7b`)
2. **Python virtualenv** with the project installed (`pip install -e .`)

## Start the Backend

```bash
cd /home/ubuntu/repos/research-agent
source .venv/bin/activate
python -m research_agent.serve --port 8000
```

Verify with: `curl http://localhost:8000/api/health`
Expected: `{"status":"ok","provider":"ollama","version":"1.0.0"}`

## Load Extension in Chrome

The Chrome file picker dialog may not work well in headless/remote environments. Instead, launch Chrome with `--load-extension` flag:

```bash
$CHROME_BIN --load-extension=/path/to/research-agent/extension --user-data-dir="$USER_DATA" "chrome://extensions"
```

This reliably loads the extension without needing the file picker GUI.

## Key Test Points

### 1. Extension Loads (chrome://extensions)
- Shows "Devil's Advocate" v1.0.0
- No "Errors" badge
- Toggle is enabled
- Description: "Analyzes opinion pieces and news articles to generate well-sourced counter-arguments."

### 2. Popup UI (click extension icon on an article page)
- Title: "Devil's Advocate"
- Tagline: "Challenge your thinking. Break the echo chamber."
- Green dot + "Backend connected" (requires backend running)
- Shows detected article title and word count
- "Analyze This Article" button is enabled

### 3. Floating Action Button (navigate to any page with `<article>` tags)
- Red circular button (56px) fixed bottom-right
- Has tooltip: "Devil's Advocate: Generate counter-arguments"
- BBC News articles work well for testing

### 4. API Pipeline
```bash
curl -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"title":"Test","url":"https://example.com","text":"Social media is destroying democracy."}'
```

Expected response fields: `original_summary`, `original_claims` (array), `counter_arguments` (array with title/argument/evidence), `bias_assessment` (score 0-100 + explanation)

## Performance Notes

- The full analysis pipeline with Ollama on a 2-CPU VM might take 5-10+ minutes due to 3 sequential LLM calls + web searches + content extraction.
- Consider using `--max-time 600` with curl for API tests.
- For faster testing, use a cloud LLM provider (Gemini/OpenAI) instead of local Ollama by configuring environment variables.
- The `duckduckgo_search` package may show a rename warning — this is cosmetic and doesn't affect functionality.

## Devin Secrets Needed

No secrets required for local Ollama testing. For cloud LLM providers:
- `GOOGLE_API_KEY` — for Gemini provider
- `OPENAI_API_KEY` — for OpenAI provider
