# Autonomous Research Agent

An AI-powered research agent that takes a research question, autonomously searches the web, reads and analyzes sources, synthesizes findings, and produces a comprehensive structured report with citations.

## Architecture

Built with **LangGraph** for multi-step agentic reasoning:

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌─────────────┐     ┌──────────┐
│  Planner │ ──▶ │ Searcher │ ──▶ │  Reader  │ ──▶ │ Synthesizer │ ──▶ │  Writer  │
└──────────┘     └──────────┘     └──────────┘     └─────────────┘     └──────────┘
     ▲                                                                       │
     │                    (if report needs improvement)                      │
     └───────────────────────────────────────────────────────────────────────┘
```

### Workflow Nodes

1. **Planner** - Breaks down the research question into sub-questions and generates targeted search queries
2. **Searcher** - Executes web searches using DuckDuckGo (free) or Tavily API
3. **Reader** - Extracts content from web pages using trafilatura and analyzes relevance with LLM
4. **Synthesizer** - Combines findings across sources into coherent, evidence-backed insights
5. **Writer** - Generates a structured Markdown report with inline citations, then self-reviews for quality

The agent can **iterate**: if the self-review scores the report below threshold, it loops back to the Planner to search for additional information.

## Tech Stack

- **[LangGraph](https://github.com/langchain-ai/langgraph)** - Agentic workflow orchestration with stateful graph execution
- **[LangChain](https://github.com/langchain-ai/langchain)** - LLM integration (Google Gemini free tier, OpenAI optional)
- **[DuckDuckGo Search](https://github.com/deedy5/duckduckgo_search)** - Free web search (no API key required)
- **[Trafilatura](https://github.com/adbar/trafilatura)** - High-quality web content extraction
- **[Rich](https://github.com/Textualize/rich)** - Beautiful terminal output
- **[httpx](https://github.com/encode/httpx)** - Modern HTTP client

## Setup

### Prerequisites

- Python 3.11+
- A Google Gemini API key (free) — get one at [aistudio.google.com/apikey](https://aistudio.google.com/apikey)

### Installation

```bash
# Clone the repository
git clone https://github.com/tergel69/research-agent.git
cd research-agent

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate

# Install the package
pip install -e .

# Configure your API key (free)
cp .env.example .env
# Edit .env and add your GOOGLE_API_KEY (free from https://aistudio.google.com/apikey)

# Or for OpenAI (paid):
# pip install -e ".[openai]"
```

### Configuration

Edit `.env` to configure:

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GOOGLE_API_KEY` | Yes* | - | Google Gemini API key (free) |
| `GEMINI_MODEL` | No | `gemini-2.0-flash` | Gemini model to use |
| `OPENAI_API_KEY` | Alt* | - | OpenAI API key (paid alternative) |
| `OPENAI_MODEL` | No | `gpt-4o-mini` | OpenAI model to use |
| `LLM_PROVIDER` | No | auto | Force `gemini` or `openai` |
| `TAVILY_API_KEY` | No | - | Tavily API key for enhanced search |
| `MAX_SEARCH_RESULTS` | No | `5` | Max results per search query |
| `MAX_PAGES_TO_READ` | No | `3` | Max pages to read per iteration |

*Set either `GOOGLE_API_KEY` (free) or `OPENAI_API_KEY` (paid). At least one is required.

## Usage

```bash
# Basic usage
research-agent "Latest trends in quantum computing startups"

# With more iterations for deeper research
research-agent "Impact of AI on healthcare diagnostics" --iterations 3

# Custom output directory
research-agent "Comparison of Rust vs Go for web services" -o ./my-reports

# Or run as a Python module
python -m research_agent.main "Your research question here"
```

### Output

Reports are saved as Markdown files in the `reports/` directory (or custom path) with timestamps:

```
reports/20250503_120000_latest_trends_in_quantum_computing.md
```

Each report includes:
- **Executive Summary** - Key takeaways at a glance
- **Introduction** - Context and scope
- **Key Findings** - Detailed findings with inline citations `[Source N]`
- **Analysis** - Cross-cutting trends and implications
- **Knowledge Gaps** - Areas needing further research
- **Conclusion** - Summary of most important takeaways
- **References** - Numbered list of all sources with URLs

## Example

```bash
$ research-agent "What are the latest breakthroughs in nuclear fusion energy?"
```

```
╭─────────── Research Question ───────────╮
│ What are the latest breakthroughs in    │
│ nuclear fusion energy?                  │
╰─────────────────────────────────────────╯

Planning research strategy...
  Generated 4 sub-questions
  Generated 6 search queries

Searching the web...
  Searching: nuclear fusion breakthroughs 2025
  Searching: fusion energy startup funding
    ...
  Total unique sources: 18

Reading and analyzing sources...
  Reading: https://example.com/fusion-news
    Relevant (score: 0.9)
    ...

Synthesizing findings...
  Synthesized 8 key findings

Writing research report...
  Draft report generated
  Report finalized (quality: 0.85)

Report saved to: reports/20250503_120000_latest_breakthroughs_in_nuclear_fusion.md
```

## Project Structure

```
research-agent/
├── pyproject.toml              # Project config and dependencies
├── .env.example                # Environment variable template
├── README.md
├── reports/                    # Generated reports (gitignored)
└── src/research_agent/
    ├── __init__.py
    ├── main.py                 # CLI entry point
    ├── agent.py                # LangGraph workflow definition
    ├── config.py               # LLM configuration
    ├── state.py                # Agent state types
    ├── prompts.py              # LLM prompts for each node
    ├── tools/
    │   ├── search.py           # Web search (DuckDuckGo / Tavily)
    │   └── scraper.py          # Content extraction (trafilatura)
    └── nodes/
        ├── planner.py          # Research planning node
        ├── searcher.py         # Web search execution node
        ├── reader.py           # Content reading & analysis node
        ├── synthesizer.py      # Findings synthesis node
        └── writer.py           # Report generation node
```

## License

MIT
