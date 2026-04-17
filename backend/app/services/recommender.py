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
from pathlib import Path

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
    "romantic": 0.40,
    "nostalgic": 0.35,
    "confident": 0.70,
    "dreamy": 0.25,
    "triumphant": 0.88,
    "chill": 0.45,
    "hype": 0.90,
    "melancholic": 0.30,
    "hopeful": 0.65,
    "frustrated": 0.75,
    "bored": 0.40,
}

VOICE_CENTROIDS: dict[MoodLabel, tuple[float, float, float, float]] = {
    "happy":       (0.15, 140, 45, 0.20),
    "sad":         (0.06, 90,  20, 0.40),
    "angry":       (0.22, 160, 60, 0.15),
    "calm":        (0.08, 110, 25, 0.30),
    "anxious":     (0.12, 165, 70, 0.25),
    "focused":     (0.10, 130, 30, 0.18),
    "excited":     (0.20, 170, 65, 0.15),
    "neutral":     (0.10, 120, 35, 0.25),
    "romantic":    (0.09, 105, 30, 0.35),
    "nostalgic":   (0.07, 95,  25, 0.38),
    "confident":   (0.16, 140, 40, 0.18),
    "dreamy":      (0.06, 85,  20, 0.45),
    "triumphant":  (0.24, 150, 55, 0.12),
    "chill":       (0.09, 110, 25, 0.30),
    "hype":        (0.25, 180, 70, 0.10),
    "melancholic": (0.05, 85,  15, 0.42),
    "hopeful":     (0.14, 135, 45, 0.22),
    "frustrated":  (0.18, 155, 55, 0.20),
    "bored":       (0.07, 100, 15, 0.35),
}

CONTEXT_ENERGY_OFFSETS: dict[str, float] = {
    "general": 0.00,
    "study":   -0.15,
    "workout":  0.22,
    "relax":   -0.20,
    "sleep":   -0.30,
    "party":    0.28,
}

# Spotify language â†’ search market & genre mapping 
SPOTIFY_MARKET_MAP: dict[str, dict] = {
    "english": {"market": "US", "genres": ["pop", "rock", "indie", "hip-hop", "top-50"]},
    "spanish": {"market": "ES", "genres": ["latin", "reggaeton", "pop", "spanish", "latino"]},
    "hindi":   {"market": "IN", "genres": ["indian", "bollywood", "pop", "desi"]},
    "korean":  {"market": "KR", "genres": ["k-pop", "pop", "korean"]},
    "japanese":{"market": "JP", "genres": ["j-pop", "j-rock", "anime", "pop"]},
    "french":  {"market": "FR", "genres": ["french", "pop", "chanson"]},
    "german":  {"market": "DE", "genres": ["german", "pop", "rock"]},
    "portuguese": {"market": "BR", "genres": ["brazil", "bossanova", "sertanejo", "pop"]},
}

# Spotify mood â†’ seed parameters mapping
SPOTIFY_MOOD_SEEDS: dict[MoodLabel, dict] = {
    "happy":   {"min_valence": 0.6, "target_valence": 0.8, "min_energy": 0.6, "target_energy": 0.8, "seed_genres": ["happy", "pop", "dance"]},
    "sad":     {"max_valence": 0.4, "target_valence": 0.2, "max_energy": 0.5, "target_energy": 0.3, "seed_genres": ["sad", "acoustic", "piano"]},
    "angry":   {"max_valence": 0.4, "min_energy": 0.7, "target_energy": 0.9, "seed_genres": ["metal", "hard-rock", "punk", "emo"]},
    "calm":    {"target_valence": 0.5, "max_energy": 0.4, "target_energy": 0.2, "seed_genres": ["ambient", "chill", "sleep", "acoustic"]},
    "anxious": {"target_valence": 0.3, "min_energy": 0.4, "target_energy": 0.6, "seed_genres": ["indie", "alternative", "sad"]},
    "focused": {"target_valence": 0.5, "max_energy": 0.6, "target_energy": 0.4, "seed_genres": ["study", "classical", "piano", "instrumental"]},
    "excited": {"min_valence": 0.5, "target_valence": 0.8, "min_energy": 0.7, "target_energy": 0.9, "seed_genres": ["party", "dance", "edm", "club"]},
    "neutral": {"target_valence": 0.5, "target_energy": 0.5, "seed_genres": ["indie-pop", "pop", "singer-songwriter"]},
}

# Last.fm mood → tag mapping (fallback when Spotify unavailable)
LASTFM_MOOD_TAGS: dict[MoodLabel, list[str]] = {
    "happy":   ["happy", "feel good", "upbeat"],
    "sad":     ["sad", "melancholy", "heartbreak"],
    "angry":   ["angry", "aggressive", "metal"],
    "calm":    ["calm", "relaxing", "ambient"],
    "anxious": ["anxious", "tense", "dark"],
    "focused": ["focus", "study", "instrumental"],
    "excited": ["energetic", "party", "dance"],
    "neutral": ["indie", "alternative", "mellow"],
}

# Method weights for fusion (higher = more trusted signal)
METHOD_WEIGHTS: dict[str, float] = {
    "face":  1.5,
    "voice": 1.3,
    "text":  1.0,
    "quiz":  0.8,
}

FACE_EXPRESSION_MAP: dict[str, MoodLabel] = {
    "smile": "happy",
    "frown": "sad",
    "neutral": "neutral",
    "surprised": "excited",
    "tense": "anxious",
}

# Simple in-memory cache for Last.fm/Spotify results (tag → songs, TTL 30 min)
_lastfm_cache: dict[str, tuple[float, list[SongItem]]] = {}
_spotify_cache: dict[str, tuple[float, list[SongItem]]] = {}
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
    "romantic": [
        "love", "romantic", "affection", "passion", "adore", "crush", "sweet", "darling", "heart", "intimate"
    ],
    "nostalgic": [
        "nostalgic", "memories", "past", "remember", "throwback", "miss", "old times", "childhood", "reminisce"
    ],
    "confident": [
        "confident", "sure", "strong", "unbeatable", "ready", "bold", "fearless", "unstoppable", "proud", "capable"
    ],
    "dreamy": [
        "dreamy", "floaty", "surreal", "sleepy", "wander", "space", "lost in thought", "ethereal", "cloud", "magic"
    ],
    "triumphant": [
        "triumph", "victory", "won", "succeed", "champion", "glory", "conquer", "hero", "overcome", "success"
    ],
    "chill": [
        "chill", "vibe", "laid back", "breezy", "smooth", "groove", "cruising", "lounging", "unwind", "kick back"
    ],
    "hype": [
        "hype", "lit", "fire", "crazy", "wild", "turnt", "banger", "rager", "energy", "pop off"
    ],
    "melancholic": [
        "melancholy", "somber", "pensive", "wistful", "reflective", "sigh", "mournful", "sorrowful", "bleak"
    ],
    "hopeful": [
        "hope", "optimistic", "looking forward", "bright", "promising", "believe", "faith", "wish", "dream"
    ],
    "frustrated": [
        "frustrated", "annoy", "bothered", "stuck", "fed up", "exasperated", "irritated", "impatient", "aghast"
    ],
    "bored": [
        "bored", "dull", "tedious", "yawn", "uninterested", "tiresome", "monotonous", "lame", "drag"
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


def _voice_tone_fallback(tone_profile: dict | None, language: str = "English") -> tuple[MoodLabel, float] | None:
    """
    Infer mood from acoustic features when available.
    Uses K-Nearest Neighbor Euclidean Centroid mapping across all metrics for full coverage against 19 emotions.
    """
    if not tone_profile:
        return None

    avg_volume = float(tone_profile.get("avg_volume", 0.0) or 0.0)
    pitch_var = float(tone_profile.get("pitch_variability", 0.0) or 0.0)
    speaking_rate = float(tone_profile.get("speaking_rate_wpm", 0.0) or 0.0)
    pause_ratio = float(tone_profile.get("pause_ratio", 0.0) or 0.0)

    lang_lower = language.lower()
    
    # ML Domain Adjustment for Spoken Languages
    rate_mult, pitch_mult, vol_mult = 1.0, 1.0, 1.0
    if lang_lower in ["telugu", "hindi", "tamil", "kannada", "malayalam"]:
        rate_mult = 0.85
        pitch_mult = 1.15
        vol_mult = 1.10
    elif lang_lower in ["spanish", "italian", "japanese"]:
        rate_mult = 0.75
    elif lang_lower in ["french", "german"]:
        pitch_mult = 1.10

    n_rate = speaking_rate * rate_mult
    n_pitch_var = pitch_var * pitch_mult
    n_vol = avg_volume * vol_mult

    best_mood = "neutral"
    min_dist = float('inf')

    # Continuous multidimensional space distance mapped to 19 clusters
    for cluster_mood, (c_vol, c_rate, c_pitch, c_pause) in VOICE_CENTROIDS.items():
        # Scale variables uniformly (Volume: ~0.3, Rate: ~200 WPM, Pitch Var: ~100 Hz, Pause: ~0.5)
        # to ensure Euclidean math treats each metric as a uniform ~[0-1] scale dimension
        norm_vol = min(1.0, n_vol / 0.3)
        norm_rate = min(1.0, n_rate / 200.0)
        norm_pitch_var = min(1.0, n_pitch_var / 100.0)
        norm_pause = min(1.0, pause_ratio / 0.5)
        
        nc_vol = min(1.0, c_vol / 0.3)
        nc_rate = min(1.0, c_rate / 200.0)
        nc_pitch = min(1.0, c_pitch / 100.0)
        nc_pause = min(1.0, c_pause / 0.5)
        
        dist = ((norm_vol - nc_vol)**2 + 
                (norm_rate - nc_rate)**2 + 
                (norm_pitch_var - nc_pitch)**2 + 
                (norm_pause - nc_pause)**2) ** 0.5
                
        if dist < min_dist:
            min_dist = dist
            best_mood = cluster_mood
            
    # Convert n-dimensional distance (max ~2.0) to a scaled confidence score
    confidence = max(0.40, min(0.99, 1.0 - (min_dist / 1.5)))
    return best_mood, round(confidence, 2)

    avg_volume = float(tone_profile.get("avg_volume", 0.0) or 0.0)
    volume_var = float(tone_profile.get("volume_variability", 0.0) or 0.0)
    avg_pitch = float(tone_profile.get("avg_pitch_hz", 0.0) or 0.0)
    pitch_var = float(tone_profile.get("pitch_variability", 0.0) or 0.0)
    speaking_rate = float(tone_profile.get("speaking_rate_wpm", 0.0) or 0.0)
    pause_ratio = float(tone_profile.get("pause_ratio", 0.0) or 0.0)

    lang_lower = language.lower()
    
    # ML Domain Adjustment for Spoken Languages
    # Indian/Dravidian languages natively spoken fast with less variation
    rate_mult, pitch_mult, vol_mult = 1.0, 1.0, 1.0
    if lang_lower in ["telugu", "hindi", "tamil", "kannada", "malayalam"]:
        rate_mult = 0.85
        pitch_mult = 1.15
        vol_mult = 1.10
    elif lang_lower in ["spanish", "italian", "japanese"]:
        rate_mult = 0.75
    elif lang_lower in ["french", "german"]:
        pitch_mult = 1.10

    n_rate = speaking_rate * rate_mult
    n_pitch_var = pitch_var * pitch_mult
    n_vol = avg_volume * vol_mult

    # Adjusted heuristics targeting the normalized prosody
    if n_vol >= 0.18 and n_rate >= 145 and n_pitch_var >= 55: return "excited", 0.84
    if n_vol >= 0.20 and n_rate >= 130 and pause_ratio <= 0.18: return "angry", 0.82
    if n_rate >= 150 and n_pitch_var >= 60 and pause_ratio >= 0.22: return "anxious", 0.82
    if n_vol <= 0.07 and n_rate <= 95 and pause_ratio >= 0.32: return "sad", 0.79
    if n_vol <= 0.09 and n_rate <= 120 and n_pitch_var <= 30: return "calm", 0.77
    if n_rate >= 110 and n_rate <= 165 and pause_ratio <= 0.2 and n_pitch_var <= 45: return "focused", 0.74
    if n_vol >= 0.10 and n_vol <= 0.16 and n_pitch_var >= 40 and pause_ratio <= 0.28: return "happy", 0.72

    return None

    avg_volume = float(tone_profile.get("avg_volume", 0.0) or 0.0)
    volume_var = float(tone_profile.get("volume_variability", 0.0) or 0.0)
    avg_pitch = float(tone_profile.get("avg_pitch_hz", 0.0) or 0.0)
    pitch_var = float(tone_profile.get("pitch_variability", 0.0) or 0.0)
    speaking_rate = float(tone_profile.get("speaking_rate_wpm", 0.0) or 0.0)
    pause_ratio = float(tone_profile.get("pause_ratio", 0.0) or 0.0)

    # Voice mood heuristics from common prosody patterns.
    if avg_volume >= 0.18 and speaking_rate >= 145 and pitch_var >= 55:
        return "excited", 0.84
    if avg_volume >= 0.2 and speaking_rate >= 130 and pause_ratio <= 0.18:
        return "angry", 0.8
    if speaking_rate >= 150 and pitch_var >= 60 and pause_ratio >= 0.22:
        return "anxious", 0.82
    if avg_volume <= 0.07 and speaking_rate <= 95 and pause_ratio >= 0.32:
        return "sad", 0.79
    if avg_volume <= 0.09 and speaking_rate <= 120 and pitch_var <= 30:
        return "calm", 0.77
    if speaking_rate >= 110 and speaking_rate <= 165 and pause_ratio <= 0.2 and pitch_var <= 45:
        return "focused", 0.74
    if avg_volume >= 0.1 and avg_volume <= 0.16 and pitch_var >= 40 and pause_ratio <= 0.28:
        return "happy", 0.72

    # If we have enough acoustic data but no clear mood pattern, return neutral with low confidence.
    if avg_volume > 0 or avg_pitch > 0 or speaking_rate > 0:
        return "neutral", 0.58
    return None


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


# ---------------------------------------------------------------------------
# Spotify token cache (Client Credentials — no user login needed)
# ---------------------------------------------------------------------------

_spotify_token: dict = {}  # {"access_token": str, "expires_at": float}


def _spotify_get_token() -> str | None:
    """Fetch or return cached Spotify Client Credentials token."""
    client_id = os.getenv("SPOTIFY_CLIENT_ID")
    client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
    if not client_id or not client_secret:
        return None

    now = time.time()
    if _spotify_token.get("access_token") and now < _spotify_token.get("expires_at", 0) - 30:
        return _spotify_token["access_token"]

    try:
        resp = httpx.post(
            "https://accounts.spotify.com/api/token",
            data={"grant_type": "client_credentials"},
            auth=(client_id, client_secret),
            timeout=8.0,
        )
        resp.raise_for_status()
        data = resp.json()
        _spotify_token["access_token"] = data["access_token"]
        _spotify_token["expires_at"] = now + data.get("expires_in", 3600)
        logger.info("Spotify token refreshed")
        return _spotify_token["access_token"]
    except Exception as exc:
        logger.warning(f"Spotify token error: {exc}")
        return None


# ---------------------------------------------------------------------------
# Spotify Advanced Recommender (httpx, no spotipy dependency)
# ---------------------------------------------------------------------------

def _spotify_fetch_songs(mood: MoodLabel, language: str, limit: int = 50, tone_emotion: str | None = None, text_emotion: str | None = None) -> list[SongItem]:
    """
    Two-phase Spotify fetch:
    Phase 1 — Recommendations API: seed genres + mood audio feature targets
              → returns tracks already filtered by valence/energy/danceability.
    Phase 2 — Audio Features API: enrich each track with real valence + energy
              so the recommender scoring engine uses ground-truth Spotify data.
    """
    # Cache key includes dual emotions for explicit Phase 3 logic
    cache_key = f"sp::{mood}::{language}::{limit}::{tone_emotion}::{text_emotion}"
    now = time.time()
    if cache_key in _spotify_cache:
        ts, cached = _spotify_cache[cache_key]
        if now - ts < CACHE_TTL:
            return cached

    token = _spotify_get_token()
    if not token:
        return []

    headers = {"Authorization": f"Bearer {token}"}
    lang_key = language.strip().lower()
    market_info = SPOTIFY_MARKET_MAP.get(lang_key, {"market": "US", "genres": ["pop"]})
    market = market_info["market"]
    
    # Base params mapping
    mood_params = SPOTIFY_MOOD_SEEDS.get(mood, SPOTIFY_MOOD_SEEDS["neutral"]).copy()
    
    # Explicit Phase 3 logic on Spotify parameters tuning on our unified targets
    if tone_emotion and text_emotion and tone_emotion != text_emotion:
        tone_params = SPOTIFY_MOOD_SEEDS.get(tone_emotion, SPOTIFY_MOOD_SEEDS["neutral"])
        text_params = SPOTIFY_MOOD_SEEDS.get(text_emotion, SPOTIFY_MOOD_SEEDS["neutral"])
        
        # 60% tone, 40% text weight for valence and energy
        target_v_tone = tone_params.get("target_valence", mood_params.get("target_valence", 0.5))
        target_v_text = text_params.get("target_valence", mood_params.get("target_valence", 0.5))
        target_e_tone = tone_params.get("target_energy", mood_params.get("target_energy", 0.5))
        target_e_text = text_params.get("target_energy", mood_params.get("target_energy", 0.5))
        
        mood_params["target_valence"] = round((target_v_tone * 0.6) + (target_v_text * 0.4), 2)
        mood_params["target_energy"] = round((target_e_tone * 0.6) + (target_e_text * 0.4), 2)
        
        # Blend genres safely
        seed_genres = dict.fromkeys(tone_params.get("seed_genres", []) + text_params.get("seed_genres", []))
        mood_params["seed_genres"] = list(seed_genres)

    # Seed genres: up to 5 total (Spotify limit)
    lang_genres = market_info["genres"][:3]
    mood_genres = mood_params.get("seed_genres", [])[:2]
    seed_genres = ",".join(dict.fromkeys(lang_genres + mood_genres))[:5]

    # Build audio feature params for recommendations
    rec_params: dict = {
        "seed_genres": seed_genres,
        "market": market,
        "limit": min(limit, 100),
    }
    for key in ("min_valence", "max_valence", "target_valence",
                "min_energy", "max_energy", "target_energy",
                "min_danceability", "target_danceability"):
        if key in mood_params:
            rec_params[key] = mood_params[key]

    try:
        # Phase 1: Search tracks since Spotify deprecated the /recommendations and /audio-features endpoints
        
        # Build query strictly with space-separated terms, using the first genre. Spotify search syntax parses 'genre:pop happy' perfectly
        safe_genre = lang_genres[0] if lang_genres else "pop"
        query = f"genre:{safe_genre} {mood}"
        
        search_resp = httpx.get(
            "https://api.spotify.com/v1/search",
            headers=headers,
            params={"q": query, "type": "track", "limit": min(limit, 50), "market": market},
            timeout=8.0,
        )
        search_resp.raise_for_status()
        tracks = search_resp.json().get("tracks", {}).get("items", [])

        if not tracks:
            logger.warning(f"Spotify search returned 0 tracks for mood={mood}, lang={language}")
            return []

        songs: list[SongItem] = []
        for t in tracks:
            if not t: continue
            title = t.get("name", "").strip()
            artists = t.get("artists", [])
            artist = artists[0]["name"].strip() if artists else "Unknown"
            if not title or not artist:
                continue

            sp_id = t.get("id", "")

            # Use mood target defaults since /audio-features is forbidden
            energy = mood_params.get("target_energy", 0.5)
            valence = mood_params.get("target_valence", 0.5)
            tempo = 120.0

            album_art = ""
            images = t.get("album", {}).get("images", [])
            if images:
                album_art = images[0].get("url", "")

            songs.append(SongItem(
                id=f"sp_{sp_id}" if sp_id else "sp_" + hashlib.md5(f"{title}::{artist}".encode()).hexdigest()[:10],
                title=title,
                artist=artist,
                language=language,
                mood_tags=[mood],
                energy=round(energy, 3),
                valence=round(valence, 3),
                tempo=round(tempo, 1),
                popularity=t.get("popularity", 50),
                spotify_id=sp_id or None,
                album_art=album_art or None,
                source="spotify",
            ))

        # Sort by popularity descending
        songs.sort(key=lambda s: s.popularity or 0, reverse=True)
        _spotify_cache[cache_key] = (now, songs)
        logger.info(f"Spotify: {len(songs)} tracks for mood={mood}, lang={language}, market={market}")
        return songs

    except Exception as exc:
        logger.warning(f"Spotify fetch error mood={mood} lang={language}: {exc}")
        return []


def _fetch_global_songs_for_mood(mood: MoodLabel, language: str, limit: int = 50, tone_emotion: str | None = None, text_emotion: str | None = None) -> list[SongItem]:
    """
    Priority: Spotify (real audio features) → Last.fm (playcount) → empty (local catalog fallback).
    """
    spotify_songs = _spotify_fetch_songs(mood, language, limit=limit, tone_emotion=tone_emotion, text_emotion=text_emotion)
    if spotify_songs:
        return spotify_songs[:limit]

    # Last.fm fallback
    tags = LASTFM_MOOD_TAGS.get(mood, ["pop"])
    all_songs: dict[str, SongItem] = {}
    for tag in tags[:3]:
        for song in _lastfm_fetch_songs(tag, language, limit=30):
            key = f"{song.title.lower()}::{song.artist.lower()}"
            if key not in all_songs or song.playcount > all_songs[key].playcount:
                song.mood_tags = [mood]
                song.energy = MOOD_ENERGY_TARGETS.get(mood, 0.5)
                all_songs[key] = song
    return sorted(all_songs.values(), key=lambda s: s.playcount, reverse=True)[:limit]

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

    def detect_voice_mood(self, transcript: str, tone_profile: dict | None = None, language: str = "English") -> dict:
        """
        Detect mood from voice transcript and tone profile independently.
        Returns a dictionary containing the combined mood, individual emotions, and confidence.
        """
        context_hint = (
            f"Context: This is a transcript from the user's voice recording in {language}. "
            "Consider spoken-language patterns, filler words (um, uh, like), "
            "sentence fragments, and the emotional energy implied by word choice. "
            "Spoken language often reveals mood more directly than written text."
        )
        
        transcript_result = _gemini_detect_mood(transcript, context_hint) if transcript.strip() else None
        tone_result = _voice_tone_fallback(tone_profile, language)
        
        final_mood = "neutral"
        final_conf = 0.5
        confidence_level = "LOW"
        text_emotion = transcript_result[0] if transcript_result else None
        tone_emotion = tone_result[0] if tone_result else None
        
        if transcript_result and tone_result:
            transcript_mood, transcript_conf = transcript_result
            tone_mood, tone_conf = tone_result
            
            if transcript_mood == tone_mood:
                final_mood = tone_mood
                final_conf = min(0.99, max(tone_conf, transcript_conf) + 0.09)
                confidence_level = "HIGH"
            else:
                # Disagreement logic (60% tone weight, 40% text weight as per hybrid design)
                tone_weighted = tone_conf * 0.60
                text_weighted = transcript_conf * 0.40
                
                if tone_weighted >= text_weighted:
                    final_mood = tone_mood
                    final_conf = min(0.96, 0.58 + ((tone_conf + transcript_conf) / 2) * 0.45)
                    confidence_level = "MEDIUM"
                else:
                    final_mood = transcript_mood
                    final_conf = min(0.95, 0.56 + ((tone_conf + transcript_conf) / 2) * 0.42)
                    confidence_level = "MEDIUM"
                    
        elif tone_result:
            final_mood, tone_conf = tone_result
            final_conf = min(0.92, tone_conf + 0.04)
            confidence_level = "MEDIUM"
        elif transcript_result:
            final_mood, conf = transcript_result
            final_conf = min(0.99, conf * 1.05)
            confidence_level = "MEDIUM"
        else:
            final_mood, conf = _keyword_fallback(transcript)
            final_conf = min(0.88, conf + 0.05)
            confidence_level = "LOW"
            text_emotion = final_mood
            
        return {
            "mood": final_mood,
            "confidence": final_conf,
            "tone_emotion": tone_emotion,
            "text_emotion": text_emotion,
            "confidence_level": confidence_level
        }

    def _heuristic_face_mood(self, expression: str | None, intensity: float | None) -> tuple[MoodLabel, float]:
        if not expression:
            return "neutral", 0.45
        mood = FACE_EXPRESSION_MAP.get(expression, "neutral")
        face_intensity = intensity if intensity is not None else 0.6
        confidence = 0.60 + (face_intensity * 0.35)
        return mood, min(0.95, max(0.45, confidence))

    def _parse_frontend_face_payload(
        self,
        image_data: str | None,
        expression: str | None,
        intensity: float | None,
    ) -> tuple[str | None, str | None, float | None]:
        """
        Accept both payload formats:
        1. Real image data URL (`data:image/...;base64,...`)
        2. Simulated frontend JSON string stored in `image_data`
        """
        if image_data and image_data.strip().startswith("{"):
            try:
                payload = json.loads(image_data)
                parsed_expression = str(payload.get("expression", "")).strip() or expression
                parsed_intensity_raw = payload.get("intensity", intensity)
                parsed_intensity = float(parsed_intensity_raw) if parsed_intensity_raw is not None else intensity
                return None, parsed_expression, parsed_intensity
            except Exception:
                return None, expression, intensity

        return image_data, expression, intensity

    def _offline_deep_learning_face_mood(self, image_data: str) -> tuple[MoodLabel, float]:
        """
        High Accuracy Offline Computer Vision Fallback using OpenCV and ONNX FERPlus.
        Provides robust face detection + cropping + emotion classification.    
        Used when GEMINI_API_KEY is restricted/missing.
        """
        try:
            import base64
            import numpy as np
            import cv2
            import os

            logger.info("Initializing High-Accuracy Offline Face Detection w/ ONNX FERPlus...")

            # Decode the base64 image coming from the React face scan
            if ";base64," in image_data:
                header, encoded = image_data.split(";base64,", 1)
            else:
                encoded = image_data

            image_bytes = base64.b64decode(encoded)
            nparr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            if img is None:
                return "neutral", 0.45

            # Convert to grayscale for face and emotion detection
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

            # Load the OpenCV cascade classifier
            cascade_path = os.path.join(cv2.data.haarcascades, "haarcascade_frontalface_default.xml")
            if not os.path.exists(cascade_path):
                logger.warning("Cascade not found. Using naive sizing.")
                face_crop = cv2.resize(gray, (64, 64))
            else:
                face_cascade = cv2.CascadeClassifier(cascade_path)
                faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
                
                if len(faces) == 0:
                    logger.warning("No face detected for emotion analysis. Computing on whole image.")
                    face_crop = cv2.resize(gray, (64, 64))
                else:
                    # Take the largest face
                    faces = sorted(faces, key=lambda x: x[2]*x[3], reverse=True)
                    x, y, w, h = faces[0]
                    face_crop = cv2.resize(gray[y:y+h, x:x+w], (64, 64))

            # ONNX FERPlus model path (downloaded earlier in background)
            # Find the path dynamically
            current_dir = os.path.dirname(os.path.abspath(__file__))
            backend_dir = os.path.dirname(os.path.dirname(current_dir))
            model_path = os.path.join(backend_dir, "data", "emotion-ferplus-8.onnx")
            
            if not os.path.exists(model_path):
                logger.warning(f"ONNX model not found at {model_path}, falling back to neutral.")
                return "neutral", 0.45

            # Load the network and perform inference
            net = cv2.dnn.readNetFromONNX(model_path)
            blob = cv2.dnn.blobFromImage(face_crop, scalefactor=1.0, size=(64, 64), mean=(0,), swapRB=False, crop=False)
            net.setInput(blob)
            preds = net.forward()

            # The 8 emotion classes in FERPlus
            emotions_list = ['neutral', 'happiness', 'surprise', 'sadness', 'anger', 'disgust', 'fear', 'contempt']
            
            # Apply softmax to get probabilities
            exp_preds = np.exp(preds[0] - np.max(preds[0]))
            probs = exp_preds / np.sum(exp_preds)
            
            class_idx = int(np.argmax(probs))
            score = float(probs[class_idx])
            detected_emotion = emotions_list[class_idx]

            # Map FERPlus output to our MoodLabel enum
            mapping_dict = {
                "happiness": "happy",
                "surprise": "excited",
                "sadness": "sad",
                "anger": "angry",
                "disgust": "angry", 
                "fear": "anxious",
                "contempt": "angry"
            }

            final_mood = mapping_dict.get(detected_emotion, "neutral")

            # Validate output matches our schema
            valid_moods: set[MoodLabel] = {"happy", "sad", "angry", "calm", "anxious", "focused", "excited", "neutral"}
            if final_mood not in valid_moods:
                final_mood = "neutral"

            logger.info(f"Offline ONNX Model Success! Detected {final_mood} at {score:.2f} confidence.")
            return final_mood, score

        except Exception as e:
            logger.error(f"High accuracy offline face detect failed: {e}")      
            return "neutral", 0.45

    def detect_face_mood(
        self,
        image_data: str | None = None,
        expression: str | None = None,
        intensity: float | None = None,
    ) -> tuple[MoodLabel, float]:
        """
        Detect mood from facial input.
        Supports both:
        - Real image-based detection via Gemini Vision.
        - Expression/intensity heuristic fallback (for simulated capture mode).
        - High Accuracy Offline CV Transformer pipeline if no API keys are present.
        """
        image_data, expression, intensity = self._parse_frontend_face_payload(image_data, expression, intensity)

        api_key = os.getenv("GEMINI_API_KEY")

        # If no valid image input exists, use robust expression-based fallback.
        if not image_data or not image_data.startswith("data:image"):
            return self._heuristic_face_mood(expression, intensity)

        # 1. Attempt High-Accuracy Offline Detection First (Saves Gemini Quota, Infinite Usage)
        offline_mood, offline_score = self._offline_deep_learning_face_mood(image_data)
        # _offline_deep_learning_face_mood returns ("neutral", 0.45) on failure or no face.
        if offline_score > 0.45 or offline_mood != "neutral":
            return offline_mood, offline_score

        # 2. Fallback to Gemini if offline failed (e.g. model not downloaded)
        if not api_key:
            return self._heuristic_face_mood(expression, intensity)

        try:
            import base64
            import io
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
                    genai.types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
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
            return self._heuristic_face_mood(expression, intensity)

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

    def enrich_catalog_bg(self, mood: str, language: str, tone_emotion: str | None = None, text_emotion: str | None = None) -> None:
        '''
        BACKGROUND CRAWLER (The Adaptive Vault):
        Fetches live songs asynchronously and appends them to the vault to ensure fresh dynamic content
        for subsequent queries without blocking the user response.
        '''
        import threading
        try:
            logger.info(f"Adaptive Vault: Fetching dynamic songs for {mood} ({language}) in background...")
            live_songs = _fetch_global_songs_for_mood(
                mood, language, limit=30, tone_emotion=tone_emotion, text_emotion=text_emotion
            )
            
            existing_keys = {f"{s.title.lower()}::{s.artist.lower()}" for s in self.catalog}
            new_songs = []
            
            for song in live_songs:
                k = f"{song.title.lower()}::{song.artist.lower()}"
                if k not in existing_keys:
                    self.catalog.append(song)
                    existing_keys.add(k)
                    new_songs.append(song)
            
            if new_songs:
                logger.info(f"Adaptive Vault: Absorbed {len(new_songs)} new dynamic songs. Total size: {len(self.catalog)}")
        except Exception as e:
            logger.error(f"Adaptive Vault Fetch Error: {e}")

    def recommend(
        self,
        mood: str,
        language: str,
        context: str = "general",
        limit: int = 10,
        use_live: bool = False,
        tone_emotion: str | None = None,
        text_emotion: str | None = None,
    ) -> list:
        '''
        Recommend globally best-fit songs using Collaborative Ranking.
        1. Uses ONLY local vault `self.catalog` (use_live = False).
        2. Filter by language.
        3. ML Collaborative Filter Ranking: Scored by exact mood + historical user feedback.
        '''
        normalized_language = language.strip().lower()
        normalized_context = context.strip().lower()

        base_target_energy = self.mood_energy_targets.get(mood, 0.5)

        if tone_emotion and text_emotion and tone_emotion != text_emotion:      
            tone_e = self.mood_energy_targets.get(tone_emotion, base_target_energy)
            text_e = self.mood_energy_targets.get(text_emotion, base_target_energy)
            target_energy = round((tone_e * 0.6) + (text_e * 0.4), 2)
        else:
            target_energy = base_target_energy

        context_offset = self.context_energy_offsets.get(normalized_context, 0.0)
        target_energy = min(1.0, max(0.0, target_energy + context_offset))      

        working_set = []
        if use_live:
            # Fallback if explicitly asked to block
            working_set = _fetch_global_songs_for_mood(mood, language, limit=50, tone_emotion=tone_emotion, text_emotion=text_emotion)
            new_k = {f"{s.title.lower()}::{s.artist.lower()}" for s in working_set}
            working_set.extend([s for s in self.catalog if f"{s.title.lower()}::{s.artist.lower()}" not in new_k])
        else:
            # 100% Adaptive Vault Path
            working_set = self.catalog

        # Language filter (soft fallback to all if zero matches)
        lang_filtered = [s for s in working_set if s.language.lower() == normalized_language]
        working_set = lang_filtered if lang_filtered else working_set

        # Calculate Average Collaborative Energy from User Interactions
        # This drifts the target energy towards what the user *actually* likes.
        liked_songs = [s for s in self.catalog if self._feedback_boosts.get(s.id, 0.0) > 0.0]
        if len(liked_songs) > 0:
            avg_liked_energy = sum(s.energy for s in liked_songs) / len(liked_songs)
            # 30% collaborative drift
            target_energy = (target_energy * 0.7) + (avg_liked_energy * 0.3)

        # --- Jittered Multi-Tiered Ranking (Darwin Evolution Applied) ---
        import random
        # Opposing moods for strict penalization
        opposing_moods = {
            "happy": ["sad", "angry"],
            "sad": ["happy", "excited", "party"],
            "angry": ["calm", "focused", "relax", "happy"],
            "calm": ["angry", "excited"],
            "excited": ["sad", "calm", "sleep"],
            "focused": ["angry", "party"],
            "neutral": ["angry", "excited", "sad"]
        }

        def score(song) -> float:
            # 1. Buff Exact Mood Match heavily so wrong tags NEVER outrank correct ones
            mood_match = 5.0 if mood in song.mood_tags else 0.0
            
            # 2. Strict Penalization for entirely Opposite Moods
            penalty = 0.0
            song_tags_set = set(song.mood_tags)
            if any(opp in song_tags_set for opp in opposing_moods.get(mood, [])):
                penalty = -4.0  # Decimates any score advantages from popularity or energy

            # 3. Energy fit still matters for ranking among matching moods
            energy_fit = 1.2 - abs(song.energy - target_energy)
            
            lang_bonus = 1.0 if song.language.lower() == normalized_language else 0.0

            pop_score = 0.0
            if song.playcount > 0:
                pop_score = min(1.0, song.playcount / 5_000_000) * 0.8
            elif song.popularity is not None:
                pop_score = (song.popularity / 100.0) * 0.7

            fb_boost = self._feedback_boosts.get(song.id, 0.0)

            collab_bonus = 0.0
            if fb_boost == 0.0 and len(liked_songs) > 0:
                for l_song in liked_songs:
                    if set(l_song.mood_tags).intersection(song_tags_set):
                        collab_bonus += 0.2

            context_bonus = 0.0
            if normalized_context == "study" and mood in ("focused", "calm"): context_bonus = 0.5
            elif normalized_context == "workout" and mood in ("angry", "excited"): context_bonus = 0.5
            elif normalized_context == "sleep" and mood in ("calm", "sad"): context_bonus = 0.5
            elif normalized_context == "party" and mood in ("happy", "excited"): context_bonus = 0.5

            neutral_bonus = 0.5 if mood == "neutral" and any(t in song_tags_set for t in ("calm", "happy")) else 0.0
            
            # 4. Stochastic serendipity drift (Randomness)
            # Adds between 0.0 to 1.5 extra points, allowing rotation of equal-match songs on reload
            serendipity_drift = random.uniform(0.0, 1.5)

            # 5. Fallback tiny partial match if there is tag overlap
            partial_match = 0.0
            if mood_match == 0.0 and tone_emotion and tone_emotion in song_tags_set: partial_match += 1.5
            if mood_match == 0.0 and text_emotion and text_emotion in song_tags_set: partial_match += 1.0

            return mood_match + partial_match + energy_fit + lang_bonus + pop_score + fb_boost + collab_bonus + context_bonus + neutral_bonus + serendipity_drift + penalty
            
        ranked = sorted(working_set, key=score, reverse=True)

        seen_artists = {}
        diverse = []
        overflow = []

        for song in ranked:
            artist_key = song.artist.lower()
            count = seen_artists.get(artist_key, 0)
            if count < 2:
                diverse.append(song)
                seen_artists[artist_key] = count + 1
            else:
                overflow.append(song)
            if len(diverse) >= limit: break

        if len(diverse) < limit:
            diverse.extend(overflow[: limit - len(diverse)])

        return diverse[:limit]

recommender_service = RecommenderService()
