"""
LexiFlow — Speech Analysis Engine
Analyzes transcripts for filler words, vocabulary diversity, word frequency, and WPM.
"""

import re
from collections import Counter
from typing import Any

# Filler words / weak phrases to detect
FILLER_WORDS = {
    "um", "uh", "uhh", "umm", "er", "ah", "like", "you know",
    "basically", "literally", "actually", "honestly", "right",
    "so", "well", "I mean", "kind of", "sort of", "stuff",
    "things", "whatever", "anyway", "obviously"
}

WEAK_WORDS = {
    "very", "really", "just", "things", "stuff", "got", "get",
    "good", "bad", "big", "small", "nice", "great", "a lot"
}

# Common stop words to exclude from "top repeated" analysis
STOP_WORDS = {
    "the", "a", "an", "is", "are", "was", "were", "be", "been",
    "being", "have", "has", "had", "do", "does", "did", "will",
    "would", "could", "should", "may", "might", "shall", "can",
    "to", "of", "in", "for", "on", "with", "at", "by", "from",
    "as", "into", "through", "during", "before", "after", "and",
    "but", "or", "nor", "not", "no", "it", "its", "this", "that",
    "these", "those", "i", "me", "my", "we", "our", "you", "your",
    "he", "she", "him", "her", "his", "they", "them", "their",
    "what", "which", "who", "whom", "where", "when", "how", "if",
    "then", "than", "so", "up", "out", "about", "also", "just",
    "more", "some", "any", "all", "each", "there", "here"
}


def tokenize(text: str) -> list[str]:
    """Lowercase and split text into word tokens."""
    text = text.lower()
    # Keep apostrophes in contractions, strip other punctuation
    text = re.sub(r"[^\w\s']", "", text)
    return text.split()


def detect_fillers(text: str) -> dict[str, int]:
    """Count occurrences of filler words/phrases in the transcript."""
    text_lower = text.lower()
    counts = {}

    # Check multi-word fillers first
    for filler in sorted(FILLER_WORDS, key=lambda x: -len(x)):
        pattern = r'\b' + re.escape(filler) + r'\b'
        matches = re.findall(pattern, text_lower)
        if matches:
            counts[filler] = len(matches)

    return counts


def analyze_transcript(transcript: str, duration_seconds: float) -> dict[str, Any]:
    """
    Full analysis of a speech transcript.

    Returns:
        - filler_count: total filler word occurrences
        - filler_words: breakdown by filler word
        - top_repeated_words: most used non-stop words
        - vocab_diversity: unique_words / total_words
        - words_per_minute: speech pace
        - word_data: visualization-ready format with word/count/category
    """
    tokens = tokenize(transcript)
    total_words = len(tokens)

    if total_words == 0:
        return {
            "filler_count": 0,
            "filler_words": {},
            "top_repeated_words": [],
            "vocab_diversity": 0.0,
            "words_per_minute": 0.0,
            "word_data": [],
            "total_words": 0,
            "unique_words": 0,
        }

    # --- Filler detection ---
    filler_counts = detect_fillers(transcript)
    filler_count = sum(filler_counts.values())

    # --- Word frequency (excluding stop words) ---
    content_words = [w for w in tokens if w not in STOP_WORDS]
    word_freq = Counter(content_words)
    top_repeated = word_freq.most_common(15)

    # --- Vocab diversity ---
    unique_words = len(set(tokens))
    vocab_diversity = round(unique_words / total_words, 3)

    # --- Words per minute ---
    duration_minutes = duration_seconds / 60.0 if duration_seconds > 0 else 1.0
    wpm = round(total_words / duration_minutes, 1)

    # --- Visualization data ---
    filler_set = {f.split()[0] for f in FILLER_WORDS}  # single-word forms for matching
    word_data = []
    for word, count in top_repeated:
        if word in filler_set or word in FILLER_WORDS:
            category = "filler"
        elif word in WEAK_WORDS:
            category = "weak"
        else:
            category = "normal"
        word_data.append({
            "word": word,
            "count": count,
            "category": category,
        })

    # Add fillers that might not be in top_repeated
    for filler, count in filler_counts.items():
        if not any(d["word"] == filler for d in word_data):
            word_data.append({
                "word": filler,
                "count": count,
                "category": "filler",
            })

    # Sort by count descending
    word_data.sort(key=lambda x: x["count"], reverse=True)

    return {
        "filler_count": filler_count,
        "filler_words": filler_counts,
        "top_repeated_words": [{"word": w, "count": c} for w, c in top_repeated],
        "vocab_diversity": vocab_diversity,
        "words_per_minute": wpm,
        "word_data": word_data,
        "total_words": total_words,
        "unique_words": unique_words,
    }
