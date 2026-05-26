# PM Copilot

**An AI copilot that takes a product manager from raw user feedback → clustered insights → prioritized features → PRDs → roadmap recommendation.**

Built as a multi-agent system using LangGraph + Google Gemini. Not another RAG chatbot — this models the actual workflow a PM runs every week.

## Why this exists

PMs spend hours triaging support tickets, hunting for patterns in NPS, arguing about priority, and writing PRDs from scratch. PM Copilot automates the mechanical 70% so the PM can spend their time on the judgment 30%.

## The agents

| # | Agent | What it does |
|---|---|---|
| 1 | **Feedback Intelligence** | Embeds feedback (Gemini text-embedding-004), clusters with HDBSCAN, classifies sentiment, labels themes. Every cluster cites its source tickets. |
| 2 | **Opportunity Scoring** | Computes RICE per cluster. Reach/Impact/Confidence are derived from the data; Effort is AI-estimated with an explicit caveat and overridable by the PM. |
| 3 | **Product Strategy** | Synthesizes Quick Wins, Long-Term Bets, and Risks from the scored features + clusters. |
| 4 | **PRD Generator** | Drafts a structured PRD (Problem, Goal, User Stories, Metrics, Requirements, Edge Cases) for a chosen feature, citing source feedback. |
| 5 | **PRD Critic** | Second-pass review: flags ambiguity, missing metrics, unclear requirements, untestable edges. Optional revision loop. |
| 6 | **Roadmap Generator** | Organizes accepted features into themes across Now / Next / Later, respects a capacity budget, surfaces dependencies. |

The agents are orchestrated by a LangGraph state machine. Progress streams to the UI over SSE.

## What makes this different from a chatbot

- **Grounded methodology.** Clusters come from embeddings + HDBSCAN, not "ask the LLM to group these." Sentiment is a classifier. Numbers can be checked.
- **Traceability.** Every insight, score, and PRD line links back to the raw feedback it came from. PMs can verify before they ship.
- **Human-in-the-loop.** PRDs are editable. Critic notes can be accepted or dismissed. RICE Effort is overridable.
- **Conversational refinement.** A chat panel re-runs agents with new constraints ("re-prioritize weighting enterprise users 2×").

## Stack

- **Frontend:** Next.js 15 (App Router), TypeScript, Tailwind, shadcn/ui-style components
- **Backend:** FastAPI, SQLAlchemy 2, Alembic, LangGraph
- **AI:** Google Gemini (gemini-1.5-flash for agents, text-embedding-004 for embeddings)
- **DB:** Postgres + pgvector (Supabase or Neon free tier works)
- **Deploy:** Vercel (frontend) + Render (backend)

## Quick start

Full step-by-step in [SETUP.md](./SETUP.md). The short version:

```powershell
# 1. Postgres+pgvector: Supabase or Neon free tier. Copy the connection string,
#    swap "postgresql://" -> "postgresql+psycopg://".
# 2. Gemini key: https://aistudio.google.com/app/apikey

# Backend
cd backend
python -m venv .venv; .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env   # edit DATABASE_URL + GEMINI_API_KEY
alembic upgrade head
uvicorn app.main:app --reload --port 8000

# Frontend (new terminal)
cd frontend
npm install
Copy-Item .env.example .env.local
npm run dev
```

On Windows, `.\start-dev.ps1` from the root spawns both in separate windows.

Open http://localhost:3000 → **New project** → **Seed demo** (500 items) → **Run all agents**.

There's also a CLI smoke test: `python backend\smoke_test.py` (uses ~80 items to keep Gemini usage small).

## Demo flow (for interviewers)

1. **Upload / seed** 500 feedback items
2. **Feedback Intelligence** clusters them — open a cluster to see the source tickets it came from
3. **Prioritization** ranks features by RICE — edit Effort to see ranking update
4. **Strategy** surfaces Quick Wins / Bets / Risks
5. **Pick a feature → PRD** generates a draft; the **Critic** panel flags weaknesses
6. **Roadmap** organizes accepted features across Now / Next / Later

## Project layout

```
pm-copilot/
├── backend/           FastAPI + LangGraph agents
│   ├── app/
│   │   ├── api/       HTTP routes
│   │   ├── agents/    Six agents + LangGraph orchestration
│   │   ├── services/  embeddings, clustering, ingestion
│   │   ├── models/    SQLAlchemy models
│   │   └── synthetic/ demo data generator
│   └── alembic/       migrations
└── frontend/          Next.js 15 App Router
    ├── app/projects/  step-by-step PM workflow
    ├── components/    UI primitives + feature components
    └── lib/           API client
```

## What's intentionally out of scope (v1)

- Auth / multi-tenancy
- Native integrations (Zendesk, App Store API, Intercom) — upload CSV/JSON instead
- Real-time collaboration on PRDs
