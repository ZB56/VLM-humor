# VLM Humor Agent

A fantasy baseball humor agent trained on your personal writing style from Evernote notes and fantasy league emails. Integrates with Yahoo Fantasy Sports API to generate daily humorous league emails.

## Features

- **Evernote Parser**: Extract humor examples from your exported notes (`.enex`)
- **Email Parser**: Parse fantasy league email threads (`.mbox`, `.eml`)
- **Yahoo Fantasy Integration**: Pull standings, matchups, transactions, and roast-worthy moments
- **Humor Agent**: Generate content in your personal style using Claude

## Quick Start

```bash
# Clone and install
git clone <repo-url>
cd VLM-humor
pip install -e ".[dev]"

# Set up environment
cp .env.example .env
# Edit .env with your API keys

# Parse your humor corpus
python -m src.ingestion.evernote_parser data/raw/notes.enex -o data/processed/notes.json
python -m src.ingestion.email_parser data/raw/emails.mbox -o data/processed/emails.json
```

## Project Structure

```
VLM-humor/
├── data/
│   ├── raw/           # Original Evernote/email exports
│   ├── processed/     # Parsed JSON output
│   └── curated/       # Hand-picked best humor examples
├── src/
│   ├── ingestion/     # Evernote & email parsers
│   ├── agent/         # Humor agent logic
│   └── integrations/  # Yahoo Fantasy API client
├── prompts/           # System prompts & templates
├── docs/              # API documentation
└── tests/             # Test suite
```

## Roadmap

See [ROADMAP.md](ROADMAP.md) for the full project plan.

**Current Phase**: Data Collection & Preparation

1. Export your Evernote notes and fantasy league emails
2. Run the parsers to extract text
3. Curate 50-100 of your best humor examples
4. Set up Yahoo Fantasy API credentials

## Requirements

- Python 3.11+
- Anthropic API key (for Claude)
- Yahoo Developer credentials (for Fantasy API)

## License

MIT
