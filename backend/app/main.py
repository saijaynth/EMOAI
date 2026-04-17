from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.core.config import settings
from app.services.feedback_store import feedback_store
from app.services.recommender import recommender_service
from app.services.user_store import user_store

from app.core.database import Base, engine

import sqlalchemy.exc

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize DB safely across multiple workers
    try:
        Base.metadata.create_all(bind=engine, checkfirst=True)
    except sqlalchemy.exc.OperationalError as e:
        if "already exists" not in str(e).lower():
            raise
    
    recommender_service.load_catalog()
    feedback_store.load()
    user_store.load()
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)

allowed_origins = [origin.strip() for origin in settings.allowed_origins.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    # Keep dev and preview environments stable across host/port variations.
    allow_origin_regex=r"^https?://.*$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/")
def read_root():
    return {"status": "ok", "message": "Emo AI Backend is running nicely!"}
@app.get("/health")
def health():
    return {"status": "ok"}
