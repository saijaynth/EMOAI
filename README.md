
# Emo AI

Emo AI is a full-stack mood-based music recommendation platform.

## What It Does
- Detects mood from multiple methods: text, voice, face, and quiz.
- Lets users choose recommendation language first.
- Recommends songs from a universal constant song catalog.
- Applies language filtering and stable mood mapping.

## Product Principles
- Mood mapping is deterministic and versioned.
- Universal song catalog remains stable over time.
- Language preference is always respected first.
- Personalization can rerank but not break core mood logic.

## Stack
- Frontend: Next.js + TypeScript + Tailwind CSS
- Backend: FastAPI + Pydantic v2
- Database: PostgreSQL (planned)
- Cache: Redis (planned)
- Deployment: Docker Compose for local development

## Current Scope (MVP)
- Language selection flow
- Text mood detection endpoint
- Mood fusion contract for future multi-modal input
- Universal song catalog and recommendation endpoint

## Recommended Build Plan
1. Build frontend language + mood input screens.
2. Connect text mood endpoint.
3. Render recommendation cards with language filters.
4. Add feedback loop (like, skip, relevance).
5. Add voice and face detection in phase 2.

## Run Backend (after installing dependencies)
- Create virtual environment and install dependencies from backend/requirements.txt
- Configure optional accuracy/global-music keys in `backend/.env`:
  - `GEMINI_API_KEY=...` for high-accuracy text/voice/face mood analysis
  - `SPOTIFY_CLIENT_ID=...` and `SPOTIFY_CLIENT_SECRET=...` for live globally popular track recommendations via Spotify (Requires an active Spotify Premium account for developer apps)
  - `LASTFM_API_KEY=...` for live globally popular track retrieval by mood tag (fallback to Spotify)
- Start API:
  - uvicorn app.main:app --reload --port 8000

### Backend Behavior Notes
- Face mood endpoint accepts either real image input (`image_data` with data URL) or simulated payload (`{"expression": ..., "intensity": ...}` in `image_data`) for fallback mode.
- Recommendations merge live Last.fm global songs with local catalog, then rank by mood fit, energy fit, popularity, language match, and feedback boosts.

## Run Frontend (after installing dependencies)
- In frontend folder:
  - npm install
  - npm run dev

## API Preview
- GET /health
- GET /languages
- POST /mood/detect/text
- POST /mood/fuse
- GET /recommendations
- POST /feedback
