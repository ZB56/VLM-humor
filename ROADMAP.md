# VLM Humor Agent Roadmap

A fantasy baseball humor agent trained on your personal writing style.

## Project Vision

Build an AI agent that:
1. Learns your unique humor style from Evernote notes and fantasy league emails
2. Pulls data from Yahoo Fantasy Sports API
3. Generates daily humorous emails about your fantasy baseball league

---

## Phase 1: Data Collection & Preparation ✅ (Current)

### Completed
- [x] Project structure setup
- [x] Evernote parser (`src/ingestion/evernote_parser.py`)
- [x] Email parser (`src/ingestion/email_parser.py`)
- [x] Yahoo Fantasy API documentation

### Your Action Items
1. **Export your Evernote notes**
   - In Evernote: File → Export → Select notebooks → Export as `.enex`
   - Place files in `data/raw/`

2. **Export fantasy league emails**
   - Gmail: Use Google Takeout → Select Mail → Download as `.mbox`
   - Outlook: File → Open & Export → Export to `.pst` (convert to mbox)
   - Place files in `data/raw/`

3. **Run the parsers**
   ```bash
   # Parse Evernote
   python -m src.ingestion.evernote_parser data/raw/ -o data/processed/notes.json

   # Parse emails (filter for fantasy-related)
   python -m src.ingestion.email_parser data/raw/ -o data/processed/emails.json --group-threads
   ```

4. **Curate your best examples**
   - Review `data/processed/` output
   - Hand-pick 50-100 of your funniest snippets
   - Save to `data/curated/humor_examples.json`

---

## Phase 2: Yahoo Fantasy API Integration

### Tasks
- [ ] Create Yahoo Developer app and get OAuth credentials
- [ ] Implement OAuth token management in `src/integrations/yahoo_client.py`
- [ ] Build data fetchers for:
  - [ ] Standings
  - [ ] Weekly matchups & scores
  - [ ] Transactions (trades, adds, drops)
  - [ ] Roster decisions (who got benched)
- [ ] Create "humor opportunity" detector (blowouts, benched stars, etc.)

### Files to Create
```
src/integrations/
├── yahoo_client.py      # OAuth + API wrapper
├── data_fetcher.py      # Scheduled data pulls
└── humor_detector.py    # Find roast-worthy moments
```

---

## Phase 3: Humor Agent Core

### Tasks
- [ ] Design system prompt incorporating your humor style
- [ ] Implement RAG system for pulling relevant humor examples
- [ ] Create prompt templates for different scenarios:
  - Weekly recap
  - Trade analysis
  - Standings roast
  - Player spotlight (bust/boom)
- [ ] Build the core agent in `src/agent/humor_agent.py`

### Architecture Options

**Option A: Few-Shot Prompting (Recommended to start)**
- Embed 10-20 curated examples in system prompt
- Use Claude to generate new content in your style

**Option B: RAG + Examples**
- Index your curated examples with embeddings
- Retrieve relevant examples based on the current situation
- Include retrieved examples in the prompt

**Option C: Fine-Tuning (If you have 500+ examples)**
- Create training dataset from your humor corpus
- Fine-tune a model on your writing style

### Files to Create
```
src/agent/
├── humor_agent.py       # Main agent logic
├── prompt_builder.py    # Dynamic prompt construction
└── example_retriever.py # RAG for humor examples (if using Option B)

prompts/
├── system_prompt.txt    # Base personality
├── weekly_recap.txt     # Template for weekly emails
├── trade_roast.txt      # Template for trade commentary
└── standings.txt        # Template for standings update
```

---

## Phase 4: Email Generation Pipeline

### Tasks
- [ ] Implement daily data pull scheduler
- [ ] Create email content generator
- [ ] Build email formatting (HTML + plain text)
- [ ] Add review/approval workflow (optional)
- [ ] Integrate with email sending service (SendGrid, SES, etc.)

### Files to Create
```
src/
├── scheduler.py         # Daily job runner
├── email_generator.py   # Content + formatting
└── email_sender.py      # SMTP/API integration
```

---

## Phase 5: Polish & Deploy

### Tasks
- [ ] Add configuration management
- [ ] Implement logging and monitoring
- [ ] Create CLI for manual runs
- [ ] Set up deployment (cron, Lambda, etc.)
- [ ] Add ability to customize tone per recipient

---

## Quick Start Commands

```bash
# Install dependencies
pip install -e ".[dev]"

# Set up environment
cp .env.example .env
# Edit .env with your API keys

# Parse your data
python -m src.ingestion.evernote_parser data/raw/notes.enex -o data/processed/notes.json
python -m src.ingestion.email_parser data/raw/emails.mbox -o data/processed/emails.json

# Run tests
pytest

# (Future) Generate daily email
python -m src.agent.humor_agent --league YOUR_LEAGUE_ID
```

---

## Data Requirements

| Phase | Data Needed |
|-------|-------------|
| Phase 1 | Evernote exports, Email exports |
| Phase 2 | Yahoo OAuth credentials, League ID |
| Phase 3 | Curated humor examples (50-100 minimum) |
| Phase 4 | Email service credentials |

---

## Tech Stack

- **LLM**: Claude (Anthropic API)
- **Fantasy Data**: Yahoo Fantasy Sports API
- **Data Storage**: JSON files (upgrade to SQLite if needed)
- **Scheduling**: APScheduler or cron
- **Email**: SendGrid or AWS SES

---

## Notes

- Start simple with few-shot prompting before investing in RAG or fine-tuning
- The quality of your curated examples matters more than quantity
- Test humor output with league mates before automating emails
- Consider a "preview mode" that sends drafts to you first
