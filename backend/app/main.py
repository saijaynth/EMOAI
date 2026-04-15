from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.core.config import settings
from app.services.feedback_store import feedback_store
from app.services.recommender import recommender_service
from app.services.user_store import user_store

from app.core.database import Base, engine

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize DB
    Base.metadata.create_all(bind=engine)
    
    recommender_service.load_catalog()
    feedback_store.load()
    user_store.load()
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.allowed_origins.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
