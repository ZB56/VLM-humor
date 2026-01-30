# Fantasy Baseball League Agent
## Product Design Document

**Version**: 1.0
**Date**: January 2026
**Status**: Draft

---

## 1. Executive Summary

Build an AI agent trained on decades of personal fantasy baseball league history to serve as an interactive league historian, analyst, and content generator. The agent will understand league culture, inside jokes, historical context, rivalries, and member personalities to provide entertaining and insightful commentary.

---

## 2. Problem Statement

Fantasy baseball leagues that run for 10+ years accumulate rich history across fragmented data sources:
- Notes and commentary scattered across Evernote
- Email threads with trash talk, trade negotiations, and recaps
- Spreadsheets tracking historical stats, standings, and keeper decisions
- Podcast episodes with league commentary and analysis

This history is difficult to search, reference, or leverage for new content. League members forget great moments, inside jokes lose context, and new members miss years of backstory.

---

## 3. User Persona

**Primary User**: League Commissioner / Long-time Member
- Has been running or participating in a fantasy baseball league for 10+ years
- Creates league content (emails, podcasts, recaps)
- Wants to preserve and leverage league history
- Enjoys trash talk and league culture
- Technical enough to run scripts and manage data exports

---

## 4. Data Sources & Ingestion Strategy

### 4.1 Primary Data Repository: Evernote

Evernote serves as the **central aggregation point** for all league content. This simplifies the architecture by providing a single export format (`.enex`) regardless of original source.

```
┌─────────────────────────────────────────────────────────────┐
│                     DATA FLOW                                │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│   Gmail ──────────┐                                          │
│                   │                                          │
│   Google Drive ───┼──────► Evernote ──────► .enex export    │
│                   │           │                              │
│   YouTube ────────┘           │                              │
│   (transcripts)               ▼                              │
│                          Agent Training                      │
│   Evernote ───────────────────┘                              │
│   (native notes)                                             │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 Data Source Details

| Source | Content Type | Export Method | Volume Estimate |
|--------|--------------|---------------|-----------------|
| **Evernote** | Notes, commentary, recaps, draft boards | Native export to `.enex` | Varies |
| **Gmail** | League emails, trash talk, trade proposals | Forward to Evernote or Google Takeout → Evernote | 10+ years of threads |
| **Google Drive** | Spreadsheets (standings, keeper values, historical stats) | Download as CSV/PDF → Save to Evernote | Dozens of sheets |
| **YouTube** | Podcast audio/video | Download → Transcribe → Save to Evernote | 2 podcasts |

### 4.3 Data Ingestion Methods

#### Gmail → Evernote
1. **Option A: Forward to Evernote** (Recommended)
   - Each Evernote account has a unique email address (Settings → Email Notes)
   - Forward individual emails or set up Gmail filters to auto-forward
   - Preserves formatting and attachments

2. **Option B: Google Takeout**
   - Export Gmail as `.mbox`
   - Parse with email parser
   - Import parsed content to Evernote via API or manual copy

#### Google Drive → Evernote
1. **Spreadsheets**
   - Download as CSV or PDF
   - Drag into Evernote or use Web Clipper
   - For large sheets, consider converting to formatted notes

2. **Google Docs**
   - Use Evernote Web Clipper
   - Or export as PDF and import

#### YouTube → Evernote
1. **Download audio** using `yt-dlp`:
   ```bash
   yt-dlp -x --audio-format mp3 "https://youtube.com/watch?v=VIDEO_ID"
   ```

2. **Transcribe** using one of:
   - OpenAI Whisper (free, local)
   - AssemblyAI (API, speaker diarization)
   - Otter.ai (easy, some free tier)

3. **Save transcript** to Evernote as a note

---

## 5. Agent Capabilities

### 5.1 Core Functions

| Capability | Description | Example |
|------------|-------------|---------|
| **League Historian** | Answer questions about league history | "Who won the championship in 2019?" |
| **Trash Talk Generator** | Generate roasts based on current events + history | "Write something about Mike's 0-3 start" |
| **Trade Analyst** | Evaluate trades with historical context | "How does this compare to the infamous 2017 Trout trade?" |
| **Recap Writer** | Generate weekly/seasonal recaps in league voice | "Write this week's recap email" |
| **Podcast Prep** | Generate talking points for league podcasts | "What should we cover in episode 50?" |
| **New Member Onboarder** | Explain league history, rules, and culture | "Explain the 'Taco Tuesday' rule to a new member" |

### 5.2 Interaction Modes

1. **Chat Interface** - Ask questions, get answers
2. **Content Generation** - Produce emails, recaps, scripts
3. **Analysis Mode** - Deep dives on trades, seasons, members
4. **Scheduled Outputs** - Automated weekly emails (future)

---

## 6. Technical Architecture

### 6.1 High-Level Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                         SYSTEM ARCHITECTURE                       │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────┐   │
│  │   Evernote  │    │   Parser    │    │   Document Store    │   │
│  │   Export    │───►│   Pipeline  │───►│   (Chunked JSON)    │   │
│  │   (.enex)   │    │             │    │                     │   │
│  └─────────────┘    └─────────────┘    └──────────┬──────────┘   │
│                                                    │              │
│                                                    ▼              │
│                                        ┌─────────────────────┐   │
│                                        │   Embedding Index   │   │
│                                        │   (Vector Store)    │   │
│                                        └──────────┬──────────┘   │
│                                                    │              │
│  ┌─────────────┐    ┌─────────────┐              │              │
│  │   Yahoo     │    │   Context   │◄─────────────┘              │
│  │   Fantasy   │───►│   Builder   │                             │
│  │   API       │    │             │                             │
│  └─────────────┘    └──────────┬──────────┘                     │
│                                 │                                │
│                                 ▼                                │
│                      ┌─────────────────────┐                    │
│                      │   Claude Agent      │                    │
│                      │   (Anthropic API)   │                    │
│                      └──────────┬──────────┘                    │
│                                 │                                │
│                                 ▼                                │
│                      ┌─────────────────────┐                    │
│                      │   Output            │                    │
│                      │   (Chat/Email/Doc)  │                    │
│                      └─────────────────────┘                    │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

### 6.2 Component Details

#### Parser Pipeline
- **Input**: `.enex` files from Evernote export
- **Processing**:
  - Extract text, attachments, metadata
  - Identify content type (email, spreadsheet, transcript, note)
  - Apply content-specific parsing
  - Chunk long documents
  - Extract entities (names, dates, teams, players)
- **Output**: Structured JSON documents

#### Document Store
- JSON files for simplicity (upgrade to SQLite if needed)
- Schema includes: source, date, participants, content type, tags
- Supports full-text search

#### Embedding Index
- Generate embeddings for semantic search
- Use for RAG (Retrieval Augmented Generation)
- Options: OpenAI embeddings, local models (sentence-transformers)
- Store in: Chroma, FAISS, or simple JSON + numpy

#### Context Builder
- Retrieves relevant documents based on query
- Incorporates current Yahoo Fantasy data
- Builds prompt with examples and context

#### Claude Agent
- System prompt encoding league personality and style
- Few-shot examples from curated content
- Access to tools for data retrieval

---

## 7. Data Schema

### 7.1 Document Schema

```json
{
  "id": "uuid",
  "source": "evernote|email|spreadsheet|transcript",
  "original_source": "gmail|drive|youtube|native",
  "title": "string",
  "content": "string",
  "content_type": "email|recap|analysis|trash_talk|stats|transcript",
  "date": "ISO8601",
  "participants": ["string"],
  "players_mentioned": ["string"],
  "teams_mentioned": ["string"],
  "season": "2024",
  "tags": ["string"],
  "metadata": {
    "evernote_guid": "string",
    "thread_id": "string",
    "episode_number": 1
  }
}
```

### 7.2 Curated Examples Schema

```json
{
  "id": "uuid",
  "category": "trash_talk|recap|analysis|inside_joke",
  "content": "string",
  "context": "Why this is funny/effective",
  "participants": ["string"],
  "quality_score": 5
}
```

---

## 8. Implementation Phases

### Phase 1: Data Consolidation (You do this)
**Goal**: Get all data into Evernote

| Task | Status | Notes |
|------|--------|-------|
| Export existing Evernote notes | ⬜ | File → Export as `.enex` |
| Forward/import Gmail threads | ⬜ | Use Evernote email address |
| Import Google Drive sheets | ⬜ | Download → Add to Evernote |
| Download YouTube podcasts | ⬜ | Use `yt-dlp` |
| Transcribe podcasts | ⬜ | Whisper or AssemblyAI |
| Save transcripts to Evernote | ⬜ | One note per episode |
| Final `.enex` export | ⬜ | Export everything |

### Phase 2: Parsing & Processing
**Goal**: Convert raw data to structured documents

- [ ] Enhance Evernote parser for multi-source content
- [ ] Build content type classifier
- [ ] Implement entity extraction (names, players, teams)
- [ ] Create document chunking logic
- [ ] Build date/season normalizer
- [ ] Output to document store

### Phase 3: Search & Retrieval
**Goal**: Enable finding relevant content

- [ ] Implement full-text search
- [ ] Generate embeddings for all documents
- [ ] Build vector search index
- [ ] Create hybrid search (keyword + semantic)
- [ ] Build context retrieval API

### Phase 4: Agent Core
**Goal**: Interactive agent that knows your league

- [ ] Design system prompt with league personality
- [ ] Curate 50-100 best examples manually
- [ ] Implement RAG pipeline
- [ ] Build prompt templates for different use cases
- [ ] Create chat interface (CLI first)
- [ ] Add Yahoo Fantasy API integration for current data

### Phase 5: Content Generation
**Goal**: Automated content creation

- [ ] Weekly recap generator
- [ ] Trash talk generator
- [ ] Trade analysis tool
- [ ] Podcast prep generator
- [ ] Email formatting and sending

### Phase 6: Polish & Deploy
**Goal**: Production-ready system

- [ ] Web UI (optional)
- [ ] Scheduled runs
- [ ] Logging and monitoring
- [ ] Feedback loop for improving outputs

---

## 9. Success Metrics

| Metric | Target | How to Measure |
|--------|--------|----------------|
| Historical accuracy | 90%+ | Spot-check answers against known facts |
| Voice authenticity | Qualitative | League members can't tell it's AI |
| Content usability | 80%+ | % of generated content used without major edits |
| Coverage | All seasons | Can answer questions about any league year |
| Response relevance | High | Retrieved context matches query intent |

---

## 10. Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Data loss during consolidation | High | Backup everything before processing |
| Poor transcription quality | Medium | Use high-quality transcription, manual review |
| Missing context in old emails | Medium | Add metadata during import |
| Hallucinated facts | High | RAG with citations, fact-checking prompt |
| Stale Yahoo data | Low | Regular API refresh |
| Privacy concerns | Medium | Keep data local, don't expose personal info |

---

## 11. Tools & Technologies

| Component | Recommended | Alternatives |
|-----------|-------------|--------------|
| LLM | Claude (Anthropic) | GPT-4, Llama |
| Embeddings | OpenAI `text-embedding-3-small` | Sentence Transformers |
| Vector Store | Chroma | FAISS, Pinecone |
| Transcription | OpenAI Whisper | AssemblyAI, Otter |
| Video Download | yt-dlp | youtube-dl |
| Fantasy API | Yahoo Fantasy Sports | ESPN (different API) |
| Data Storage | JSON → SQLite | PostgreSQL |
| Task Scheduling | APScheduler | Cron, Celery |

---

## 12. Open Questions

1. **How far back does your data go?** This affects volume estimates and processing time.

2. **How many league members?** Need their names for entity extraction.

3. **Any sensitive content to filter?** Personal info, real names vs nicknames, etc.

4. **Preferred interaction mode?** CLI, web app, Slack bot, email?

5. **Budget for APIs?** Transcription and embeddings have costs at scale.

6. **Current state of Evernote?** Already organized or needs cleanup?

7. **ESPN or Yahoo?** Different API integration needed.

---

## 13. Immediate Next Steps

### For You (Data Owner)
1. [ ] Inventory all data sources with rough volume estimates
2. [ ] Set up Evernote email forwarding address
3. [ ] Start forwarding key Gmail threads to Evernote
4. [ ] Download YouTube podcasts
5. [ ] Get transcription running on podcast audio
6. [ ] Create an "important moments" list from memory

### For Development
1. [ ] Enhance parser to handle multi-source Evernote notes
2. [ ] Build content type classifier
3. [ ] Design entity extraction for league-specific terms
4. [ ] Create sample prompts and test with manual context

---

## Appendix A: Evernote Email Forwarding

1. Open Evernote → Settings → Email Notes
2. Copy your unique Evernote email address
3. In Gmail:
   - Forward individual emails to this address
   - Or create a filter: `from:(league-email@yahoo.com)` → Forward to Evernote

Each forwarded email becomes a new note with:
- Subject line as title
- Email body as note content
- Attachments preserved

---

## Appendix B: YouTube Transcription Workflow

```bash
# 1. Install tools
pip install yt-dlp openai-whisper

# 2. Download audio
yt-dlp -x --audio-format mp3 -o "podcast_%(title)s.%(ext)s" "YOUTUBE_URL"

# 3. Transcribe with Whisper
whisper podcast_episode1.mp3 --model medium --output_format txt

# 4. Review and save transcript to Evernote
```

For better speaker identification, consider AssemblyAI which supports diarization.

---

## Appendix C: Google Sheets Export

For each important spreadsheet:

1. Open in Google Sheets
2. File → Download → CSV (for data processing) or PDF (for archival)
3. Save to Evernote:
   - Drag file into a note, or
   - Copy/paste data directly

Consider creating a "master note" that links to or summarizes all historical spreadsheets.

---

*Document maintained in: `docs/PRODUCT_DESIGN.md`*
