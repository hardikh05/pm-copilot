from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.cluster import Cluster
from app.models.feature import Feature
from app.models.feedback import FeedbackItem
from app.models.prd import PRD
from app.models.project import Project
from app.models.roadmap import RoadmapItem
from app.schemas.project import ProjectCreate, ProjectOut, ProjectStats

router = APIRouter()


@router.get("", response_model=list[ProjectOut])
def list_projects(db: Session = Depends(get_db)):
    return list(db.scalars(select(Project).order_by(Project.created_at.desc())))


@router.post("", response_model=ProjectOut, status_code=201)
def create_project(payload: ProjectCreate, db: Session = Depends(get_db)):
    proj = Project(name=payload.name, description=payload.description)
    db.add(proj)
    db.commit()
    db.refresh(proj)
    return proj


@router.get("/{project_id}", response_model=ProjectOut)
def get_project(project_id: int, db: Session = Depends(get_db)):
    proj = db.get(Project, project_id)
    if not proj:
        raise HTTPException(404, "project not found")
    return proj


@router.delete("/{project_id}", status_code=204)
def delete_project(project_id: int, db: Session = Depends(get_db)):
    proj = db.get(Project, project_id)
    if not proj:
        raise HTTPException(404, "project not found")
    db.delete(proj)
    db.commit()


@router.get("/{project_id}/stats", response_model=ProjectStats)
def stats(project_id: int, db: Session = Depends(get_db)):
    if not db.get(Project, project_id):
        raise HTTPException(404, "project not found")
    return ProjectStats(
        feedback_count=db.scalar(select(func.count(FeedbackItem.id)).where(FeedbackItem.project_id == project_id)) or 0,
        cluster_count=db.scalar(select(func.count(Cluster.id)).where(Cluster.project_id == project_id)) or 0,
        feature_count=db.scalar(select(func.count(Feature.id)).where(Feature.project_id == project_id)) or 0,
        prd_count=db.scalar(
            select(func.count(PRD.id)).join(Feature, Feature.id == PRD.feature_id).where(Feature.project_id == project_id)
        ) or 0,
        roadmap_item_count=db.scalar(select(func.count(RoadmapItem.id)).where(RoadmapItem.project_id == project_id)) or 0,
    )
