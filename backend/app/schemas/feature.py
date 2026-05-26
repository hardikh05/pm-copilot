from pydantic import BaseModel


class FeatureOut(BaseModel):
    id: int
    cluster_id: int | None
    title: str
    description: str | None
    reach: int
    impact: float
    confidence: float
    effort: float
    effort_overridden: bool
    rice_score: float
    rationale: str | None
    strategy_bucket: str | None

    class Config:
        from_attributes = True


class FeatureEffortUpdate(BaseModel):
    effort: float
