"""
LexiFlow — Database Models (SQLite + SQLAlchemy for MVP)
"""

import datetime
import json
from sqlalchemy import create_engine, Column, Integer, Float, String, Text, Boolean, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = "sqlite:///./lexiflow.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Recording(Base):
    __tablename__ = "recordings"

    id = Column(Integer, primary_key=True, index=True)
    audio_path = Column(String, nullable=False)
    transcript = Column(Text, nullable=True)
    duration_seconds = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class Analysis(Base):
    __tablename__ = "analyses"

    id = Column(Integer, primary_key=True, index=True)
    recording_id = Column(Integer, nullable=False, index=True)
    filler_count = Column(Integer, default=0)
    vocab_diversity = Column(Float, default=0.0)
    words_per_minute = Column(Float, default=0.0)
    total_words = Column(Integer, default=0)
    unique_words = Column(Integer, default=0)
    # Store complex data as JSON strings
    word_freq_json = Column(Text, default="[]")
    filler_words_json = Column(Text, default="{}")
    word_data_json = Column(Text, default="[]")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    def set_word_data(self, data: list):
        self.word_data_json = json.dumps(data)

    def get_word_data(self) -> list:
        return json.loads(self.word_data_json)

    def set_filler_words(self, data: dict):
        self.filler_words_json = json.dumps(data)

    def get_filler_words(self) -> dict:
        return json.loads(self.filler_words_json)

    def set_word_freq(self, data: list):
        self.word_freq_json = json.dumps(data)

    def get_word_freq(self) -> list:
        return json.loads(self.word_freq_json)


class ReplacementGoal(Base):
    __tablename__ = "replacement_goals"

    id = Column(Integer, primary_key=True, index=True)
    old_phrase = Column(String, nullable=False)
    new_phrase = Column(String, nullable=False)
    context_example = Column(Text, nullable=True)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class PracticeSession(Base):
    __tablename__ = "practice_sessions"

    id = Column(Integer, primary_key=True, index=True)
    goal_id = Column(Integer, nullable=True)
    prompt_text = Column(Text, nullable=False)
    recording_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


def init_db():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
