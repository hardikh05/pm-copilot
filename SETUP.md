# Setup walkthrough

Step-by-step setup for a Windows machine with Python 3.11 and Node 20+. Mac/Linux works the same with the obvious shell differences.

## 1. Postgres + pgvector (hosted, free)

Use **[Supabase](https://supabase.com)** or **[Neon](https://neon.tech)**. Both have free tiers with pgvector enabled out of the box.

### Supabase

1. Create a new project. Pick a region close to you.
2. Project Settings → Database → **Connection string** → **URI** mode. Copy it.
3. Replace the prefix `postgresql://` with `postgresql+psycopg://` (we use psycopg 3).
4. Make sure pgvector is enabled: Database → Extensions → search "vector" → enable.

### Neon

1. Create a project. Copy the connection string from the dashboard.
2. Replace `postgresql://` with `postgresql+psycopg://`.
3. pgvector ships enabled.

## 2. Gemini API key

[aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey) → Create API key. Free tier is generous.

## 3. Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
# edit .env: paste DATABASE_URL and GEMINI_API_KEY
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

Verify: open http://localhost:8000/healthz → `{"status":"ok"}`.

## 4. Frontend

```powershell
cd ..\frontend
npm install
Copy-Item .env.example .env.local
npm run dev
```

Open http://localhost:3000.

## 5. First run

1. **New project** → name it ("Recipe app — Q1 feedback").
2. **Add feedback** → **Seed demo** (500 items).
3. Back to dashboard → **Run all agents** (watch the SSE-streamed progress).
4. **Clusters** → expand a cluster to see source tickets.
5. **Prioritization** → edit Effort on any row; RICE re-ranks live.
6. **Strategy** → see Quick Wins / Bets / Risks.
7. Click any feature → **Generate + Critic (loop)** to draft a PRD with iterative critic refinement.
8. **Roadmap** → Now / Next / Later board, capacity-aware.

## 6. Deploy

### Backend → Render

1. Push to a Git repo. In Render, **New → Blueprint** → point at the repo.
2. The `render.yaml` defines the web service. Set the environment variables in the dashboard:
   - `DATABASE_URL`
   - `GEMINI_API_KEY`
   - `ALLOWED_ORIGINS` (your Vercel URL, comma-separated)

### Frontend → Vercel

1. Import the repo. Root directory: `frontend`.
2. Add env var `NEXT_PUBLIC_API_URL` = your Render URL.
3. Deploy.

## Troubleshooting

- **`relation "vector" does not exist`** — pgvector extension not enabled. In Supabase: Database → Extensions → enable `vector`. Or run `CREATE EXTENSION vector;` against your DB.
- **CORS errors** — backend `ALLOWED_ORIGINS` must include your frontend URL exactly (no trailing slash).
- **`No module named app`** — you're not in the `backend/` directory, or the venv isn't activated.
- **Embeddings fail with rate-limit** — Gemini free tier has per-minute limits. Try a smaller seed (e.g. `?n=200`).
