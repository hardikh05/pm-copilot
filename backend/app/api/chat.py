"""The Copilot is the conversational layer over the agent pipeline. Two jobs:

1. ANSWER QUESTIONS about the project using its actual data
   ("which cluster has the worst sentiment?", "why is X a quick win?").
   We pull project context (clusters + features + roadmap + strategy summary)
   and ground the LLM reply on it. Not generic LLM knowledge.

2. RE-RUN AGENTS WITH PM GUIDANCE
   ("re-prioritize weighting enterprise users 2x", "rebuild roadmap with
   a 6-engineer-week budget"). The user's natural-language instruction is
   passed as `user_hint` to the relevant agent, which injects it into the
   LLM prompt.

Every action is persisted so the PM has a paper trail of what changed and why."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agents import feedback_intel, llm, opportunity, roadmap_gen, strategy
from app.db import get_db
from app.models.chat import ChatMessage
from app.models.cluster import Cluster
from app.models.feature import Feature
from app.models.project import Project
from app.models.roadmap import RoadmapItem

router = APIRouter()

INTENT_SYSTEM = """You route a PM's chat message to one of these actions:
- "answer" — the PM is asking a question about their project (no agent re-run needed)
- "regenerate_clusters" — re-cluster feedback (e.g. "more granular clusters", "merge X and Y")
- "regenerate_prioritization" — re-run RICE scoring (e.g. "weight enterprise users 2x")
- "regenerate_strategy" — reassign quick-win/bet/risk buckets
- "regenerate_roadmap" — rebuild the roadmap (e.g. "with 6-week capacity")

Pick the SINGLE best action. If ambiguous or it's clearly just a question, choose "answer"."""

INTENT_USER = """PM message: {msg}

Return JSON:
{{
  "action": "answer|regenerate_clusters|regenerate_prioritization|regenerate_strategy|regenerate_roadmap",
  "reason_for_action": "<one short sentence explaining why you picked this action>"
}}
"""

ANSWER_SYSTEM = """You are a PM Copilot answering questions about a product project.

You will be given:
- A summary of the project's discovered feedback clusters (with sentiment + size)
- The features that came out of RICE scoring
- The current roadmap placement

Answer the PM's question STRICTLY from this context. If the answer isn't in the data,
say so honestly — do NOT invent details. Cite cluster labels and feature titles when
relevant. Be concise: 2-4 sentences typically."""

ANSWER_USER = """Project context:

CLUSTERS ({n_clusters}):
{clusters}

FEATURES (ranked by RICE, top {n_features}):
{features}

ROADMAP:
  Now:   {now}
  Next:  {next_h}
  Later: {later}

PM question: {question}

Answer in plain prose. No JSON, no preamble — just the answer."""


def _project_context(db: Session, project_id: int) -> dict:
    clusters = list(db.scalars(
        select(Cluster).where(Cluster.project_id == project_id).order_by(Cluster.size.desc())
    ))
    features = list(db.scalars(
        select(Feature).where(Feature.project_id == project_id).order_by(Feature.rice_score.desc())
    ))
    roadmap = list(db.scalars(
        select(RoadmapItem).where(RoadmapItem.project_id == project_id)
    ))
    feature_titles = {f.id: f.title for f in features}
    now = [feature_titles.get(r.feature_id, f"#{r.feature_id}") for r in roadmap if r.horizon == "now"]
    nxt = [feature_titles.get(r.feature_id, f"#{r.feature_id}") for r in roadmap if r.horizon == "next"]
    lat = [feature_titles.get(r.feature_id, f"#{r.feature_id}") for r in roadmap if r.horizon == "later"]
    return {
        "clusters": clusters,
        "features": features,
        "roadmap_now": now,
        "roadmap_next": nxt,
        "roadmap_later": lat,
    }


def _format_clusters(clusters: list[Cluster]) -> str:
    if not clusters:
        return "  (none — feedback hasn't been clustered yet)"
    return "\n".join(
        f"  - \"{c.label}\" — n={c.size}, sentiment {c.positive_pct:.0%}+/{c.neutral_pct:.0%}o/{c.negative_pct:.0%}-"
        + (f" — {c.summary}" if c.summary else "")
        for c in clusters[:12]
    )


def _format_features(features: list[Feature]) -> str:
    if not features:
        return "  (none — prioritization hasn't been run yet)"
    return "\n".join(
        f"  - \"{f.title}\" — RICE {f.rice_score:.1f} (reach={f.reach}, impact={f.impact}, "
        f"conf={f.confidence:.2f}, effort={f.effort}w) — bucket={f.strategy_bucket or '?'}"
        for f in features[:12]
    )


def _classify_intent(message: str) -> tuple[str, str]:
    """Returns (action, reason). Falls back to 'answer' on LLM failure."""
    try:
        result = llm.chat_json(INTENT_SYSTEM, INTENT_USER.format(msg=message), temperature=0.0)
        action = str(result.get("action", "answer")).lower()
        if action not in {"answer", "regenerate_clusters", "regenerate_prioritization",
                          "regenerate_strategy", "regenerate_roadmap"}:
            action = "answer"
        reason = str(result.get("reason_for_action", ""))
        return action, reason
    except Exception:
        return "answer", "intent-classifier failed; defaulting to answer"


def _summarize_changes(ctx_before: dict, ctx_after: dict, action: str) -> str:
    """One-sentence diff between two project snapshots."""
    if action == "regenerate_clusters":
        before, after = len(ctx_before["clusters"]), len(ctx_after["clusters"])
        return f"Re-clustered. {before} → {after} clusters."
    if action == "regenerate_prioritization":
        top_before = ctx_before["features"][0].title if ctx_before["features"] else "—"
        top_after = ctx_after["features"][0].title if ctx_after["features"] else "—"
        if top_before == top_after:
            return f"Re-ran prioritization. Top feature unchanged: {top_after!r}."
        return f"Re-ran prioritization. New top: {top_after!r} (was {top_before!r})."
    if action == "regenerate_strategy":
        def _bucket_counts(feats: list[Feature]) -> str:
            from collections import Counter
            c = Counter(f.strategy_bucket or "?" for f in feats)
            return f"{c.get('quick_win', 0)} quick wins / {c.get('bet', 0)} bets / {c.get('risk', 0)} risks"
        return f"Reassigned strategy buckets: {_bucket_counts(ctx_after['features'])}."
    if action == "regenerate_roadmap":
        return (
            f"Rebuilt roadmap. {len(ctx_after['roadmap_now'])} Now / "
            f"{len(ctx_after['roadmap_next'])} Next / {len(ctx_after['roadmap_later'])} Later."
        )
    return "Done."


class ChatRequest(BaseModel):
    content: str


class ChatMessageOut(BaseModel):
    id: int
    role: str
    content: str
    triggered_agent: str | None

    class Config:
        from_attributes = True


@router.get("/{project_id}/chat", response_model=list[ChatMessageOut])
def list_messages(project_id: int, db: Session = Depends(get_db)):
    if not db.get(Project, project_id):
        raise HTTPException(404, "project not found")
    return list(
        db.scalars(
            select(ChatMessage)
            .where(ChatMessage.project_id == project_id)
            .order_by(ChatMessage.created_at.asc())
        )
    )


@router.post("/{project_id}/chat", response_model=list[ChatMessageOut])
def send_message(project_id: int, payload: ChatRequest, db: Session = Depends(get_db)):
    if not db.get(Project, project_id):
        raise HTTPException(404, "project not found")

    # 1. Persist the user message immediately so it shows up in chat history
    user_msg = ChatMessage(project_id=project_id, role="user", content=payload.content)
    db.add(user_msg)
    db.commit()

    action, reason = _classify_intent(payload.content)
    triggered: str | None = None
    reply: str

    try:
        if action == "answer":
            ctx = _project_context(db, project_id)
            try:
                reply = llm.chat_text(
                    ANSWER_SYSTEM,
                    ANSWER_USER.format(
                        n_clusters=len(ctx["clusters"]),
                        clusters=_format_clusters(ctx["clusters"]),
                        n_features=min(12, len(ctx["features"])),
                        features=_format_features(ctx["features"]),
                        now=", ".join(ctx["roadmap_now"]) or "(empty)",
                        next_h=", ".join(ctx["roadmap_next"]) or "(empty)",
                        later=", ".join(ctx["roadmap_later"]) or "(empty)",
                        question=payload.content,
                    ),
                    temperature=0.3,
                ) or "I don't have enough context to answer that yet — try running the agents first."
            except Exception as e:  # noqa: BLE001
                reply = f"Couldn't answer right now — the LLM call failed ({e})."
        else:
            # Re-run intent: snapshot before, run agent with hint, snapshot after, diff
            before = _project_context(db, project_id)
            if action == "regenerate_clusters":
                feedback_intel.run(db, project_id)  # intel doesn't take a hint yet — clusters are unsupervised
                triggered = "feedback_intel"
            elif action == "regenerate_prioritization":
                opportunity.run(db, project_id, user_hint=payload.content)
                triggered = "opportunity"
            elif action == "regenerate_strategy":
                strategy.run(db, project_id, user_hint=payload.content)
                triggered = "strategy"
            elif action == "regenerate_roadmap":
                roadmap_gen.run(db, project_id, user_hint=payload.content)
                triggered = "roadmap_gen"
            after = _project_context(db, project_id)
            change_summary = _summarize_changes(before, after, action)
            hint_note = (
                f" Applied your guidance: {payload.content!r}."
                if action != "regenerate_clusters" else ""
            )
            reply = change_summary + hint_note
    except Exception as e:  # noqa: BLE001
        reply = f"Tried to {action.replace('_', ' ')} but failed: {e}"

    assistant_msg = ChatMessage(
        project_id=project_id,
        role="assistant",
        content=reply,
        triggered_agent=triggered,
        metadata_={"action": action, "intent_reason": reason},
    )
    db.add(assistant_msg)
    db.commit()
    db.refresh(user_msg)
    db.refresh(assistant_msg)
    return [user_msg, assistant_msg]
