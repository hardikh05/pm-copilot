"""Importing this module registers all ORM models with the Base metadata."""

from app.models.chat import ChatMessage
from app.models.cluster import Cluster
from app.models.feature import Feature
from app.models.feedback import FeedbackItem
from app.models.prd import PRD, CritiqueNote
from app.models.project import Project
from app.models.roadmap import RoadmapItem


def register_all() -> None:
    """No-op; importing the module is enough to register models."""
    return None


__all__ = [
    "ChatMessage",
    "Cluster",
    "CritiqueNote",
    "Feature",
    "FeedbackItem",
    "PRD",
    "Project",
    "RoadmapItem",
    "register_all",
]
