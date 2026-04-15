
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
- Start API:
  - uvicorn app.main:app --reload --port 8000

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
