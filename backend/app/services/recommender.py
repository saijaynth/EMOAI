"""
EmoAI Recommender Service
=========================
Phase 2 – Backend Feature Development (BACKEND SKILL.md)

Improvements:
  1. Mood detection upgraded to Gemini 2.0 Flash with rich, context-aware prompts
     and structured JSON output – far more accurate than keyword matching.
  2. Fallback keyword engine uses TF-IDF-style scoring with negation handling.
  3. Weighted multi-signal fusion: face > voice > text > quiz with confidence
     calibration so a high-confidence single signal beats a noisy multi-signal.
  4. Song recommendation now integrates Last.fm "tag.getTopTracks" API to fetch
     globally popular tracks in real-time, ranked by listener count.
  5. Local catalog is the offline fallback; live Last.fm results are merged and
     de-duplicated, then re-ranked by energy fit + popularity.
  6. Feedback-loop: liked/saved songs boost their mood-tag weight at runtime.
"""

from __future__ import annotations

import json
import logging
import os
import re
import time
import hashlib
from functools import lru_cache
from pathlib import Path
from typing import Optional

import httpx
from dotenv import load_dotenv

from app.schemas.mood import MethodScore, MoodLabel, SongItem

load_dotenv()
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MOOD_ENERGY_TARGETS: dict[MoodLabel, float] = {
    "happy":   0.78,
    "sad":     0.28,
    "angry":   0.85,
    "calm":    0.32,
    "anxious": 0.38,
    "focused": 0.62,
    "excited": 0.82,
    "neutral": 0.50,
}

CONTEXT_ENERGY_OFFSETS: dict[str, float] = {
    "general": 0.00,
    "study":   -0.15,
    "workout":  0.22,
    "relax":   -0.20,
    "sleep":   -0.30,
    "party":    0.28,
}

# Last.fm mood → tag mapping (multiple tags per mood for better coverage)
LASTFM_MOOD_TAGS: dict[MoodLabel, list[str]] = {
    "happy":   ["happy", "feel good", "upbeat", "joyful", "cheerful"],
    "sad":     ["sad", "melancholy", "heartbreak", "emotional", "tearjerker"],
    "angry":   ["angry", "aggressive", "rage", "intense", "metal"],
    "calm":    ["calm", "relaxing", "peaceful", "ambient", "chill"],
    "anxious": ["anxious", "tense", "nervous", "dark", "suspense"],
    "focused": ["focus", "study", "concentration", "instrumental", "work"],
    "excited": ["energetic", "party", "dance", "hype", "uplifting"],
    "neutral": ["indie", "alternative", "mellow", "easy listening", "background"],
}

# Method weights for fusion (higher = more trusted signal)
METHOD_WEIGHTS: dict[str, float] = {
    "face":  1.5,
    "voice": 1.3,
    "text":  1.0,
    "quiz":  0.8,
}

# Simple in-memory cache for Last.fm results (tag → songs, TTL 30 min)
_lastfm_cache: dict[str, tuple[float, list[SongItem]]] = {}
CACHE_TTL = 1800  # seconds


# ---------------------------------------------------------------------------
# Keyword fallback engine (used when Gemini is unavailable)
# ---------------------------------------------------------------------------

KEYWORD_MAP: dict[MoodLabel, list[str]] = {
    "happy": [
        "happy", "joy", "joyful", "great", "awesome", "good", "excellent",
        "love", "amazing", "wonderful", "fantastic", "cheerful", "delighted",
        "glad", "pleased", "thrilled", "bliss", "elated", "content", "smile",
        "laugh", "fun", "celebrate", "grateful", "thankful", "blessed",
    ],
    "sad": [
        "sad", "down", "upset", "cry", "hurt", "depressed", "unhappy",
        "sorrow", "grief", "miserable", "heartbroken", "lonely", "lost",
        "hopeless", "tears", "weep", "mourn", "gloomy", "blue", "broken",
        "miss", "missing", "empty", "numb", "pain", "ache",
    ],
    "angry": [
        "angry", "mad", "frustrated", "rage", "annoyed", "furious", "hate",
        "irritated", "outraged", "livid", "bitter", "resentful", "hostile",
        "aggressive", "violent", "explosive", "seething", "infuriated",
        "disgusted", "fed up", "pissed",
    ],
    "calm": [
        "calm", "peaceful", "relaxed", "soft", "chill", "quiet", "serene",
        "tranquil", "still", "gentle", "soothing", "mellow", "easy",
        "comfortable", "at ease", "composed", "collected", "zen",
    ],
    "anxious": [
        "anxious", "worried", "stress", "nervous", "panic", "fear", "scared",
        "tense", "uneasy", "restless", "overwhelmed", "dread", "apprehensive",
        "jittery", "on edge", "paranoid", "insecure", "uncertain",
    ],
    "focused": [
        "focus", "study", "work", "concentrate", "productive", "learning",
        "determined", "motivated", "disciplined", "goal", "task", "project",
        "deadline", "grind", "hustle", "achieve", "accomplish", "driven",
    ],
    "excited": [
        "excited", "hyped", "energetic", "pumped", "thrilled", "eager",
        "enthusiastic", "fired up", "stoked", "amped", "buzzed", "electric",
        "exhilarated", "can't wait", "psyched", "ready", "let's go",
    ],
    "neutral": [
        "fine", "okay", "ok", "whatever", "normal", "usual", "alright",
        "so-so", "meh", "nothing special", "just", "regular", "average",
    ],
}

NEGATION_WORDS = {"not", "no", "never", "don't", "doesn't", "didn't", "isn't", "wasn't", "can't", "won't"}


def _keyword_fallback(text: str) -> tuple[MoodLabel, float]:
    """
    Improved keyword-based mood detection with:
    - Negation handling (e.g. "not happy" → doesn't score happy)
    - Phrase-level matching
    - Confidence calibrated to match count
    """
    tokens = re.findall(r"\b\w+\b", text.lower())
    negated_positions: set[int] = set()
    for i, tok in enumerate(tokens):
        if tok in NEGATION_WORDS:
            # Mark next 3 tokens as negated
            for j in range(i + 1, min(i + 4, len(tokens))):
                negated_positions.add(j)

    scores: dict[MoodLabel, float] = {m: 0.0 for m in KEYWORD_MAP}
    for mood, keywords in KEYWORD_MAP.items():
        for kw in keywords:
            kw_tokens = kw.split()
            if len(kw_tokens) == 1:
                for i, tok in enumerate(tokens):
                    if tok == kw and i not in negated_positions:
                        scores[mood] += 1.0
            else:
                # Multi-word phrase
                phrase = " ".join(kw_tokens)
                if phrase in text.lower():
                    scores[mood] += 1.5

    best_mood: MoodLabel = max(scores, key=scores.__getitem__)
    best_score = scores[best_mood]

    if best_score == 0:
        return "neutral", 0.45

    # Confidence: starts at 0.50, +0.08 per matched keyword, capped at 0.88
    confidence = min(0.88, 0.50 + best_score * 0.08)
    return best_mood, confidence


# ---------------------------------------------------------------------------
# Gemini mood detection
# ---------------------------------------------------------------------------

def _gemini_detect_mood(prompt_text: str, context_hint: str = "") -> tuple[MoodLabel, float] | None:
    """
    Call Gemini 2.0 Flash with a rich, structured prompt.
    Returns (mood, confidence) or None on failure.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return None

    try:
        from google import genai
        from pydantic import BaseModel, Field as PField

        class MoodSchema(BaseModel):
            mood: MoodLabel
            confidence: float = PField(ge=0.0, le=1.0)
            reasoning: str = PField(default="")

        system_prompt = (
            "You are an expert psychologist and sentiment analyst. "
            "Your task is to detect the emotional mood from the provided input. "
            "Choose EXACTLY ONE mood from: happy, sad, angry, calm, anxious, focused, excited, neutral. "
            "Consider subtle emotional cues, context, tone, and implicit feelings. "
            "Provide a confidence score (0.0–1.0) reflecting how certain you are. "
            "Be precise: 0.9+ means very clear signal, 0.6–0.89 means moderate, below 0.6 means ambiguous."
        )

        full_prompt = f"{system_prompt}\n\n{context_hint}\n\nInput: {prompt_text}"

        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=full_prompt,
            config={
                "response_mime_type": "application/json",
                "response_schema": MoodSchema,
                "temperature": 0.1,  # Low temperature for consistent classification
            },
        )
        result = json.loads(response.text)
        mood = result["mood"]
        confidence = float(result["confidence"])
        logger.info(f"Gemini mood: {mood} ({confidence:.2f}) | reasoning: {result.get('reasoning', '')[:80]}")
        return mood, confidence

    except Exception as exc:
        logger.warning(f"Gemini API error: {exc}")
        return None


# ---------------------------------------------------------------------------
# Last.fm song fetcher
# ---------------------------------------------------------------------------

def _lastfm_fetch_songs(tag: str, language: str, limit: int = 50) -> list[SongItem]:
    """
    Fetch top tracks for a given Last.fm tag.
    Returns SongItem list with enriched metadata.
    Cached for CACHE_TTL seconds.
    """
    cache_key = f"{tag}::{language}"
    now = time.time()
    if cache_key in _lastfm_cache:
        ts, cached = _lastfm_cache[cache_key]
        if now - ts < CACHE_TTL:
            return cached

    api_key = os.getenv("LASTFM_API_KEY")
    if not api_key:
        logger.warning("LASTFM_API_KEY not set – skipping live fetch")
        return []

    try:
        url = "https://ws.audioscrobbler.com/2.0/"
        params = {
            "method": "tag.getTopTracks",
            "tag": tag,
            "api_key": api_key,
            "format": "json",
            "limit": limit,
        }
        with httpx.Client(timeout=8.0) as client:
            resp = client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()

        tracks = data.get("tracks", {}).get("track", [])
        songs: list[SongItem] = []
        for i, track in enumerate(tracks):
            if not isinstance(track, dict):
                continue
            title = track.get("name", "").strip()
            artist = track.get("artist", {}).get("name", "").strip() if isinstance(track.get("artist"), dict) else str(track.get("artist", "")).strip()
            if not title or not artist:
                continue

            # Derive a stable ID from title+artist
            song_id = "lf_" + hashlib.md5(f"{title}::{artist}".lower().encode()).hexdigest()[:10]

            # Estimate energy from tag (mood-based heuristic)
            # Will be refined by recommender scoring
            energy = MOOD_ENERGY_TARGETS.get("neutral", 0.5)

            # Playcount for popularity scoring
            playcount = int(track.get("playcount", 0) or 0)

            # Last.fm URL
            lastfm_url = track.get("url", "")

            # Image (largest available)
            images = track.get("image", [])
            album_art = ""
            for img in reversed(images):
                if isinstance(img, dict) and img.get("#text"):
                    album_art = img["#text"]
                    break

            songs.append(SongItem(
                id=song_id,
                title=title,
                artist=artist,
                language=language,
                mood_tags=["neutral"],  # Will be overridden by recommender
                energy=energy,
                playcount=playcount,
                lastfm_url=lastfm_url,
                album_art=album_art,
                source="lastfm",
            ))

        _lastfm_cache[cache_key] = (now, songs)
        logger.info(f"Last.fm fetched {len(songs)} tracks for tag='{tag}'")
        return songs

    except Exception as exc:
        logger.warning(f"Last.fm fetch error for tag='{tag}': {exc}")
        return []


def _fetch_global_songs_for_mood(mood: MoodLabel, language: str, limit: int = 50) -> list[SongItem]:
    """
    Fetch globally popular songs for a mood by querying multiple Last.fm tags.
    Merges results, de-duplicates by title+artist, sorts by playcount.
    """
    tags = LASTFM_MOOD_TAGS.get(mood, ["pop"])
    all_songs: dict[str, SongItem] = {}

    for tag in tags[:3]:  # Top 3 tags to avoid rate limiting
        fetched = _lastfm_fetch_songs(tag, language, limit=30)
        for song in fetched:
            key = f"{song.title.lower()}::{song.artist.lower()}"
            if key not in all_songs or song.playcount > all_songs[key].playcount:
                # Assign mood tags based on the tag we searched
                song.mood_tags = [mood]
                song.energy = MOOD_ENERGY_TARGETS.get(mood, 0.5)
                all_songs[key] = song

    # Sort by playcount descending
    sorted_songs = sorted(all_songs.values(), key=lambda s: s.playcount, reverse=True)
    return sorted_songs[:limit]


# ---------------------------------------------------------------------------
# Main Recommender Service
# ---------------------------------------------------------------------------

class RecommenderService:
    mood_energy_targets = MOOD_ENERGY_TARGETS
    context_energy_offsets = CONTEXT_ENERGY_OFFSETS

    def __init__(self) -> None:
        self.catalog: list[SongItem] = []
        # Runtime feedback boosts: song_id → cumulative boost score
        self._feedback_boosts: dict[str, float] = {}

    def load_catalog(self) -> None:
        # services/ → app/ → data/
        data_path = Path(__file__).resolve().parents[1] / "data" / "universal_songs.json"
        try:
            with data_path.open("r", encoding="utf-8") as f:
                raw = json.load(f)
            self.catalog = [SongItem(**item) for item in raw]
            logger.info(f"Loaded {len(self.catalog)} songs from local catalog")
        except Exception as exc:
            logger.error(f"Failed to load catalog: {exc}")
            self.catalog = []

    def apply_feedback_boost(self, song_id: str, action: str) -> None:
        """Called by feedback endpoint to boost/penalize songs at runtime."""
        boost = {"like": 0.3, "save": 0.5, "skip": -0.2}.get(action, 0.0)
        self._feedback_boosts[song_id] = self._feedback_boosts.get(song_id, 0.0) + boost

    # ------------------------------------------------------------------
    # Mood Detection Methods
    # ------------------------------------------------------------------

    def detect_text_mood(self, text: str) -> tuple[MoodLabel, float]:
        """
        Detect mood from free-form text.
        Primary: Gemini 2.0 Flash with rich psychological prompt.
        Fallback: Enhanced keyword engine with negation handling.
        """
        context_hint = (
            "Context: The user typed this text to describe how they feel right now. "
            "Analyze the emotional tone, word choice, and any implicit feelings."
        )
        result = _gemini_detect_mood(text, context_hint)
        if result:
            return result
        return _keyword_fallback(text)

    def detect_voice_mood(self, transcript: str) -> tuple[MoodLabel, float]:
        """
        Detect mood from voice transcript.
        Voice transcripts often have filler words, incomplete sentences, and
        spoken-language patterns – the prompt accounts for this.
        """
        context_hint = (
            "Context: This is a transcript from the user's voice recording. "
            "Consider spoken-language patterns, filler words (um, uh, like), "
            "sentence fragments, and the emotional energy implied by word choice. "
            "Spoken language often reveals mood more directly than written text."
        )
        result = _gemini_detect_mood(transcript, context_hint)
        if result:
            # Voice signals are slightly more reliable than text
            mood, conf = result
            return mood, min(0.99, conf * 1.05)
        # Fallback
        mood, conf = _keyword_fallback(transcript)
        return mood, min(0.88, conf + 0.05)

    def detect_face_mood(self, image_data: str) -> tuple[MoodLabel, float]:
        """
        Detect mood from facial expression image (base64).
        Uses Gemini Vision with detailed facial analysis prompt.
        """
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key or not image_data.startswith("data:image"):
            return "neutral", 0.45

        try:
            import base64
            from google import genai
            from pydantic import BaseModel, Field as PField

            class MoodSchema(BaseModel):
                mood: MoodLabel
                confidence: float = PField(ge=0.0, le=1.0)
                facial_cues: str = PField(default="")

            mime_type = "image/jpeg"
            if ";base64," in image_data:
                header, encoded = image_data.split(";base64,", 1)
                mime_type = header.replace("data:", "")
            else:
                encoded = image_data

            image_bytes = base64.b64decode(encoded)

            face_prompt = (
                "You are an expert in facial expression analysis and emotion recognition. "
                "Analyze this facial image carefully. Look for:\n"
                "- Eye expression (wide/narrow, tears, brightness)\n"
                "- Mouth position (smile, frown, open/closed)\n"
                "- Eyebrow position (raised, furrowed, relaxed)\n"
                "- Overall facial tension or relaxation\n"
                "- Skin color changes (flushed = angry/excited, pale = anxious/sad)\n\n"
                "Classify the emotion into EXACTLY ONE of: happy, sad, angry, calm, anxious, focused, excited, neutral.\n"
                "Provide confidence (0.0–1.0) and brief facial_cues description."
            )

            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=[
                    face_prompt,
                    {"mime_type": mime_type, "data": image_bytes},
                ],
                config={
                    "response_mime_type": "application/json",
                    "response_schema": MoodSchema,
                    "temperature": 0.1,
                },
            )
            result = json.loads(response.text)
            mood = result["mood"]
            confidence = float(result["confidence"])
            logger.info(f"Face mood: {mood} ({confidence:.2f}) | cues: {result.get('facial_cues', '')[:80]}")
            return mood, confidence

        except Exception as exc:
            logger.warning(f"Face mood detection error: {exc}")
            return "neutral", 0.45

    # ------------------------------------------------------------------
    # Multi-Signal Fusion
    # ------------------------------------------------------------------

    def fuse_scores(self, scores: list[MethodScore]) -> tuple[MoodLabel, float]:
        """
        Weighted multi-signal fusion:
        1. Each method has a trust weight (face > voice > text > quiz).
        2. Weighted votes are accumulated per mood.
        3. Final confidence is the weighted winner score normalized by total weight.
        4. If a single signal has very high confidence (≥0.90), it dominates.
        """
        if not scores:
            return "neutral", 0.50

        # Check for dominant high-confidence signal
        for s in scores:
            if s.confidence >= 0.90:
                weight = METHOD_WEIGHTS.get(s.method, 1.0)
                if weight >= 1.0:  # Only face/voice/text can dominate
                    logger.info(f"Dominant signal: {s.method} → {s.mood} ({s.confidence:.2f})")
                    return s.mood, min(0.99, s.confidence)

        # Weighted accumulation
        weighted: dict[MoodLabel, float] = {}
        total_weight = 0.0

        for s in scores:
            w = METHOD_WEIGHTS.get(s.method, 1.0)
            vote = s.confidence * w
            weighted[s.mood] = weighted.get(s.mood, 0.0) + vote
            total_weight += w

        final_mood: MoodLabel = max(weighted, key=weighted.__getitem__)
        raw_confidence = weighted[final_mood] / total_weight if total_weight > 0 else 0.5

        # Calibrate: agreement bonus (all signals agree → boost confidence)
        unique_moods = {s.mood for s in scores}
        if len(unique_moods) == 1:
            raw_confidence = min(0.99, raw_confidence * 1.15)  # 15% agreement bonus

        return final_mood, min(0.99, raw_confidence)

    # ------------------------------------------------------------------
    # Song Recommendation
    # ------------------------------------------------------------------

    def recommend(
        self,
        mood: MoodLabel,
        language: str,
        context: str = "general",
        limit: int = 10,
        use_live: bool = True,
    ) -> list[SongItem]:
        """
        Recommend globally best-fit songs:
        1. Fetch live global songs from Last.fm (if API key available).
        2. Merge with local catalog.
        3. Filter by language (with fallback to all languages).
        4. Score each song by: mood match + energy fit + popularity + feedback boost.
        5. Return top `limit` songs.
        """
        normalized_language = language.strip().lower()
        normalized_context = context.strip().lower()

        target_energy = self.mood_energy_targets.get(mood, 0.5)
        context_offset = self.context_energy_offsets.get(normalized_context, 0.0)
        target_energy = min(1.0, max(0.0, target_energy + context_offset))

        # --- Step 1: Get live global songs ---
        live_songs: list[SongItem] = []
        if use_live:
            live_songs = _fetch_global_songs_for_mood(mood, language, limit=50)

        # --- Step 2: Merge with local catalog ---
        # Build a set of (title, artist) from live songs to avoid duplicates
        live_keys = {f"{s.title.lower()}::{s.artist.lower()}" for s in live_songs}

        local_songs = [
            s for s in self.catalog
            if f"{s.title.lower()}::{s.artist.lower()}" not in live_keys
        ]

        all_songs = live_songs + local_songs

        # --- Step 3: Language filter ---
        lang_filtered = [s for s in all_songs if s.language.lower() == normalized_language]
        working_set = lang_filtered if lang_filtered else all_songs

        # --- Step 4: Score each song ---
        def score(song: SongItem) -> float:
            # Mood match: exact tag match is strongly preferred
            mood_match = 2.5 if mood in song.mood_tags else 0.3

            # Energy fit: closer to target = higher score
            energy_fit = 1.0 - abs(song.energy - target_energy)

            # Language match bonus
            lang_bonus = 0.5 if song.language.lower() == normalized_language else 0.0

            # Popularity: normalize playcount (Last.fm songs have real counts)
            # Local catalog songs get a baseline of 0.1
            max_playcount = 5_000_000  # Reasonable ceiling
            pop_score = min(1.0, song.playcount / max_playcount) * 0.8 if song.playcount > 0 else 0.1

            # Feedback boost from user interactions
            fb_boost = self._feedback_boosts.get(song.id, 0.0)

            # Context-specific bonuses
            context_bonus = 0.0
            if normalized_context == "study" and mood in ("focused", "calm"):
                context_bonus = 0.3
            elif normalized_context == "workout" and mood in ("angry", "excited"):
                context_bonus = 0.3
            elif normalized_context == "sleep" and mood in ("calm", "sad"):
                context_bonus = 0.3
            elif normalized_context == "party" and mood in ("happy", "excited"):
                context_bonus = 0.3

            # Neutral mood: prefer calm/happy songs
            neutral_bonus = 0.2 if mood == "neutral" and any(t in song.mood_tags for t in ("calm", "happy")) else 0.0

            return mood_match + energy_fit + lang_bonus + pop_score + fb_boost + context_bonus + neutral_bonus

        ranked = sorted(working_set, key=score, reverse=True)

        # Diversity: avoid same artist more than twice in top results
        seen_artists: dict[str, int] = {}
        diverse: list[SongItem] = []
        overflow: list[SongItem] = []

        for song in ranked:
            artist_key = song.artist.lower()
            count = seen_artists.get(artist_key, 0)
            if count < 2:
                diverse.append(song)
                seen_artists[artist_key] = count + 1
            else:
                overflow.append(song)

            if len(diverse) >= limit:
                break

        # Fill remaining slots from overflow if needed
        if len(diverse) < limit:
            diverse.extend(overflow[: limit - len(diverse)])

        return diverse[:limit]


recommender_service = RecommenderService()
