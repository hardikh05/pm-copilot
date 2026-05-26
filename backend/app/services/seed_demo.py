"""Inserts the synthetic recipe-app dataset into a project."""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.feedback import FeedbackItem
from app.synthetic.recipe_app import generate


def seed_demo(db: Session, project_id: int, n: int = 500) -> int:
    items = generate(n=n)
    rows = [
        FeedbackItem(
            project_id=project_id,
            text=it.text,
            source=it.source,
            rating=it.rating,
            user_segment=it.user_segment,
            author=it.author,
            created_at=it.created_at,
        )
        for it in items
    ]
    db.add_all(rows)
    db.commit()
    return len(rows)
