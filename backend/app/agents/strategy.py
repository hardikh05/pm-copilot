"""Agent 3: Product Strategy.
Assigns each feature to quick_win | bet | risk and produces a short narrative."""
from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agents import llm, prompts
from app.models.feature import Feature

log = logging.getLogger(__name__)


def run(db: Session, project_id: int, user_hint: str | None = None) -> dict:
    """Assign each feature to quick_win / bet / risk and write a short narrative.
    `user_hint` is an optional PM directive (via Copilot chat) injected into the prompt."""
    features: list[Feature] = list(
        db.scalars(select(Feature).where(Feature.project_id == project_id))
    )
    if not features:
        return {"assigned": 0, "summary": ""}

    listing = "\n".join(
        f"- id={f.id} title={f.title!r} reach={f.reach} impact={f.impact} "
        f"confidence={f.confidence} effort={f.effort} rice={f.rice_score}"
        for f in features
    )
    hint_prefix = f"PM GUIDANCE: {user_hint}\n\n" if user_hint else ""
    try:
        ai = llm.chat_json(
            prompts.STRATEGY_SYSTEM,
            hint_prefix + prompts.STRATEGY_USER.format(features=listing),
            temperature=0.3,
        )
    except Exception as e:  # noqa: BLE001
        log.warning("strategy LLM failed: %s — falling back to heuristic buckets", e)
        ai = {"summary": "", "assignments": []}

    by_id = {f.id: f for f in features}
    assigned = 0
    for entry in ai.get("assignments", []):
        fid = int(entry.get("feature_id", -1))
        bucket = str(entry.get("bucket", "")).lower()
        if fid in by_id and bucket in {"quick_win", "bet", "risk"}:
            by_id[fid].strategy_bucket = bucket
            assigned += 1

    # Fallback heuristic for anything the LLM missed
    for f in features:
        if f.strategy_bucket:
            continue
        if f.effort <= 2 and f.impact >= 1.0:
            f.strategy_bucket = "quick_win"
        elif f.effort >= 4 and f.impact >= 2.0:
            f.strategy_bucket = "bet"
        else:
            f.strategy_bucket = "risk" if f.confidence >= 0.6 and f.impact >= 1.0 else "bet"
        assigned += 1

    db.commit()
    return {"assigned": assigned, "summary": str(ai.get("summary", ""))}
