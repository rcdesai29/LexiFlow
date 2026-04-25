# LexiFlow

LexiFlow is an AI speech coaching platform that turns impromptu speech into actionable insights using word-frequency visualization, filler detection, and guided practice loops.

## How It Works

```
Record → Transcribe → Analyze → Visualize → Set Goals → Practice → Re-record → Compare
```

You speak. LexiFlow breaks down what you said — how many fillers you used, how diverse your vocabulary is, which words you lean on too hard — then helps you set replacement goals and generates guided speaking prompts so you actually improve.

## MVP Metrics

| Metric | What it measures |
|---|---|
| `filler_count` | Total filler words (um, like, basically, you know, etc.) |
| `top_repeated_words` | Most-used non-stop words |
| `vocab_diversity` | `unique_words / total_words` — higher is better |
| `words_per_minute` | Speech pace |

## Visualization Format

The analysis returns visualization-ready data categorized by word type:

```json
[
  { "word": "like", "count": 12, "category": "filler" },
  { "word": "very", "count": 5, "category": "weak" },
  { "word": "significant", "count": 3, "category": "normal" }
]
```

Categories: **filler** (um, like, basically) · **weak** (very, really, stuff) · **normal** (everything else)

## Project Structure

```
lexiflow/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py          # FastAPI routes
│   │   ├── analyzer.py      # NLP analysis engine
│   │   └── models.py        # SQLite + SQLAlchemy models
│   ├── tests/
│   │   └── test_analyzer.py  # Analyzer smoke test
│   └── requirements.txt
├── frontend/
│   └── LexiFlow.jsx          # React component (connects to backend)
├── .gitignore
└── README.md
```

## Getting Started

### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

The API runs at `http://localhost:8000`. Interactive docs at `http://localhost:8000/docs`.

### Frontend

Drop `frontend/LexiFlow.jsx` into your React or Next.js project as a page component. The component expects the backend running on `localhost:8000` (configurable via the `API` constant at the top of the file).

If using Vite:

```bash
npm create vite@latest lexiflow-ui -- --template react
cd lexiflow-ui
npm install
# Copy LexiFlow.jsx into src/ and import it in App.jsx
npm run dev
```

## API Routes

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/recordings/upload` | Upload an audio file, returns a recording ID |
| `POST` | `/recordings/{id}/analyze` | Analyze a transcript (passed in request body for MVP) |
| `GET` | `/recordings/{id}/analysis` | Retrieve stored analysis results |
| `POST` | `/goals` | Create a replacement goal (e.g. "very big" → "massive") |
| `GET` | `/goals` | List all active replacement goals |
| `POST` | `/practice/generate` | Generate a guided speaking prompt based on active goals |
| `GET` | `/progress` | Compare metrics across all recordings over time |

### Example: Analyze a Speech

```bash
# 1. Upload audio
curl -X POST http://localhost:8000/recordings/upload \
  -F "file=@speech.wav"

# 2. Analyze (MVP: paste transcript manually)
curl -X POST http://localhost:8000/recordings/1/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "transcript": "So like, I basically think communication is very important...",
    "duration_seconds": 60
  }'

# 3. Create a replacement goal
curl -X POST http://localhost:8000/goals \
  -H "Content-Type: application/json" \
  -d '{
    "old_phrase": "very important",
    "new_phrase": "critical"
  }'

# 4. Get a practice prompt
curl -X POST http://localhost:8000/practice/generate \
  -H "Content-Type: application/json" \
  -d '{"topic": "teamwork in software development"}'
```

## Database Schema (MVP)

```
recordings        — id, audio_path, transcript, duration_seconds, created_at
analyses          — id, recording_id, filler_count, vocab_diversity, words_per_minute,
                    total_words, unique_words, word_freq_json, filler_words_json, word_data_json
replacement_goals — id, old_phrase, new_phrase, context_example, active, created_at
practice_sessions — id, goal_id, prompt_text, recording_id, created_at
```

Using SQLite for MVP. No auth — single-user for now.

## Roadmap

- [x] Speech analysis engine (filler detection, vocab diversity, WPM)
- [x] FastAPI backend with all MVP routes
- [x] React frontend with bubble visualization
- [x] Replacement goals + guided speaking prompts
- [x] Progress tracking (before/after comparison)
- [ ] Whisper integration for auto-transcription
- [ ] LLM-powered practice prompt generation
- [ ] Real-time filler detection mode
- [ ] User authentication
- [ ] D3.js bubble map visualization upgrade

## Tech Stack

**Backend:** Python, FastAPI, SQLAlchemy, SQLite

**Frontend:** React, Instrument Serif + DM Mono typography

**Planned:** OpenAI Whisper, spaCy, D3.js

## License

MIT
