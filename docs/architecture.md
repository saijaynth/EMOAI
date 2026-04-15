# Emo AI Architecture

## High-Level Components
1. Web App (Next.js)
2. API Service (FastAPI)
3. Song Catalog Store (JSON for MVP, DB in production)
4. User/Profile/Feedback Store (planned)
5. Mood Analysis Engines (text now, voice/face later)

## Request Lifecycle
1. User selects language.
2. User submits mood input method(s).
3. Backend computes per-method mood scores.
4. Fusion service generates final mood and confidence.
5. Recommendation service ranks songs from universal catalog.
6. Frontend displays results and captures feedback.

## Recommendation Contract
- Input: mood, language, optional energy/context
- Logic:
  - Filter catalog by language
  - Score by mood match and energy closeness
  - Add popularity boost
  - Return top N songs
- Output:
  - mood, confidence, recommendations, explanation

## Scale-Up Plan
- Move songs and feedback to PostgreSQL
- Add Redis caching for recommendation queries
- Add async task queue for heavy voice/face inference
- Add experiment tracking for model quality
