from collections import Counter
import uuid
from datetime import datetime, UTC

from app.schemas.mood import FeedbackAnalyticsResponse, FeedbackRequest
from app.core.database import SessionLocal
from app.data.models import Feedback

class FeedbackStore:
    def __init__(self) -> None:
        pass

    def load(self) -> None:
        pass

    def record(self, payload: FeedbackRequest) -> dict:
        db = SessionLocal()
        try:
            entry_dict = payload.model_dump()
            db_feedback = Feedback(
                id=f"fb_{uuid.uuid4().hex[:12]}",
                song_id=payload.song_id,
                action=payload.action,
                relevance_score=payload.relevance_score,
                mood=payload.mood,
                language=payload.language,
                session_id=payload.session_id,
                created_at=datetime.now(UTC)
            )
            db.add(db_feedback)
            db.commit()
            return entry_dict
        finally:
            db.close()

    def analytics(self) -> FeedbackAnalyticsResponse:
        db = SessionLocal()
        try:
            feedbacks = db.query(Feedback).all()
            
            total_feedback = len(feedbacks)
            likes = sum(1 for item in feedbacks if item.action == "like")
            skips = sum(1 for item in feedbacks if item.action == "skip")
            saves = sum(1 for item in feedbacks if item.action == "save")
            
            total_relevance = sum(item.relevance_score for item in feedbacks if item.relevance_score)
            average_relevance = round(total_relevance / total_feedback, 2) if total_feedback else 0.0
            
            top_songs = Counter(item.song_id for item in feedbacks if item.song_id).most_common(5)
            top_song_payload = [{"song_id": song_id, "count": count} for song_id, count in top_songs]

            return FeedbackAnalyticsResponse(
                total_feedback=total_feedback,
                likes=likes,
                skips=skips,
                saves=saves,
                average_relevance=average_relevance,
                top_songs=top_song_payload,
            )
        finally:
            db.close()

feedback_store = FeedbackStore()
