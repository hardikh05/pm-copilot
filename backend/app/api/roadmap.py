from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.project import Project
from app.models.roadmap import RoadmapItem
from app.schemas.roadmap import RoadmapItemOut, RoadmapResponse

router = APIRouter()

CAPACITY = 12.0  # default weeks per horizon, surfaced in response


@router.get("/{project_id}/roadmap", response_model=RoadmapResponse)
def get_roadmap(project_id: int, db: Session = Depends(get_db)):
    if not db.get(Project, project_id):
        raise HTTPException(404, "project not found")
    items = list(
        db.scalars(
            select(RoadmapItem)
            .where(RoadmapItem.project_id == project_id)
            .order_by(RoadmapItem.horizon, RoadmapItem.order_index)
        )
    )
    by_horizon: dict[str, list[RoadmapItem]] = {"now": [], "next": [], "later": []}
    themes_seen: list[str] = []
    for it in items:
        if it.horizon in by_horizon:
            by_horizon[it.horizon].append(it)
        if it.theme and it.theme not in themes_seen:
            themes_seen.append(it.theme)
    return RoadmapResponse(
        now=[RoadmapItemOut.model_validate(i) for i in by_horizon["now"]],
        next=[RoadmapItemOut.model_validate(i) for i in by_horizon["next"]],
        later=[RoadmapItemOut.model_validate(i) for i in by_horizon["later"]],
        capacity_weeks_per_horizon=CAPACITY,
        themes=themes_seen,
    )
