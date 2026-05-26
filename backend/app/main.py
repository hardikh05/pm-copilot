import logging
import warnings

# Quiet known-noisy upstream warnings that don't affect us.
warnings.filterwarnings("ignore", message=".*allowed_objects.*", category=DeprecationWarning)
warnings.filterwarnings("ignore", message=".*allowed_objects.*")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import agents, chat, clusters, features, feedback, prds, projects, roadmap
from app.config import settings

logging.basicConfig(level=settings.log_level)
log = logging.getLogger("pm-copilot")

app = FastAPI(title="PM Copilot API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(projects.router, prefix="/api/projects", tags=["projects"])
app.include_router(feedback.router, prefix="/api/projects", tags=["feedback"])
app.include_router(clusters.router, prefix="/api/projects", tags=["clusters"])
app.include_router(features.router, prefix="/api/projects", tags=["features"])
app.include_router(prds.router, prefix="/api/projects", tags=["prds"])
app.include_router(roadmap.router, prefix="/api/projects", tags=["roadmap"])
app.include_router(chat.router, prefix="/api/projects", tags=["chat"])
app.include_router(agents.router, prefix="/api/projects", tags=["agents"])
