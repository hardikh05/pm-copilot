"""Agent 2: Opportunity Scoring.

RICE breakdown (transparent):
- Reach: cluster size (count of distinct affected users in our sample). Real-world
  PMs would project this to total user base; we surface raw count + share.
- Impact: AI suggests on RICE's classic 0.25..3 scale, biased by avg sentiment and
  how negative the cluster is.
- Confidence: derived from data — log-scaled cluster size combined with sentiment
  consistency (low variance => high confidence).
- Effort: AI-estimated engineer-weeks (>= 0.5). PM can override.
"""
from __future__ import annotations

import logging
import math
from statistics import pstdev

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agents import llm, prompts
from app.models.cluster import Cluster
from app.models.feature import Feature
from app.models.feedback import FeedbackItem

log = logging.getLogger(__name__)


def _confidence(cluster: Cluster, scores: list[float]) -> float:
    """0..1. Larger cluster + tighter sentiment = more confident."""
    size_term = min(1.0, math.log10(max(cluster.size, 1)) / 2.0)  # ~1.0 at size 100+
    variance_term = 1.0 - min(1.0, pstdev(scores) if len(scores) > 1 else 0.0)
    return round(0.5 * size_term + 0.5 * variance_term, 2)


def run(db: Session, project_id: int, user_hint: str | None = None) -> dict:
    """Score every cluster with RICE.

    `user_hint` is an optional natural-language directive from the PM (typically via the
    Copilot chat — e.g. "weight enterprise users 2x more heavily") that gets injected
    into each LLM prompt as additional guidance. The LLM is asked to bias its scoring
    accordingly. Best-effort; not a hard mathematical constraint."""
    clusters = list(db.scalars(select(Cluster).where(Cluster.project_id == project_id)))
    if not clusters:
        return {"features": 0}

    # Wipe old features for this project (they're derivative)
    db.query(Feature).filter(Feature.project_id == project_id).delete()
    db.flush()

    hint_prefix = f"PM GUIDANCE (apply throughout your scoring): {user_hint}\n\n" if user_hint else ""

    created = 0
    for cluster in clusters:
        items = list(
            db.scalars(
                select(FeedbackItem).where(FeedbackItem.cluster_id == cluster.id).limit(10)
            )
        )
        samples = "\n".join(f"- {it.text}" for it in items[:6])

        try:
            ai = llm.chat_json(
                prompts.OPPORTUNITY_SYSTEM,
                hint_prefix + prompts.OPPORTUNITY_USER.format(
                    label=cluster.label,
                    summary=cluster.summary or "",
                    size=cluster.size,
                    positive_pct=cluster.positive_pct,
                    neutral_pct=cluster.neutral_pct,
                    negative_pct=cluster.negative_pct,
                    avg_sentiment=cluster.avg_sentiment,
                    samples=samples,
                ),
                temperature=0.3,
            )
        except Exception as e:  # noqa: BLE001
            log.warning("opportunity scoring failed for cluster %d: %s", cluster.id, e)
            ai = {
                "title": f"Address: {cluster.label}",
                "description": cluster.summary or "",
                "impact": 1.0,
                "effort": 2.0,
                "rationale": "Fallback estimate after LLM error.",
            }

        impact = float(ai.get("impact", 1.0))
        if impact not in {0.25, 0.5, 1.0, 2.0, 3.0}:
            impact = min({0.25, 0.5, 1.0, 2.0, 3.0}, key=lambda x: abs(x - impact))

        effort = max(0.5, float(ai.get("effort", 2.0)))
        all_scores = [it.sentiment_score or 0.0 for it in db.scalars(
            select(FeedbackItem).where(FeedbackItem.cluster_id == cluster.id)
        )]
        confidence = _confidence(cluster, all_scores)
        reach = cluster.size

        rice = (reach * impact * confidence) / effort

        feature = Feature(
            project_id=project_id,
            cluster_id=cluster.id,
            title=str(ai.get("title", f"Address: {cluster.label}"))[:200],
            description=str(ai.get("description", "")),
            reach=reach,
            impact=impact,
            confidence=confidence,
            effort=effort,
            effort_overridden=False,
            rice_score=round(rice, 2),
            rationale=str(ai.get("rationale", "")),
        )
        db.add(feature)
        created += 1

    db.commit()
    return {"features": created}


def recompute_rice(feature: Feature) -> None:
    """Recompute a feature's RICE score from its current inputs."""
    feature.rice_score = round(
        (feature.reach * feature.impact * feature.confidence) / max(feature.effort, 0.5),
        2,
    )
