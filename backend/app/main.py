from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import time
import logging

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

logger = logging.getLogger("uvicorn.access")

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.perf_counter()
    response = await call_next(request)
    process_time = time.perf_counter() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    logger.info(f"{request.method} {request.url.path} - {response.status_code} - {process_time:.4f}s")
    return response

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"message": "Internal Server Error", "details": str(exc) if settings.debug else "hidden"}
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.allowed_origins.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
