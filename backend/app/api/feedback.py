from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.feedback import FeedbackItem
from app.models.project import Project
from app.schemas.feedback import FeedbackOut, FeedbackUploadResult
from app.services import ingestion, seed_demo

router = APIRouter()


def _ensure_project(db: Session, project_id: int) -> None:
    if not db.get(Project, project_id):
        raise HTTPException(404, "project not found")


@router.post("/{project_id}/feedback/upload", response_model=FeedbackUploadResult)
async def upload(project_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    _ensure_project(db, project_id)
    content = await file.read()
    name = (file.filename or "").lower()
    try:
        if name.endswith(".json"):
            inserted, skipped, total = ingestion.ingest_json(db, project_id, content)
        else:
            inserted, skipped, total = ingestion.ingest_csv(db, project_id, content)
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
    return FeedbackUploadResult(inserted=inserted, skipped=skipped, total=total)


@router.post("/{project_id}/feedback/seed-demo", response_model=FeedbackUploadResult)
def seed(project_id: int, n: int = Query(500, ge=10, le=2000), db: Session = Depends(get_db)):
    _ensure_project(db, project_id)
    inserted = seed_demo.seed_demo(db, project_id, n)
    return FeedbackUploadResult(inserted=inserted, skipped=0, total=inserted)


@router.get("/{project_id}/feedback", response_model=list[FeedbackOut])
def list_feedback(
    project_id: int,
    cluster_id: int | None = None,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    _ensure_project(db, project_id)
    stmt = select(FeedbackItem).where(FeedbackItem.project_id == project_id)
    if cluster_id is not None:
        stmt = stmt.where(FeedbackItem.cluster_id == cluster_id)
    stmt = stmt.order_by(FeedbackItem.id.desc()).limit(limit).offset(offset)
    return list(db.scalars(stmt))
