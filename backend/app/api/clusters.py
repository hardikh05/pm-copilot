from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.cluster import Cluster
from app.models.feedback import FeedbackItem
from app.models.project import Project
from app.schemas.cluster import ClusterOut, ClusterWithSamples

router = APIRouter()


@router.get("/{project_id}/clusters", response_model=list[ClusterOut])
def list_clusters(project_id: int, db: Session = Depends(get_db)):
    if not db.get(Project, project_id):
        raise HTTPException(404, "project not found")
    return list(
        db.scalars(
            select(Cluster).where(Cluster.project_id == project_id).order_by(Cluster.size.desc())
        )
    )


@router.get("/{project_id}/clusters/{cluster_id}", response_model=ClusterWithSamples)
def get_cluster(project_id: int, cluster_id: int, db: Session = Depends(get_db)):
    cluster = db.get(Cluster, cluster_id)
    if not cluster or cluster.project_id != project_id:
        raise HTTPException(404, "cluster not found")
    samples = list(
        db.scalars(
            select(FeedbackItem)
            .where(FeedbackItem.cluster_id == cluster_id)
            .order_by(FeedbackItem.sentiment_score.asc().nulls_last())
            .limit(20)
        )
    )
    return ClusterWithSamples(
        id=cluster.id,
        label=cluster.label,
        summary=cluster.summary,
        size=cluster.size,
        positive_pct=cluster.positive_pct,
        neutral_pct=cluster.neutral_pct,
        negative_pct=cluster.negative_pct,
        avg_sentiment=cluster.avg_sentiment,
        sample_feedback=[
            {
                "id": s.id,
                "text": s.text,
                "source": s.source,
                "rating": s.rating,
                "sentiment": s.sentiment,
                "user_segment": s.user_segment,
            }
            for s in samples
        ],
    )
