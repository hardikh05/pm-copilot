from datetime import datetime

from pydantic import BaseModel


class FeedbackOut(BaseModel):
    id: int
    text: str
    source: str | None
    rating: int | None
    user_segment: str | None
    author: str | None
    created_at: datetime | None
    sentiment: str | None
    sentiment_score: float | None
    cluster_id: int | None

    class Config:
        from_attributes = True


class FeedbackUploadResult(BaseModel):
    inserted: int
    skipped: int
    total: int
