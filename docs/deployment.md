# EMO AI Deployment Runbook & Strategy ??

This repository uses a decoupled hosting strategy optimized for ML workloads and Next.js React Server Components. Since Vercel Serverless Functions have a harsh `250MB` size limit (which PyTorch/ONNX/OpenCV break) and a `10-second` cold start on Hobby tiers, we split the front and back:

*   **Frontend**: Vercel (Native Edge Network)
*   **Backend**: Render / Railway / Fly.io (Containerized Docker deployment)

## GitOps Pipeline (CI/CD)
Each commit pushed to the `main` branch on GitHub automatically kicks off:
1.  **GitHub Actions**: Runs `npm run build` locally in CI, and `pytest` against Python. Both act as quality gates preventing broken production deploys.
2.  **Vercel Auto-Deployment**: Upon a green merge, Vercel pulls `frontend/` and serves the UI globally.

## Step 1: Deploy the Backend (Render.com)
1.  Sign up for [Render](https://render.com).
2.  Go to **New -> Web Service** and authorize your GitHub Repo.
3.  Fill out the deployment params:
    *   **Name**: `emoai-backend`
    *   **Root Directory**: `backend`
    *   **Environment**: Docker (It will automatically pick up `backend/Dockerfile`)
    *   **Instance Type**: Ensure you select Free or Starter.
4.  **Environment Variables** (Add the keys exactly from your `.env` minus `localhost`):
    *   `GEMINI_API_KEY=your_key`
    *   `SPOTIFY_CLIENT_ID=your_id`
    *   `ALLOWED_ORIGINS=https://emoai.vercel.app` *(Leave as `*` first, then lock down)*
5.  Deploy. Wait for the green "Live". Copy your final URL (e.g. `https://emoai-backend.onrender.com`).

## Step 2: Deploy the Frontend (Vercel)
1.  Sign up for [Vercel](https://vercel.com) using GitHub.
2.  Click **Add New Project** and select `EMOAI`.
3.  Configure the build step:
    *   **Framework Preset**: Next.js
    *   **Root Directory**: `frontend`
4.  **Environment Variables**:
    *   Add exactly one variable so the frontend knows where the backend lives:
    *   Name: `NEXT_PUBLIC_API_BASE_URL`
    *   Value: `https://emoai-backend.onrender.com` (Paste the Render URL from Step 1 here WITHOUT A TRAILING SLASH)
5. Click **Deploy**.

## Zero-Downtime Releases
When making future changes, commit code sequentially:
1. First, branch new features locally.
2. Changes to APIs must be backwards-compatible (don't break existing payload contracts). Render auto-updates `backend/` first on merge.
3. Vercel auto-updates `frontend/` seamlessly.

If you face any issues during Vercel deployment, check your GitHub Actions Status badge inside your PRs for failing logs!
