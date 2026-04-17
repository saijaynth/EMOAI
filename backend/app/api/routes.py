from fastapi import APIRouter, HTTPException, Query, BackgroundTasks

from app.schemas.mood import (
    FeedbackRequest,
    FeedbackAnalyticsResponse,
    MoodDetectionResponse,
    MoodFusionRequest,
    MoodLabel,
    RecommendationResponse,
    TextMoodRequest,
    VoiceMoodRequest,
    FaceMoodRequest,
    SessionRecord,
    SessionRecordRequest,
    UserLoginRequest,
    UserProfileResponse,
    UserRegisterRequest,
    UserResponse,
    VoiceTranscriptionRequest,
    VoiceTranscriptionResponse,
)
from app.services.feedback_store import feedback_store
from app.services.recommender import recommender_service
from app.services.transcriber import VoiceTranscriptionError, voice_transcriber_service
from app.services.user_store import user_store

router = APIRouter()


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/languages")
async def list_languages() -> dict[str, list[str]]:
    languages = sorted({song.language for song in recommender_service.catalog})
    return {"languages": languages}


@router.post("/mood/detect/text", response_model=MoodDetectionResponse)
async def detect_text_mood(payload: TextMoodRequest) -> MoodDetectionResponse:
    mood, confidence = recommender_service.detect_text_mood(payload.text)
    return MoodDetectionResponse(
        mood=mood,
        confidence=confidence,
        method_scores=[{"method": "text", "mood": mood, "confidence": confidence}],
    )


@router.post("/mood/detect/voice", response_model=MoodDetectionResponse)
async def detect_voice_mood(payload: VoiceMoodRequest) -> MoodDetectionResponse:
    tone_profile = payload.tone_profile.model_dump(exclude_none=True) if payload.tone_profile else None
    result = recommender_service.detect_voice_mood(payload.transcript, tone_profile=tone_profile, language=payload.language)
    
    return MoodDetectionResponse(
        mood=result["mood"],
        confidence=result["confidence"],
        method_scores=[{"method": "voice", "mood": result["mood"], "confidence": result["confidence"]}],
        tone_emotion=result.get("tone_emotion"),
        text_emotion=result.get("text_emotion"),
        confidence_level=result.get("confidence_level")
    )

@router.post("/voice/transcribe", response_model=VoiceTranscriptionResponse)
async def transcribe_voice(payload: VoiceTranscriptionRequest) -> VoiceTranscriptionResponse:
    try:
        transcript, confidence = voice_transcriber_service.transcribe(
            audio_base64=payload.audio_base64,
            language=payload.language,
            mime_type=payload.mime_type,
            fallback_transcript=payload.fallback_transcript,
        )
    except VoiceTranscriptionError as exc:
        raise HTTPException(status_code=422, detail={"message": str(exc)}) from exc

    return VoiceTranscriptionResponse(
        transcript=transcript,
        language=payload.language,
        confidence=confidence,
    )


@router.post("/mood/detect/face", response_model=MoodDetectionResponse)
async def detect_face_mood(payload: FaceMoodRequest) -> MoodDetectionResponse:
    mood, confidence = recommender_service.detect_face_mood(
        image_data=payload.image_data,
        expression=payload.expression,
        intensity=payload.intensity,
    )
    return MoodDetectionResponse(
        mood=mood,
        confidence=confidence,
        method_scores=[{"method": "face", "mood": mood, "confidence": confidence}],
    )


@router.post("/mood/fuse", response_model=MoodDetectionResponse)
async def fuse_mood(payload: MoodFusionRequest) -> MoodDetectionResponse:
    mood, confidence = recommender_service.fuse_scores(payload.method_scores)
    return MoodDetectionResponse(mood=mood, confidence=confidence, method_scores=payload.method_scores)


@router.get("/recommendations", response_model=RecommendationResponse)
async def get_recommendations(
    background_tasks: BackgroundTasks,
    mood: MoodLabel = Query(...),
    language: str = Query(...),
    context: str = Query(default="general"),
    confidence: float = Query(default=0.7),
    limit: int = Query(default=10, ge=1, le=30),
    tone_emotion: str | None = Query(default=None),
    text_emotion: str | None = Query(default=None),
) -> RecommendationResponse:
    if not recommender_service.catalog:
        # If catalog is somehow completely empty, we can't recommend without blocking.
        # But ordinarily we still shouldn't crash.
        recommender_service.load_catalog()

    recommendations = recommender_service.recommend(
        mood=mood, language=language, context=context, limit=limit,
        use_live=False, # Use Adaptive Vault zero-latency local retrieval
        tone_emotion=tone_emotion, text_emotion=text_emotion
    )
    
    # Spawn background Shadow Crawler process to fetch dynamic songs as per YouTube two-tower design
    background_tasks.add_task(
        recommender_service.enrich_catalog_bg, mood, language, tone_emotion, text_emotion
    )

    return RecommendationResponse(
        mood=mood,
        language=language,
        confidence=confidence,
        recommendations=recommendations,
    )


@router.post("/feedback")
async def submit_feedback(payload: FeedbackRequest) -> dict[str, str]:
    feedback_store.record(payload)
    recommender_service.apply_feedback_boost(payload.song_id, payload.action)
    return {"message": "Feedback recorded"}


@router.get("/feedback/analytics", response_model=FeedbackAnalyticsResponse)
async def feedback_analytics() -> FeedbackAnalyticsResponse:
    return feedback_store.analytics()


@router.post("/users/register", response_model=UserResponse)
async def register_user(payload: UserRegisterRequest) -> UserResponse:
    return user_store.register_or_get(payload.username)


@router.post("/users/login", response_model=UserResponse)
async def login_user(payload: UserLoginRequest) -> UserResponse:
    user = user_store.login(payload.username)
    if not user:
        raise HTTPException(status_code=404, detail={"message": "User not found"})
    return user


@router.post("/sessions", response_model=SessionRecord)
async def create_session(payload: SessionRecordRequest) -> SessionRecord:
    return user_store.add_session(payload)


@router.get("/users/{user_id}/profile", response_model=UserProfileResponse)
async def user_profile(user_id: str) -> UserProfileResponse:
    profile = user_store.profile(user_id)
    if not profile:
        raise HTTPException(status_code=404, detail={"message": "User not found"})
    return profile


@router.get("/users/{user_id}/sessions", response_model=list[SessionRecord])
async def user_sessions(user_id: str) -> list[SessionRecord]:
    profile = user_store.profile(user_id)
    if not profile:
        raise HTTPException(status_code=404, detail={"message": "User not found"})
    return user_store.sessions(user_id)
