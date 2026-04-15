from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Table
from sqlalchemy.orm import relationship
from datetime import datetime, UTC
import uuid

from app.core.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)

    sessions = relationship("Session", back_populates="user")
    feedback = relationship("Feedback", back_populates="user")

class Session(Base):
    __tablename__ = "sessions"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"))
    mood = Column(String)
    language = Column(String)
    context = Column(String)
    method = Column(String)
    song_ids = Column(String) # Comma separated list of song ids
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))

    user = relationship("User", back_populates="sessions")

class Feedback(Base):
    __tablename__ = "feedback"

    id = Column(String, primary_key=True, index=True)
    song_id = Column(String, index=True)
    action = Column(String)  # like, skip, save
    relevance_score = Column(Integer)  # 1 to 5
    mood = Column(String, nullable=True)
    language = Column(String, nullable=True)
    session_id = Column(String, index=True, nullable=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))

    user = relationship("User", back_populates="feedback")
