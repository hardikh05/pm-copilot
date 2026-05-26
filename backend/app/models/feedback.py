from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base

EMBED_DIM = 768  # Gemini text-embedding-004


class FeedbackItem(Base):
    __tablename__ = "feedback_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)

    text: Mapped[str] = mapped_column(Text)
    source: Mapped[str | None] = mapped_column(String(50), nullable=True)  # app_store, play_store, zendesk, nps
    rating: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 1–5 where available
    user_segment: Mapped[str | None] = mapped_column(String(80), nullable=True)  # enterprise, smb, new_user, power_user
    author: Mapped[str | None] = mapped_column(String(120), nullable=True)
    created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ingested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    embedding: Mapped[list[float] | None] = mapped_column(Vector(EMBED_DIM), nullable=True)
    sentiment: Mapped[str | None] = mapped_column(String(20), nullable=True)  # positive, neutral, negative
    sentiment_score: Mapped[float | None] = mapped_column(nullable=True)  # -1.0..1.0

    cluster_id: Mapped[int | None] = mapped_column(ForeignKey("clusters.id", ondelete="SET NULL"), nullable=True, index=True)

    project = relationship("Project", back_populates="feedback_items")
    cluster = relationship("Cluster", back_populates="items")
