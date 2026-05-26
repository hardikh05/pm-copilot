from datetime import datetime
from typing import Any

from pydantic import BaseModel


class PRDContent(BaseModel):
    problem: str
    goal: str
    user_stories: list[str]
    success_metrics: list[str]
    requirements: list[str]
    edge_cases: list[str]
    out_of_scope: list[str] = []


class PRDOut(BaseModel):
    id: int
    feature_id: int
    version: int
    content: dict[str, Any]
    source_feedback_ids: list[int]
    status: str
    title: str | None
    summary: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class PRDUpdate(BaseModel):
    content: dict[str, Any] | None = None
    status: str | None = None
    title: str | None = None
    summary: str | None = None


class CritiqueOut(BaseModel):
    id: int
    prd_id: int
    section: str
    severity: str
    category: str
    message: str
    suggestion: str | None
    status: str

    class Config:
        from_attributes = True


class CritiqueStatusUpdate(BaseModel):
    status: str  # accepted, dismissed
