"""
LexiFlow — FastAPI Backend
Routes: upload, analyze, get analysis, goals, practice prompts, progress
"""

import os
import json
import shutil
import uuid
from fastapi import FastAPI, UploadFile, File, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.models import init_db, get_db, Recording, Analysis, ReplacementGoal, PracticeSession
from app.analyzer import analyze_transcript

app = FastAPI(title="LexiFlow", version="0.1.0")

# CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # Next.js / Vite
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@app.on_event("startup")
def startup():
    init_db()


# ──────────────────────────────────────────────
# Schemas
# ──────────────────────────────────────────────

class AnalyzeRequest(BaseModel):
    transcript: str  # For MVP: user pastes transcript (Whisper integration later)
    duration_seconds: float = 60.0


class GoalCreate(BaseModel):
    old_phrase: str
    new_phrase: str
    context_example: str | None = None


class PracticeRequest(BaseModel):
    topic: str | None = "general communication"


# ──────────────────────────────────────────────
# Routes
# ──────────────────────────────────────────────

@app.post("/recordings/upload")
async def upload_recording(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Upload an audio file. Returns a recording ID."""
    ext = os.path.splitext(file.filename)[1] if file.filename else ".wav"
    safe_name = f"{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(UPLOAD_DIR, safe_name)
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    recording = Recording(audio_path=file_path)
    db.add(recording)
    db.commit()
    db.refresh(recording)

    return {"id": recording.id, "audio_path": file_path, "message": "Uploaded. Call POST /recordings/{id}/analyze next."}


@app.post("/recordings/{recording_id}/analyze")
def analyze_recording(recording_id: int, req: AnalyzeRequest, db: Session = Depends(get_db)):
    """
    Analyze a recording's transcript.
    MVP: transcript is passed in the request body.
    Future: auto-transcribe from audio via Whisper.
    """
    recording = db.query(Recording).filter(Recording.id == recording_id).first()
    if not recording:
        raise HTTPException(status_code=404, detail="Recording not found")

    # Save transcript to recording
    recording.transcript = req.transcript
    recording.duration_seconds = req.duration_seconds

    # Run analysis
    results = analyze_transcript(req.transcript, req.duration_seconds)

    # Store analysis
    analysis = Analysis(
        recording_id=recording_id,
        filler_count=results["filler_count"],
        vocab_diversity=results["vocab_diversity"],
        words_per_minute=results["words_per_minute"],
        total_words=results["total_words"],
        unique_words=results["unique_words"],
    )
    analysis.set_word_data(results["word_data"])
    analysis.set_filler_words(results["filler_words"])
    analysis.set_word_freq(results["top_repeated_words"])

    db.add(analysis)
    db.commit()
    db.refresh(analysis)

    return {
        "recording_id": recording_id,
        "analysis_id": analysis.id,
        "transcript": req.transcript,
        "metrics": {
            "filler_count": results["filler_count"],
            "vocab_diversity": results["vocab_diversity"],
            "words_per_minute": results["words_per_minute"],
            "total_words": results["total_words"],
            "unique_words": results["unique_words"],
        },
        "filler_words": results["filler_words"],
        "top_repeated_words": results["top_repeated_words"],
        "word_data": results["word_data"],  # visualization-ready
    }


@app.get("/recordings/{recording_id}/analysis")
def get_analysis(recording_id: int, db: Session = Depends(get_db)):
    """Get the analysis for a recording."""
    analysis = db.query(Analysis).filter(Analysis.recording_id == recording_id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")

    recording = db.query(Recording).filter(Recording.id == recording_id).first()

    return {
        "recording_id": recording_id,
        "transcript": recording.transcript if recording else None,
        "metrics": {
            "filler_count": analysis.filler_count,
            "vocab_diversity": analysis.vocab_diversity,
            "words_per_minute": analysis.words_per_minute,
            "total_words": analysis.total_words,
            "unique_words": analysis.unique_words,
        },
        "filler_words": analysis.get_filler_words(),
        "top_repeated_words": analysis.get_word_freq(),
        "word_data": analysis.get_word_data(),
    }


@app.post("/goals")
def create_goal(goal: GoalCreate, db: Session = Depends(get_db)):
    """Create a replacement goal (e.g. 'very big' -> 'massive')."""
    new_goal = ReplacementGoal(
        old_phrase=goal.old_phrase,
        new_phrase=goal.new_phrase,
        context_example=goal.context_example,
    )
    db.add(new_goal)
    db.commit()
    db.refresh(new_goal)

    return {
        "id": new_goal.id,
        "old_phrase": new_goal.old_phrase,
        "new_phrase": new_goal.new_phrase,
        "context_example": new_goal.context_example,
        "active": new_goal.active,
    }


@app.get("/goals")
def list_goals(db: Session = Depends(get_db)):
    """List all active replacement goals."""
    goals = db.query(ReplacementGoal).filter(ReplacementGoal.active == True).all()
    return [
        {
            "id": g.id,
            "old_phrase": g.old_phrase,
            "new_phrase": g.new_phrase,
            "context_example": g.context_example,
        }
        for g in goals
    ]


@app.post("/practice/generate")
def generate_practice(req: PracticeRequest, db: Session = Depends(get_db)):
    """
    Generate a guided speaking prompt based on active goals.
    MVP: template-based. Future: LLM-generated.
    """
    goals = db.query(ReplacementGoal).filter(ReplacementGoal.active == True).all()

    if not goals:
        prompt = f"Speak for 60 seconds about: {req.topic}. Focus on clear, concise language and avoid filler words."
    else:
        replacements = [f"'{g.old_phrase}' → '{g.new_phrase}'" for g in goals[:3]]
        replacement_text = ", ".join(replacements)
        prompt = (
            f"Speak for 60 seconds about: {req.topic}. "
            f"Challenge: try using these upgrades in your speech: {replacement_text}. "
            f"Avoid filler words like 'um', 'like', and 'you know'."
        )

    session = PracticeSession(
        goal_id=goals[0].id if goals else None,
        prompt_text=prompt,
    )
    db.add(session)
    db.commit()

    return {"prompt": prompt}


@app.get("/progress")
def get_progress(db: Session = Depends(get_db)):
    """Compare metrics across all recordings for progress tracking."""
    analyses = (
        db.query(Analysis, Recording)
        .join(Recording, Analysis.recording_id == Recording.id)
        .order_by(Recording.created_at)
        .all()
    )

    if not analyses:
        return {"recordings": [], "summary": "No recordings yet."}

    timeline = []
    for analysis, recording in analyses:
        timeline.append({
            "recording_id": recording.id,
            "created_at": recording.created_at.isoformat() if recording.created_at else None,
            "filler_count": analysis.filler_count,
            "vocab_diversity": analysis.vocab_diversity,
            "words_per_minute": analysis.words_per_minute,
            "total_words": analysis.total_words,
        })

    # Summary: compare first vs last
    first = timeline[0]
    last = timeline[-1]
    summary = {
        "filler_change": last["filler_count"] - first["filler_count"],
        "vocab_diversity_change": round(last["vocab_diversity"] - first["vocab_diversity"], 3),
        "wpm_change": round(last["words_per_minute"] - first["words_per_minute"], 1),
        "total_recordings": len(timeline),
    }

    return {"timeline": timeline, "summary": summary}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
