"""Endpoints that kick off agent runs. Pipeline endpoints stream progress via SSE."""
import json

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sse_starlette.sse import EventSourceResponse

from app.agents import graph
from app.db import get_db
from app.models.feature import Feature
from app.models.project import Project

router = APIRouter()


@router.post("/{project_id}/agents/run-all")
def run_all_sync(project_id: int, db: Session = Depends(get_db)):
    """Synchronous run of the full pipeline. Useful for tests; UI uses /stream."""
    if not db.get(Project, project_id):
        raise HTTPException(404, "project not found")
    db.close()  # graph nodes open their own sessions
    final = graph.PIPELINE_GRAPH.invoke({"project_id": project_id})
    return final


@router.get("/{project_id}/agents/pipeline/stream")
def pipeline_stream(project_id: int):
    """SSE: streams {step, status, data} events as each agent completes."""
    def event_gen():
        for event in graph.stream_pipeline(project_id):
            yield {"data": json.dumps(event)}
    return EventSourceResponse(event_gen())


@router.post("/{project_id}/features/{feature_id}/prd/run-with-critic")
def run_prd_with_critic(
    project_id: int,
    feature_id: int,
    max_iterations: int = Query(2, ge=0, le=5),
    db: Session = Depends(get_db),
):
    feature = db.get(Feature, feature_id)
    if not feature or feature.project_id != project_id:
        raise HTTPException(404, "feature not found")
    db.close()
    return graph.run_prd_pipeline(feature_id, max_iterations=max_iterations)


@router.get("/{project_id}/features/{feature_id}/prd/run-with-critic/stream")
def run_prd_with_critic_stream(project_id: int, feature_id: int, max_iterations: int = Query(2, ge=0, le=5)):
    def event_gen():
        for event in graph.stream_prd_pipeline(feature_id, max_iterations=max_iterations):
            yield {"data": json.dumps(event)}
    return EventSourceResponse(event_gen())
