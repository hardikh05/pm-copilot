from pydantic import BaseModel


class RoadmapItemOut(BaseModel):
    id: int
    feature_id: int
    horizon: str
    theme: str | None
    order_index: int
    depends_on: list[int]
    estimated_weeks: float

    class Config:
        from_attributes = True


class RoadmapResponse(BaseModel):
    now: list[RoadmapItemOut]
    next: list[RoadmapItemOut]
    later: list[RoadmapItemOut]
    capacity_weeks_per_horizon: float
    themes: list[str]
