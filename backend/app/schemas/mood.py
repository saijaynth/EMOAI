from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

MoodLabel = Literal[
    "happy", "sad", "angry", "calm", "anxious", "focused", "excited", "neutral",
    "romantic", "nostalgic", "confident", "dreamy", "triumphant", "chill", "hype",
    "melancholic", "hopeful", "frustrated", "bored"
]


class TextMoodRequest(BaseModel):
    text: str = Field(min_length=1, max_length=1200)
    language: str = Field(min_length=2, max_length=30)


class VoiceToneProfile(BaseModel):
    duration_ms: int | None = Field(default=None, ge=200, le=120000)
    speaking_rate_wpm: float | None = Field(default=None, ge=0.0, le=350.0)
    avg_volume: float | None = Field(default=None, ge=0.0, le=1.0)
    volume_variability: float | None = Field(default=None, ge=0.0, le=1.0)
    avg_pitch_hz: float | None = Field(default=None, ge=50.0, le=500.0)
    pitch_variability: float | None = Field(default=None, ge=0.0, le=300.0)
    pause_ratio: float | None = Field(default=None, ge=0.0, le=1.0)
    energy_label: str | None = Field(default=None, min_length=2, max_length=40)


class VoiceMoodRequest(BaseModel):
    transcript: str = Field(max_length=1200)
    language: str = Field(min_length=2, max_length=30)
    tone_profile: VoiceToneProfile | None = None

    @model_validator(mode="before")
    @classmethod
    def allow_empty_transcript(cls, data: Any) -> Any:
        if isinstance(data, dict) and 'transcript' in data:
            if not data['transcript']:
                data['transcript'] = " "
        return data


class VoiceTranscriptionRequest(BaseModel):
    audio_base64: str = Field(min_length=0, max_length=12_000_000)
    language: str = Field(min_length=2, max_length=30)
    mime_type: str = Field(default="audio/webm", min_length=2, max_length=80)
    fallback_transcript: str | None = Field(default=None, max_length=2000)


class VoiceTranscriptionResponse(BaseModel):
    transcript: str
    language: str
    confidence: float = Field(ge=0.0, le=1.0)


class FaceMoodRequest(BaseModel):
    image_data: str | None = Field(default=None, min_length=1, max_length=5_000_000)
    expression: Literal["smile", "frown", "neutral", "surprised", "tense"] | None = None
    intensity: float | None = Field(default=None, ge=0.0, le=1.0)
    language: str = Field(min_length=2, max_length=30)

    @model_validator(mode="after")
    def validate_payload(self) -> "FaceMoodRequest":
        if self.image_data is None and self.expression is None:
            raise ValueError("Either image_data or expression must be provided")
        return self


class MethodScore(BaseModel):
    method: Literal["text", "voice", "face", "quiz"]
    mood: MoodLabel
    confidence: float = Field(ge=0.0, le=1.0)


class MoodDetectionResponse(BaseModel):
    mood: MoodLabel
    confidence: float = Field(ge=0.0, le=1.0)
    method_scores: list[MethodScore]
    tone_emotion: str | None = None
    text_emotion: str | None = None
    confidence_level: str | None = None


class MoodFusionRequest(BaseModel):
    method_scores: list[MethodScore]


class SongItem(BaseModel):
    id: str
    title: str
    artist: str
    language: str
    mood_tags: list[MoodLabel]
    energy: float = Field(ge=0.0, le=1.0)
    valence: float | None = Field(default=None, ge=0.0, le=1.0)
    tempo: float | None = Field(default=None, ge=0.0)
    popularity: int | None = Field(default=None, ge=0, le=100)
    playcount: int = Field(default=0, ge=0)
    spotify_id: str | None = None
    youtube_id: str | None = None
    album_art: str | None = None
    lastfm_url: str | None = None
    source: Literal["local", "lastfm", "spotify"] = "local"


class RecommendationResponse(BaseModel):
    mood: MoodLabel
    language: str
    confidence: float = Field(ge=0.0, le=1.0)
    recommendations: list[SongItem]


class FeedbackRequest(BaseModel):
    song_id: str
    action: Literal["like", "skip", "save"]
    relevance_score: int = Field(ge=1, le=5)
    mood: MoodLabel | None = None
    language: str | None = None
    session_id: str | None = None

class FeedbackAnalyticsResponse(BaseModel):
    total_feedback: int
    likes: int
    skips: int
    saves: int
    average_relevance: float
    top_songs: list[dict[str, Any]]


class UserRegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=40)


class UserLoginRequest(BaseModel):
    username: str = Field(min_length=3, max_length=40)


class UserResponse(BaseModel):
    user_id: str
    username: str


class SessionRecordRequest(BaseModel):
    user_id: str = Field(min_length=3, max_length=80)
    mood: MoodLabel
    language: str = Field(min_length=2, max_length=30)
    context: str = Field(default="general", min_length=2, max_length=30)
    method: Literal["text", "voice", "face", "quiz"]
    song_ids: list[str] = Field(default_factory=list)


class SessionRecord(BaseModel):
    session_id: str
    user_id: str
    mood: MoodLabel
    language: str
    context: str
    method: Literal["text", "voice", "face", "quiz"]
    song_ids: list[str]
    created_at: str


class UserProfileResponse(BaseModel):
    user_id: str
    username: str
    total_sessions: int
    favorite_mood: MoodLabel | None
    favorite_language: str | None
    last_mood: MoodLabel | None
