from pydantic import BaseModel


class ClusterOut(BaseModel):
    id: int
    label: str
    summary: str | None
    size: int
    positive_pct: float
    neutral_pct: float
    negative_pct: float
    avg_sentiment: float

    class Config:
        from_attributes = True


class ClusterWithSamples(ClusterOut):
    sample_feedback: list[dict]
