# Fantasy Baseball Agent Training Specification

## Overview

Train a personalized humor agent on ~10 years of fantasy baseball league content to generate emails, commentary, and roasts that match your authentic voice and style.

## Data Sources

### 1. Evernote Notes
**Status**: Parser complete (`src/ingestion/evernote_parser.py`)

**Content types**:
- Draft emails and newsletters
- League rules and traditions
- Roasts, recaps, and award write-ups
- Notes on league members, running jokes, inside references

**Collection process**:
1. Export notebooks as `.enex` files from Evernote
2. Place in `data/raw/evernote/`
3. Run parser: `python -m src.ingestion.evernote_parser data/raw/evernote/ data/processed/evernote/`

---

### 2. Gmail/Email Archives
**Status**: Parser complete (`src/ingestion/email_parser.py`)

**Content types**:
- Sent fantasy league emails
- Email threads and replies
- Trash talk, trade negotiations, weekly recaps

**Collection process**:

**Option A: Gmail → Evernote (recommended)**
1. Forward emails to your Evernote email address
2. Process as Evernote notes (consolidates into one pipeline)

**Option B: Direct Gmail Export**
1. Use Google Takeout to export Gmail as `.mbox`
2. Filter to relevant labels/threads
3. Place in `data/raw/email/`
4. Run parser: `python -m src.ingestion.email_parser data/raw/email/ data/processed/email/`

---

### 3. YouTube Podcasts (NEW)
**Status**: Not yet implemented

**Content types**:
- Audio commentary and banter
- Verbal humor patterns and delivery
- Nicknames, catchphrases, recurring bits

**Collection process**:
1. Download audio from YouTube videos
2. Transcribe using Whisper (or similar)
3. Parse and structure transcripts

**New module needed**: `src/ingestion/youtube_parser.py`

---

## Data Processing Pipeline

```
┌─────────────────────────────────────────────────────────────────────┐
│                         RAW DATA SOURCES                            │
├─────────────────┬─────────────────────┬─────────────────────────────┤
│   Evernote      │      Gmail          │       YouTube               │
│   (.enex)       │   (.mbox/.eml)      │    (video URLs)             │
└────────┬────────┴──────────┬──────────┴──────────────┬──────────────┘
         │                   │                         │
         ▼                   ▼                         ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────────────────┐
│ evernote_parser │ │  email_parser   │ │     youtube_parser          │
│   (complete)    │ │   (complete)    │ │ - yt-dlp for audio download │
│                 │ │                 │ │ - whisper for transcription │
│                 │ │                 │ │ - speaker diarization       │
└────────┬────────┘ └────────┬────────┘ └──────────────┬──────────────┘
         │                   │                         │
         ▼                   ▼                         ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    PROCESSED DATA (JSON)                            │
│                    data/processed/                                  │
│  - notes.json (evernote)                                           │
│  - emails.json (gmail)                                             │
│  - transcripts.json (youtube)                                      │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      CONTENT ANALYZER                               │
│  - Extract humor patterns                                          │
│  - Identify recurring jokes/references                             │
│  - Build league member profiles                                    │
│  - Tag content by type (roast, recap, trade talk, etc.)           │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    CURATED EXAMPLES                                 │
│                    data/curated/                                    │
│  - best_roasts.json                                                │
│  - weekly_recaps.json                                              │
│  - trade_negotiations.json                                         │
│  - league_lore.json (inside jokes, nicknames, history)            │
└─────────────────────────────────────────────────────────────────────┘
```

---

## YouTube Parser Specification

### Dependencies
```
yt-dlp          # YouTube audio download
openai-whisper  # Transcription (local) OR
anthropic       # Claude for transcription (cloud)
```

### Data Model
```python
@dataclass
class PodcastTranscript:
    video_id: str
    title: str
    upload_date: datetime
    duration_seconds: int
    transcript: str
    segments: list[TranscriptSegment]  # timestamped chunks
    speakers: list[str]  # if diarization available
    source_url: str

@dataclass
class TranscriptSegment:
    start_time: float
    end_time: float
    text: str
    speaker: str | None
```

### Processing Steps
1. **Download**: `yt-dlp -x --audio-format mp3 <url>`
2. **Transcribe**: Whisper large-v3 or Claude audio API
3. **Segment**: Break into speaker turns / topic chunks
4. **Extract**: Pull out quotable moments, jokes, references

---

## Training Approaches (Ranked by Recommendation)

### Approach 1: RAG + Few-Shot Prompting (RECOMMENDED START)

**How it works**:
- Embed all curated examples using Claude or OpenAI embeddings
- At generation time, retrieve most relevant examples
- Include 3-5 examples in the prompt as style references

**Pros**:
- No fine-tuning required
- Easy to update with new content
- Full control over what examples are used
- Works with any amount of data

**Implementation**:
```python
# Pseudocode
examples = retrieve_similar_examples(current_context, k=5)
prompt = f"""
You write humor for our fantasy baseball league.
Here are examples of my writing style:

{format_examples(examples)}

Now write a {content_type} about {topic}.
"""
response = claude.generate(prompt)
```

**Requirements**:
- 50-100 curated examples minimum
- Vector database (Chroma, Pinecone, or simple FAISS)
- Good tagging/categorization of examples

---

### Approach 2: Long System Prompt with Style Guide

**How it works**:
- Analyze your content to extract patterns, vocabulary, humor techniques
- Build a comprehensive "style bible" as system prompt
- Include league context, member profiles, inside jokes

**Pros**:
- Simpler than RAG
- No infrastructure needed
- Good for consistent voice

**Implementation**:
```python
system_prompt = """
You are writing as [Name] for the [League Name] fantasy baseball league.

## Voice & Style
- Heavy use of sarcasm and self-deprecation
- References to 2017 draft disaster constantly
- Calls Mike "The Algorithm" ironically
- Never uses exclamation points unironically

## League Lore
- The Bartolo Colon Incident (2019)
- Annual "Biggest Disappointment" trophy
- Running joke about Steve's "process"

## Vocabulary
- "absolute wagon" = good pitcher
- "certified fraud" = underperforming player
- "league winner" = always used sarcastically
...
"""
```

**Requirements**:
- Manual analysis of content patterns
- Maintain and update the style guide
- Works with less data than RAG

---

### Approach 3: Fine-Tuning (FUTURE)

**How it works**:
- Create training dataset of input/output pairs
- Fine-tune Claude or another model on your content

**Pros**:
- Most authentic voice replication
- Fastest inference (no retrieval)
- Handles nuance better

**Cons**:
- Requires 500+ high-quality examples
- More expensive and complex
- Harder to update

**When to consider**:
- After validating RAG approach works
- When you have 500+ curated examples
- If RAG isn't capturing your voice well enough

---

## Recommended Implementation Order

### Phase 1: Data Collection (Week 1-2)
- [ ] Export all Evernote notebooks
- [ ] Export Gmail via Takeout or forward to Evernote
- [ ] List all YouTube podcast URLs
- [ ] Run existing parsers on Evernote/Email data
- [ ] Build YouTube parser

### Phase 2: Data Curation (Week 2-3)
- [ ] Review processed content
- [ ] Tag content by type (roast, recap, trade talk, etc.)
- [ ] Identify 100 best examples across all sources
- [ ] Extract league lore (inside jokes, nicknames, history)
- [ ] Document recurring humor patterns

### Phase 3: RAG System (Week 3-4)
- [ ] Set up vector database
- [ ] Embed all curated examples
- [ ] Build retrieval pipeline
- [ ] Create prompt templates for each content type
- [ ] Test generation quality

### Phase 4: Integration (Week 4-5)
- [ ] Connect Yahoo Fantasy API (already documented)
- [ ] Build "humor opportunity" detector
- [ ] Create daily generation pipeline
- [ ] Add human review/approval step

### Phase 5: Iteration (Ongoing)
- [ ] Collect feedback on generated content
- [ ] Add new examples to the corpus
- [ ] Refine prompts based on what works
- [ ] Consider fine-tuning if justified

---

## File Structure After Implementation

```
data/
├── raw/
│   ├── evernote/           # .enex exports
│   ├── email/              # .mbox exports
│   └── youtube/            # Downloaded audio files
├── processed/
│   ├── evernote.json       # Parsed notes
│   ├── emails.json         # Parsed emails
│   └── transcripts.json    # Parsed transcripts
├── curated/
│   ├── roasts.json
│   ├── recaps.json
│   ├── trade_talk.json
│   └── league_lore.json
└── embeddings/
    └── examples.index      # Vector index

src/
├── ingestion/
│   ├── evernote_parser.py  # ✅ Complete
│   ├── email_parser.py     # ✅ Complete
│   └── youtube_parser.py   # 🆕 To build
├── analysis/
│   ├── content_tagger.py   # 🆕 Auto-categorize content
│   └── pattern_extractor.py # 🆕 Extract style patterns
├── retrieval/
│   ├── embeddings.py       # 🆕 Generate embeddings
│   └── retriever.py        # 🆕 RAG retrieval
├── agent/
│   ├── prompts.py          # 🆕 Prompt templates
│   └── generator.py        # 🆕 Content generation
└── integrations/
    └── yahoo_client.py     # Phase 2 roadmap item
```

---

## Success Metrics

1. **Voice Authenticity**: Generated content is indistinguishable from your actual writing (blind test with league members)
2. **Humor Quality**: Content is genuinely funny, not just templated
3. **Context Awareness**: References real league history and inside jokes appropriately
4. **Consistency**: Maintains voice across different content types
5. **Efficiency**: Can generate a week's worth of content in minutes

---

## Open Questions

1. **How many YouTube podcasts?** More audio = better voice capture, but transcription takes time
2. **Multi-speaker podcasts?** Need speaker diarization to isolate your voice
3. **Content freshness?** How much do recent examples matter vs. classic bits?
4. **Approval workflow?** Always human review, or auto-send for low-stakes content?
5. **Legal/Privacy?** Any concerns about processing league members' communications?

---

## Next Steps

1. Confirm this approach works for your goals
2. Start data exports (Evernote, Gmail)
3. Provide YouTube podcast URLs
4. I'll build the YouTube parser next
