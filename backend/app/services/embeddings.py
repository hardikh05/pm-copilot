"""Generates embeddings for feedback items that don't have one yet, in-place."""
from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agents.llm import embed
from app.models.feedback import FeedbackItem

log = logging.getLogger(__name__)


def embed_missing(db: Session, project_id: int, batch_size: int = 100) -> int:
    """Embed all feedback in the project that doesn't yet have an embedding.
    Returns the number embedded."""
    stmt = select(FeedbackItem).where(
        FeedbackItem.project_id == project_id,
        FeedbackItem.embedding.is_(None),
    )
    items: list[FeedbackItem] = list(db.scalars(stmt))
    if not items:
        return 0

    total = 0
    for i in range(0, len(items), batch_size):
        chunk = items[i : i + batch_size]
        vectors = embed([it.text for it in chunk])
        for it, vec in zip(chunk, vectors):
            it.embedding = vec
        db.commit()
        total += len(chunk)
        log.info("embedded %d/%d feedback items for project %d", total, len(items), project_id)
    return total
