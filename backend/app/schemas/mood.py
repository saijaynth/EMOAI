from typing import Literal, Any, Optional

from pydantic import BaseModel, Field

MoodLabel = Literal["happy", "sad", "angry", "calm", "anxious", "focused", "excited", "neutral"]


class TextMoodRequest(BaseModel):
    text: str = Field(min_length=1, max_length=1200)
    language: str = Field(min_length=2, max_length=30)


class VoiceMoodRequest(BaseModel):
    transcript: str = Field(min_length=1, max_length=1200)
    language: str = Field(min_length=2, max_length=30)


class FaceMoodRequest(BaseModel):
    image_data: str = Field(description="Base64 encoded image string")
    language: str = Field(min_length=2, max_length=30)


class MethodScore(BaseModel):
    method: Literal["text", "voice", "face", "quiz"]
    mood: MoodLabel
    confidence: float = Field(ge=0.0, le=1.0)


class MoodDetectionResponse(BaseModel):
    mood: MoodLabel
    confidence: float = Field(ge=0.0, le=1.0)
    method_scores: list[MethodScore]


class MoodFusionRequest(BaseModel):
    method_scores: list[MethodScore]


class SongItem(BaseModel):
    id: str
    title: str
    artist: str
    language: str
    mood_tags: list[MoodLabel]
    energy: float = Field(ge=0.0, le=1.0)
    playcount: int = Field(default=0)
    lastfm_url: str = Field(default="")
    album_art: str = Field(default="")
    source: str = Field(default="local")


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
