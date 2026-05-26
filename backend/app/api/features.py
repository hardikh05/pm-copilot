from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agents.opportunity import recompute_rice
from app.db import get_db
from app.models.feature import Feature
from app.models.project import Project
from app.schemas.feature import FeatureEffortUpdate, FeatureOut

router = APIRouter()


@router.get("/{project_id}/features", response_model=list[FeatureOut])
def list_features(project_id: int, db: Session = Depends(get_db)):
    if not db.get(Project, project_id):
        raise HTTPException(404, "project not found")
    return list(
        db.scalars(
            select(Feature)
            .where(Feature.project_id == project_id)
            .order_by(Feature.rice_score.desc())
        )
    )


@router.patch("/{project_id}/features/{feature_id}/effort", response_model=FeatureOut)
def update_effort(
    project_id: int, feature_id: int, payload: FeatureEffortUpdate, db: Session = Depends(get_db)
):
    feature = db.get(Feature, feature_id)
    if not feature or feature.project_id != project_id:
        raise HTTPException(404, "feature not found")
    if payload.effort < 0.5:
        raise HTTPException(400, "effort must be >= 0.5")
    feature.effort = payload.effort
    feature.effort_overridden = True
    recompute_rice(feature)
    db.commit()
    db.refresh(feature)
    return feature
