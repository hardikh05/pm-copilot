from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agents import prd_critic, prd_generator
from app.db import get_db
from app.models.feature import Feature
from app.models.prd import PRD, CritiqueNote
from app.schemas.prd import CritiqueOut, CritiqueStatusUpdate, PRDOut, PRDUpdate

router = APIRouter()


@router.post("/{project_id}/features/{feature_id}/prds", response_model=PRDOut, status_code=201)
def generate(project_id: int, feature_id: int, db: Session = Depends(get_db)):
    feature = db.get(Feature, feature_id)
    if not feature or feature.project_id != project_id:
        raise HTTPException(404, "feature not found")
    prd = prd_generator.run(db, feature_id)
    return prd


@router.get("/{project_id}/features/{feature_id}/prds", response_model=list[PRDOut])
def list_prds(project_id: int, feature_id: int, db: Session = Depends(get_db)):
    feature = db.get(Feature, feature_id)
    if not feature or feature.project_id != project_id:
        raise HTTPException(404, "feature not found")
    return list(
        db.scalars(
            select(PRD).where(PRD.feature_id == feature_id).order_by(PRD.version.desc())
        )
    )


@router.get("/{project_id}/prds/{prd_id}", response_model=PRDOut)
def get_prd(project_id: int, prd_id: int, db: Session = Depends(get_db)):
    prd = db.get(PRD, prd_id)
    if not prd:
        raise HTTPException(404, "prd not found")
    feature = db.get(Feature, prd.feature_id)
    if not feature or feature.project_id != project_id:
        raise HTTPException(404, "prd not found")
    return prd


@router.patch("/{project_id}/prds/{prd_id}", response_model=PRDOut)
def update_prd(project_id: int, prd_id: int, payload: PRDUpdate, db: Session = Depends(get_db)):
    prd = db.get(PRD, prd_id)
    if not prd:
        raise HTTPException(404, "prd not found")
    feature = db.get(Feature, prd.feature_id)
    if not feature or feature.project_id != project_id:
        raise HTTPException(404, "prd not found")
    if payload.content is not None:
        prd.content = payload.content
    if payload.status is not None:
        if payload.status not in {"draft", "accepted", "rejected"}:
            raise HTTPException(400, "invalid status")
        prd.status = payload.status
    if payload.title is not None:
        prd.title = payload.title
    if payload.summary is not None:
        prd.summary = payload.summary
    db.commit()
    db.refresh(prd)
    return prd


@router.post("/{project_id}/prds/{prd_id}/critique", response_model=list[CritiqueOut])
def run_critique(project_id: int, prd_id: int, db: Session = Depends(get_db)):
    prd = db.get(PRD, prd_id)
    if not prd:
        raise HTTPException(404, "prd not found")
    feature = db.get(Feature, prd.feature_id)
    if not feature or feature.project_id != project_id:
        raise HTTPException(404, "prd not found")
    notes, _ = prd_critic.critique(db, prd_id)
    return notes


@router.get("/{project_id}/prds/{prd_id}/critique", response_model=list[CritiqueOut])
def list_critique(project_id: int, prd_id: int, db: Session = Depends(get_db)):
    prd = db.get(PRD, prd_id)
    if not prd:
        raise HTTPException(404, "prd not found")
    feature = db.get(Feature, prd.feature_id)
    if not feature or feature.project_id != project_id:
        raise HTTPException(404, "prd not found")
    return list(db.scalars(select(CritiqueNote).where(CritiqueNote.prd_id == prd_id)))


@router.patch("/{project_id}/critique/{note_id}", response_model=CritiqueOut)
def update_critique(
    project_id: int, note_id: int, payload: CritiqueStatusUpdate, db: Session = Depends(get_db)
):
    note = db.get(CritiqueNote, note_id)
    if not note:
        raise HTTPException(404, "note not found")
    if payload.status not in {"open", "accepted", "dismissed"}:
        raise HTTPException(400, "invalid status")
    note.status = payload.status
    db.commit()
    db.refresh(note)
    return note
