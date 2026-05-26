from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Feature(Base):
    """A candidate feature derived from a cluster, scored with RICE."""

    __tablename__ = "features"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    cluster_id: Mapped[int | None] = mapped_column(ForeignKey("clusters.id", ondelete="SET NULL"), nullable=True)

    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # RICE inputs (1..10 except reach which is a count)
    reach: Mapped[int] = mapped_column(Integer, default=0)  # count of affected users (~cluster size)
    impact: Mapped[float] = mapped_column(Float, default=0.0)  # 0.25..3.0 (classic RICE scale)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)  # 0..1
    effort: Mapped[float] = mapped_column(Float, default=1.0)  # engineer-weeks (>=0.5)
    effort_overridden: Mapped[bool] = mapped_column(default=False)  # PM has set this manually

    rice_score: Mapped[float] = mapped_column(Float, default=0.0)
    rationale: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Strategy bucket
    strategy_bucket: Mapped[str | None] = mapped_column(String(20), nullable=True)  # quick_win, bet, risk

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    project = relationship("Project", back_populates="features")
    cluster = relationship("Cluster", back_populates="features")
    prds = relationship("PRD", back_populates="feature", cascade="all, delete-orphan")
    roadmap_items = relationship("RoadmapItem", back_populates="feature", cascade="all, delete-orphan")
