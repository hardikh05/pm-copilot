# Using PM Copilot

A guided walkthrough — what to click, what to expect, what to look at if something breaks — plus the post-MVP extension roadmap.

---

## Setup recap (skip if already running)

You should have both servers up:

- Backend: `http://127.0.0.1:8000` — healthcheck at `/healthz` returns `{"status":"ok"}`, API docs at `/docs`
- Frontend: `http://localhost:3000`

If they're not running:

```powershell
# Terminal 1
cd D:\Project\pm-copilot\backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --host 127.0.0.1 --port 8000

# Terminal 2
cd D:\Project\pm-copilot\frontend
npm run dev
```

Or from the project root: `.\start-dev.ps1`.

---

## Demo walkthrough (≈5 minutes end-to-end)

This is the flow to run when an interviewer asks "can you walk me through it?"

### 1. Create a project — 10 seconds

- Open http://localhost:3000
- Click **Start a project** → **New project**
- Name it something concrete, e.g. *"Recipe app — Q1 2026 feedback"*
- Optional description: *"Synthesizing 500 customer voice items across reviews + tickets + NPS"*

**What this gives you in a demo:** A blank dashboard with a 6-step progress strip (Upload → Cluster → Prioritize → Strategy → PRDs → Roadmap). Each step lights up green as you complete it.

### 2. Load feedback — 5 seconds

From the project dashboard → **Add feedback**.

Two options:
- **Seed demo data** (500 items by default) — synthetic recipe-app feedback across 8 themes (payment failures, slow onboarding, recipe-gen quality, search bugs, sync issues, dark mode requests, praise, pricing complaints). Use this for demos.
- **Upload CSV/JSON** — drag a file. Recognized columns are listed on the page. Use this when you want to show real data.

**What to point out:** "I designed the seed data to mirror the messy distribution PMs actually deal with — overlapping themes, mixed sentiment within a single theme, varying source channels."

### 3. Run the agent pipeline — 30–60 seconds

Back to dashboard → **Run all agents**. A live SSE-streamed progress card appears showing each agent as it completes:

1. **Feedback Intelligence** (~10s for 500 items) — embeds with Gemini, clusters with HDBSCAN, classifies sentiment, labels each cluster with the LLM
2. **Opportunity Scoring** (~5–10s) — computes RICE per cluster
3. **Product Strategy** (~3s) — assigns Quick Win / Bet / Risk
4. **Roadmap Generator** (~3s) — themes + Now / Next / Later + dependencies

**What to point out:** "Notice the methodology — clusters come from HDBSCAN over embeddings, not 'ask the LLM to group these.' Sentiment is a classifier. Numbers are reproducible."

### 4. Explore clusters — 1 minute

Dashboard → **Clusters** stat or **Feedback Intelligence** step.

You'll see ~6–10 cluster cards. For each:
- Theme label + 1-sentence summary (LLM-written)
- Size + sentiment bar (green/grey/red)
- Click to expand → source feedback items with their original source, rating, sentiment

**What to point out:**
- "Every cluster cites its source — if a PM disagrees with the AI's grouping, they can verify in two clicks."
- "Mixed-sentiment clusters (recipe gen) are surfaced honestly; not all bugs are 'all-negative.'"

### 5. Prioritize with RICE — 30 seconds

Click **Prioritization**. You'll see all features sorted by RICE score.

- Click any **Effort** cell to edit. Change `2.0w` to `5.0w`, hit Enter. The RICE score recomputes, the row re-sorts, and an asterisk marks the override.
- Click any feature title link or the PRD button to drill in.

**What to point out:**
- "Reach is grounded in the data (cluster size). Confidence is derived (log-scale of size + sentiment variance). Impact and Effort are LLM-suggested but Effort is one click to override — PMs always know engineering capacity better than the model."

### 6. Strategy view — 15 seconds

Click **Strategy** in the breadcrumb. Three columns:
- **Quick Wins** (low effort, high impact) — ship next
- **Long-Term Bets** (high effort, high upside) — quarter+ planning
- **Risks** (churn drivers, ops/regulatory) — must-do non-features

**What to point out:** "This is the slide a PM presents to leadership. Generating it from clusters → features → buckets is exactly the synthesis work that took me hours before."

### 7. Generate a PRD with Critic loop — 1–2 minutes

Click any feature → PRD workspace opens.

If no PRD exists, click **Generate + Critic (loop)**. Watch the stream:
- Generator drafts v1
- Critic reviews → flags ambiguities / missing metrics / untestable requirements
- If high-severity notes exist, generator drafts v2 addressing them
- Up to 2 revisions, then stops

You end up with the latest version selected, Critic notes on the right.

**What to point out:**
- "Multi-agent quality control. The Critic is a separate LLM call with a different prompt and temperature — it doesn't just rubber-stamp the generator."
- Click any Critic note → **Accept** or **Dismiss**. "PRDs are editable; suggestions are advisory. This is the human-in-the-loop pattern that makes the system trustworthy."
- Click **Markdown** to export. "Drops straight into Notion, Linear, or a Slack thread."

### 8. Roadmap — 30 seconds

Click **Roadmap**. Three columns: Now / Next / Later. Within each:
- Grouped by theme
- Each card shows bucket, RICE, estimated weeks
- Capacity badge turns yellow if a horizon is over budget
- Dependency arrows (`needs: <feature>`) show prerequisites

**What to point out:** "Themes, dependencies, capacity-aware placement — not just 'sprint / quarter / future' with feature names. This is what a real roadmap doc looks like."

### 9. (Bonus) Conversational refinement — 30 seconds

Back to dashboard. **Copilot chat** panel at the bottom. Try:

- *"Re-prioritize weighting enterprise users 2×"* → routes to opportunity agent, re-runs scoring
- *"Regenerate strategy focused on retention"* → routes to strategy agent

**What to point out:** "Not a chatbot bolted on — it's an intent-router that re-runs the relevant agent with constraints. The PM stays in their workflow."

---

## Talking points (when interviewers probe)

| If they ask… | Say… |
|---|---|
| "How is this different from ChatGPT?" | "Three things: grounded methodology (HDBSCAN, sentiment classifier — not LLM 'vibes'), traceability (every insight links to source feedback), and multi-agent orchestration with a critic loop. ChatGPT gives you one shot at a PRD; this critiques and revises until it passes." |
| "What about hallucinations?" | "The PRD Critic catches the most common ones — vague metrics, untestable requirements. Source feedback IDs on every cluster and PRD let the PM verify before acting." |
| "Why LangGraph?" | "Two reasons: deterministic state machine for the pipeline (vs. ad-hoc chaining), and clean primitives for conditional loops — the Critic ↔ Generator revision loop is one `add_conditional_edges` call." |
| "Why Gemini and not GPT/Claude?" | "Free tier was generous enough for a portfolio project. The LLM wrapper at `app/agents/llm.py` is the only file that imports `google.generativeai` — swapping providers is a 20-line change." |
| "How do you know the clusters are good?" | "HDBSCAN's density-based selection — items not in a dense neighborhood get labeled noise rather than being forced into a wrong cluster. I left in an 'Uncategorized' bucket for that reason. The PM-relevant metric I'd want next is a small labeled set + ARI / NMI scores against it." |

---

## Gemini free-tier quota — IMPORTANT

The free tier on `gemini-2.5-flash-lite` allows **20 generate requests per day** per project, per model. A single full pipeline run (intel + opportunity + strategy + roadmap) uses **~15–20 requests** depending on cluster count. PRD generation + Critic adds **2–4 more**.

**In practice:** you can do roughly one full pipeline OR one PRD-with-critic loop per day on a free key. Then you wait until quota resets (midnight Pacific) or:

- Switch models in `.env` — try `GEMINI_CHAT_MODEL=gemini-2.0-flash-lite` (separate quota)
- Get a paid Gemini key — no daily limit, pay per token (pennies for this workload)
- Use a smaller seed dataset (e.g. seed `?n=50` instead of 500) — fewer clusters means fewer LLM calls

**For demos / interviews:** run the full flow once when your quota is fresh, screen-record it (Loom is great), link the video in your README. You don't need a live re-run for every interviewer.

---

## Common errors and fixes

| Symptom | Cause | Fix |
|---|---|---|
| `relation "vector" does not exist` | pgvector extension not enabled | Supabase → Database → Extensions → enable `vector`. Or run `CREATE EXTENSION vector;` |
| `DuplicatePreparedStatement: prepared statement "_pg3_X" already exists` | Prepared statements + PgBouncer pooler | Already fixed in `app/db.py` (defaults `prepare_threshold=None`) |
| `model X is not found for API version v1beta` | Gemini model name has been renamed | Run `python -c "import google.generativeai as g; g.configure(api_key='YOUR_KEY'); [print(m.name) for m in g.list_models()]"` to see current names. Update `GEMINI_CHAT_MODEL` / `GEMINI_EMBED_MODEL` in `.env` |
| Couldn't reach the backend | Backend not running, or CORS misconfigured | `curl http://127.0.0.1:8000/healthz` → if not 200, restart uvicorn. If CORS, check `ALLOWED_ORIGINS` in `.env` matches your frontend URL exactly |
| `429` per-minute quota exceeded | Free-tier RPM cap hit | Wait 60s, retry. Or switch to a higher-quota model. |
| `429` per-day quota exceeded (limit:20) | Daily free-tier cap on chat model | See "Gemini free-tier quota" section above — switch model, wait, or upgrade |
| Pipeline stream "lost connection" | Backend crashed mid-pipeline | Check backend log. Usually a transient Gemini error — re-run |
| `Expecting value: line 1 column 1` in smoke test | Backend returned 500 (look at backend log) | Backend log will show the actual exception. Common causes: model name wrong, quota hit, DB connection lost |
| Node V8 fatal error / dev server crashed | Memory pressure on Node 24 | Restart: `npm run dev`. If recurring, downgrade to Node 20 LTS |
| `langgraph` import errors | Pinned versions drifted | `pip install -r requirements.txt --force-reinstall` |

---

## Extension roadmap

Ordered by impact / effort. Each item is tagged for which interview lane it strengthens:
- **[APM]** — strategy / PM judgment skills
- **[Analyst]** — measurement / evaluation skills

### Highest impact for either interview track

1. **[Analyst] Eval set + metrics dashboard** — A small labeled gold set (~20 PRDs scored by you for ambiguity/specificity, ~100 manually-categorized feedback items). Run the pipeline against it nightly and chart agreement scores over time. Demonstrates: you ship with eval, not just vibes. *Effort: 1–2 days. This is the single highest-leverage addition.*

2. **[APM] Trend over time** — Re-cluster weekly snapshots, show shifts (`+62% mentions of payment issues this week vs last`). A panel on the dashboard. Demonstrates: turning point analysis, which is *the* most valuable PM workflow this product can automate. *Effort: 1 day.*

3. **[APM + Analyst] Segment slicing** — Filter clusters/features by `user_segment` (enterprise / SMB / new / power). Compare RICE rankings across segments. Demonstrates: persona-aware prioritization + the analyst skill of slicing. *Effort: ½ day.*

### Mid-effort, high signal

4. **[Analyst] Inter-rater reliability for the Critic** — Run the Critic over the same PRD 5 times, measure note-set agreement. Surface as "Critic confidence: 0.84". Demonstrates: model evaluation rigor. *Effort: ½ day.*

5. **[APM] Notion + Linear export** — One-click "Push to Linear as ticket" and "Open in Notion as doc". The export already produces Markdown; add an `/integrations` page that takes API tokens. Demonstrates: integration thinking, "where does this live in a real team's workflow." *Effort: 1 day each.*

6. **[APM] What-if simulator** — On Prioritization, a slider "if engineering capacity doubles" — re-ranks features and re-flows the roadmap. Demonstrates: scenario planning, a senior-PM skill. *Effort: ½ day.*

### Bigger swings (if you have a week+)

7. **[Analyst] Live data integration** — App Store Connect API + Zendesk webhooks. Real ingestion pipeline, not CSV upload. Demonstrates: end-to-end product thinking. *Effort: 3–5 days per integration.*

8. **[APM + Analyst] Multi-PM workspace** — Auth (Clerk), per-workspace projects, role-based access. A real product, not a portfolio toy. Demonstrates: "I can build something I'd actually ship." *Effort: 3–4 days.*

9. **[Analyst] Model drift monitoring** — Compare embeddings of "today's feedback" to "30-days-ago feedback" via clustered KL divergence. Alert when distribution shifts. Demonstrates: production ML thinking. *Effort: 2 days.*

### Cheap polish (do these before showing to recruiters)

10. **Screenshot the demo flow and embed in README** — Use Loom to record a 60-second walkthrough. Add the link to the top of `README.md`. *Effort: 15 minutes.*

11. **Deploy a public demo** — Vercel + Render free tiers per `SETUP.md`. A working URL beats any screenshot. Use a read-only demo project with pre-loaded data. *Effort: 1 hour.*

12. **Reproducibility script** — A `bootstrap.ps1` that creates a fresh project, seeds, runs the pipeline, generates 3 PRDs. So an interviewer hitting your demo URL sees a populated dashboard, not an empty one. *Effort: 1 hour.*

---

## What I'd build next if optimizing for interviews

If you only have one weekend before interviews start: **#1 (eval set) + #2 (trends) + #10 (Loom recording) + #11 (public deploy)**. That's the maximum signal-per-hour.

If you have two weekends: add **#3 (segments) + #5 (Linear export)**.

If you have a week: also add **#6 (what-if simulator) + #4 (Critic IRR)**.

Anything beyond a week, you should probably be applying to jobs instead of building features. The product is already strong enough.
