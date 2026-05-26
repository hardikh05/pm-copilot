"""Smoke test: hits the backend end-to-end with a small synthetic dataset.

Usage:
    # Terminal A:  uvicorn app.main:app --reload --port 8000
    # Terminal B:
    python smoke_test.py
"""
from __future__ import annotations

import sys
import time

import httpx

BASE = "http://localhost:8000"


def main() -> int:
    with httpx.Client(base_url=BASE, timeout=600.0) as c:
        r = c.get("/healthz")
        r.raise_for_status()
        print("healthz:", r.json())

        proj = c.post("/api/projects", json={"name": "Smoke test", "description": "auto"}).json()
        pid = proj["id"]
        print("created project", pid)

        seed = c.post(f"/api/projects/{pid}/feedback/seed-demo?n=80").json()
        print("seeded:", seed)

        print("running pipeline (this hits Gemini; allow ~30s)...")
        t0 = time.time()
        run = c.post(f"/api/projects/{pid}/agents/run-all").json()
        print(f"pipeline done in {time.time() - t0:.1f}s")
        print("  intel:", run.get("intel"))
        print("  opportunity:", run.get("opportunity"))
        print("  strategy:", run.get("strategy"))
        print("  roadmap:", run.get("roadmap"))

        clusters = c.get(f"/api/projects/{pid}/clusters").json()
        features = c.get(f"/api/projects/{pid}/features").json()
        roadmap = c.get(f"/api/projects/{pid}/roadmap").json()
        print(f"clusters={len(clusters)} features={len(features)} now/next/later={len(roadmap['now'])}/{len(roadmap['next'])}/{len(roadmap['later'])}")

        if features:
            fid = features[0]["id"]
            print(f"generating PRD with critic for feature {fid}...")
            prd_res = c.post(f"/api/projects/{pid}/features/{fid}/prd/run-with-critic").json()
            print("  ", prd_res)

        print("\nAll good ✓")
    return 0


if __name__ == "__main__":
    sys.exit(main())
