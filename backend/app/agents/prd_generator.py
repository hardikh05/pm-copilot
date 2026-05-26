"""Agent 4: PRD Generator."""
from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agents import llm, prompts
from app.models.cluster import Cluster
from app.models.feature import Feature
from app.models.feedback import FeedbackItem
from app.models.prd import PRD

log = logging.getLogger(__name__)

REQUIRED_SECTIONS = [
    "problem",
    "goal",
    "user_stories",
    "success_metrics",
    "requirements",
    "edge_cases",
    "out_of_scope",
]


def _sentiment_summary(cluster: Cluster | None) -> str:
    if not cluster:
        return "n/a"
    return (
        f"{cluster.positive_pct:.0%} pos / {cluster.neutral_pct:.0%} neu / "
        f"{cluster.negative_pct:.0%} neg (avg {cluster.avg_sentiment:+.2f})"
    )


def _normalize(content: dict) -> dict:
    """Ensure required sections exist and are the right type."""
    out = dict(content) if isinstance(content, dict) else {}
    for key in ["user_stories", "success_metrics", "requirements", "edge_cases", "out_of_scope"]:
        v = out.get(key)
        if not isinstance(v, list):
            out[key] = [str(v)] if v else []
        else:
            out[key] = [str(x) for x in v]
    for key in ["problem", "goal"]:
        if not isinstance(out.get(key), str):
            out[key] = str(out.get(key, ""))
    return out


def run(db: Session, feature_id: int) -> PRD:
    feature: Feature | None = db.get(Feature, feature_id)
    if feature is None:
        raise ValueError(f"feature {feature_id} not found")

    cluster: Cluster | None = db.get(Cluster, feature.cluster_id) if feature.cluster_id else None
    items = (
        list(
            db.scalars(
                select(FeedbackItem).where(FeedbackItem.cluster_id == cluster.id).limit(8)
            )
        )
        if cluster
        else []
    )
    samples = "\n".join(f"- {it.text}" for it in items[:6]) or "(no source feedback)"

    ai = llm.chat_json(
        prompts.PRD_GENERATOR_SYSTEM,
        prompts.PRD_GENERATOR_USER.format(
            title=feature.title,
            description=feature.description or "",
            cluster_label=cluster.label if cluster else "n/a",
            cluster_summary=cluster.summary if cluster else "",
            reach=feature.reach,
            sentiment_summary=_sentiment_summary(cluster),
            samples=samples,
        ),
        temperature=0.4,
    )

    content = _normalize(ai)

    # Versioning: bump version if previous PRDs exist
    prev_count = db.query(PRD).filter(PRD.feature_id == feature.id).count()
    prd = PRD(
        feature_id=feature.id,
        version=prev_count + 1,
        content=content,
        source_feedback_ids=[it.id for it in items],
        status="draft",
        title=str(ai.get("title", feature.title))[:200],
        summary=str(ai.get("summary", ""))[:1000],
    )
    db.add(prd)
    db.commit()
    db.refresh(prd)
    return prd
