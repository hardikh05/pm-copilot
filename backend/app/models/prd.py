from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class PRD(Base):
    """Generated PRD for a feature. Versioned: each edit/regen creates a new row."""

    __tablename__ = "prds"

    id: Mapped[int] = mapped_column(primary_key=True)
    feature_id: Mapped[int] = mapped_column(ForeignKey("features.id", ondelete="CASCADE"), index=True)
    version: Mapped[int] = mapped_column(Integer, default=1)

    # Structured PRD content. Stored as JSON so the UI can render each section.
    # Sections: problem, goal, user_stories[], success_metrics[], requirements[], edge_cases[], out_of_scope[]
    content: Mapped[dict] = mapped_column(JSON)

    # Source feedback IDs that informed this PRD (traceability)
    source_feedback_ids: Mapped[list[int]] = mapped_column(JSON, default=list)

    status: Mapped[str] = mapped_column(String(20), default="draft")  # draft, accepted, rejected
    title: Mapped[str | None] = mapped_column(String(200), nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    feature = relationship("Feature", back_populates="prds")
    critiques = relationship("CritiqueNote", back_populates="prd", cascade="all, delete-orphan")


class CritiqueNote(Base):
    """A single critique from the PRD Critic agent."""

    __tablename__ = "critique_notes"

    id: Mapped[int] = mapped_column(primary_key=True)
    prd_id: Mapped[int] = mapped_column(ForeignKey("prds.id", ondelete="CASCADE"), index=True)

    section: Mapped[str] = mapped_column(String(50))  # problem, goal, user_stories, ...
    severity: Mapped[str] = mapped_column(String(20))  # low, medium, high
    category: Mapped[str] = mapped_column(String(50))  # ambiguity, missing_metric, unclear_requirement, untestable
    message: Mapped[str] = mapped_column(Text)
    suggestion: Mapped[str | None] = mapped_column(Text, nullable=True)

    status: Mapped[str] = mapped_column(String(20), default="open")  # open, accepted, dismissed
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    prd = relationship("PRD", back_populates="critiques")
