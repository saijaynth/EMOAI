import uuid
from collections import Counter
from datetime import datetime, UTC
from threading import Lock

from app.schemas.mood import (
    SessionRecord,
    SessionRecordRequest,
    UserProfileResponse,
    UserResponse,
)
from app.core.database import SessionLocal
from app.data.models import User, Session

class UserStore:
    def __init__(self) -> None:
        self._lock = Lock()  # Kept for compatibility if used concurrently, though SessionLocal handles it

    def load(self) -> None:
        pass

    def register_or_get(self, username: str) -> UserResponse:
        normalized = username.strip().lower()
        db = SessionLocal()
        try:
            with self._lock:
                user = db.query(User).filter(User.username.ilike(normalized)).first()
                if user:
                    return UserResponse(user_id=user.id, username=user.username)

                user_id = f"user_{uuid.uuid4().hex[:10]}"
                new_user = User(id=user_id, username=username.strip())
                db.add(new_user)
                db.commit()
                return UserResponse(user_id=user_id, username=new_user.username)
        finally:
            db.close()

    def login(self, username: str) -> UserResponse | None:
        normalized = username.strip().lower()
        db = SessionLocal()
        try:
            with self._lock:
                user = db.query(User).filter(User.username.ilike(normalized)).first()
                if user:
                    return UserResponse(user_id=user.id, username=user.username)
            return None
        finally:
            db.close()

    def add_session(self, payload: SessionRecordRequest) -> SessionRecord:
        db = SessionLocal()
        try:
            session_id = f"sess_{uuid.uuid4().hex[:12]}"
            created_dt = datetime.now(UTC)
            
            # Serialize song_ids to string for DB
            song_ids_str = ",".join(payload.song_ids) if payload.song_ids else ""

            db_session = Session(
                id=session_id,
                user_id=payload.user_id,
                mood=payload.mood,
                language=payload.language,
                context=payload.context,
                method=payload.method,
                song_ids=song_ids_str,
                created_at=created_dt
            )
            db.add(db_session)
            db.commit()
            
            return SessionRecord(
                session_id=session_id,
                user_id=payload.user_id,
                mood=payload.mood,
                language=payload.language,
                context=payload.context,
                method=payload.method,
                song_ids=payload.song_ids,
                created_at=created_dt.isoformat()
            )
        finally:
            db.close()

    def profile(self, user_id: str) -> UserProfileResponse | None:
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return None
                
            active_sessions = db.query(Session).filter(Session.user_id == user_id).order_by(Session.created_at.asc()).all()
            total_sessions = len(active_sessions)
            
            mood_counter = Counter(s.mood for s in active_sessions if s.mood)
            language_counter = Counter(s.language for s in active_sessions if s.language)

            favorite_mood = mood_counter.most_common(1)[0][0] if mood_counter else None
            favorite_language = language_counter.most_common(1)[0][0] if language_counter else None
            last_mood = active_sessions[-1].mood if active_sessions else None

            return UserProfileResponse(
                user_id=user.id,
                username=user.username,
                total_sessions=total_sessions,
                favorite_mood=favorite_mood,
                favorite_language=favorite_language,
                last_mood=last_mood,
            )
        finally:
            db.close()

    def sessions(self, user_id: str) -> list[SessionRecord]:
        db = SessionLocal()
        try:
            active_sessions = db.query(Session).filter(Session.user_id == user_id).all()
            records = []
            for s in active_sessions:
                # Deserialize
                songs = s.song_ids.split(",") if s.song_ids else []
                records.append(SessionRecord(
                    session_id=s.id,
                    user_id=s.user_id,
                    mood=s.mood,
                    language=s.language,
                    context=s.context,
                    method=s.method,
                    song_ids=songs,
                    created_at=s.created_at.isoformat() if s.created_at else ""
                ))
            return records
        finally:
            db.close()

user_store = UserStore()
