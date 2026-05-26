from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class RoadmapItem(Base):
    __tablename__ = "roadmap_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    feature_id: Mapped[int] = mapped_column(ForeignKey("features.id", ondelete="CASCADE"))

    horizon: Mapped[str] = mapped_column(String(20))  # now, next, later
    theme: Mapped[str | None] = mapped_column(String(120), nullable=True)
    order_index: Mapped[int] = mapped_column(Integer, default=0)
    depends_on: Mapped[list[int]] = mapped_column(JSON, default=list)  # other feature IDs
    estimated_weeks: Mapped[float] = mapped_column(default=0.0)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    project = relationship("Project", back_populates="roadmap_items")
    feature = relationship("Feature", back_populates="roadmap_items")
