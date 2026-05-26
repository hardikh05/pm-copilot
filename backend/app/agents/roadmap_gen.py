"""Agent 6: Roadmap Generator.
Themes + dependencies + capacity-respecting placement across Now / Next / Later."""
from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agents import llm, prompts
from app.models.feature import Feature
from app.models.roadmap import RoadmapItem

log = logging.getLogger(__name__)

VALID_HORIZONS = {"now", "next", "later"}


def run(
    db: Session,
    project_id: int,
    capacity_weeks_per_horizon: float = 12.0,
    user_hint: str | None = None,
) -> dict:
    """Build Now/Next/Later roadmap. `user_hint` is an optional PM directive
    (via Copilot chat) injected into the prompt — e.g. 'rebuild with 6-week capacity'."""
    features = list(db.scalars(select(Feature).where(Feature.project_id == project_id)))
    if not features:
        return {"items": 0, "themes": []}

    listing = "\n".join(
        f"- id={f.id} title={f.title!r} bucket={f.strategy_bucket or 'unknown'} "
        f"rice={f.rice_score} effort={f.effort}"
        for f in features
    )
    hint_prefix = f"PM GUIDANCE: {user_hint}\n\n" if user_hint else ""
    try:
        ai = llm.chat_json(
            prompts.ROADMAP_SYSTEM,
            hint_prefix + prompts.ROADMAP_USER.format(features=listing, capacity=capacity_weeks_per_horizon),
            temperature=0.3,
        )
    except Exception as e:  # noqa: BLE001
        log.warning("roadmap LLM failed: %s — falling back to bucket-based placement", e)
        ai = {"themes": ["Improvements"], "items": []}

    themes = [str(t) for t in ai.get("themes", []) if isinstance(t, (str, int))] or ["Improvements"]
    raw_items = ai.get("items", []) if isinstance(ai, dict) else []

    # Wipe and rebuild
    db.query(RoadmapItem).filter(RoadmapItem.project_id == project_id).delete()
    db.flush()

    placed: dict[int, RoadmapItem] = {}
    for entry in raw_items:
        if not isinstance(entry, dict):
            continue
        try:
            fid = int(entry["feature_id"])
        except (KeyError, TypeError, ValueError):
            continue
        if fid not in {f.id for f in features} or fid in placed:
            continue
        horizon = str(entry.get("horizon", "")).lower()
        if horizon not in VALID_HORIZONS:
            horizon = "later"
        item = RoadmapItem(
            project_id=project_id,
            feature_id=fid,
            horizon=horizon,
            theme=str(entry.get("theme", themes[0]))[:120],
            order_index=int(entry.get("order_index", 0) or 0),
            depends_on=[int(x) for x in entry.get("depends_on", []) if isinstance(x, (int, str)) and str(x).isdigit()],
            estimated_weeks=float(entry.get("estimated_weeks", 0.0) or 0.0),
        )
        db.add(item)
        placed[fid] = item

    # Fallback: any unplaced features get bucket-based placement
    for f in features:
        if f.id in placed:
            continue
        if f.strategy_bucket == "quick_win" or f.strategy_bucket == "risk":
            horizon = "now"
        elif f.strategy_bucket == "bet":
            horizon = "next" if f.effort < 6 else "later"
        else:
            horizon = "next"
        item = RoadmapItem(
            project_id=project_id,
            feature_id=f.id,
            horizon=horizon,
            theme=themes[0],
            order_index=len(placed),
            depends_on=[],
            estimated_weeks=f.effort,
        )
        db.add(item)
        placed[f.id] = item

    db.commit()
    return {"items": len(placed), "themes": themes, "capacity_weeks_per_horizon": capacity_weeks_per_horizon}
