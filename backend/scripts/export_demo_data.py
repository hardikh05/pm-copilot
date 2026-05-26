"""Exports demo data files for the repo.

Produces two kinds of files:

INPUT (the kind of data a PM would feed in):
  data/sample_feedback_500.csv  — 500 synthetic recipe-app feedback items
  data/sample_feedback_50.csv   — 50-item subset for quick testing
  data/sample_feedback.json     — same 500 items in JSON

OUTPUT (what the agents produced for a real run, snapshotted from the DB):
  data/sample_output_clusters.json  — labeled clusters with sentiment stats
  data/sample_output_features.json  — RICE-scored features with strategy buckets
  data/sample_output_roadmap.json   — Now/Next/Later placement

Run:  python backend/scripts/export_demo_data.py [project_id]
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

# Add backend/ to path so `from app...` works when run from project root
ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

from sqlalchemy import select  # noqa: E402

from app.db import SessionLocal  # noqa: E402
from app.models.cluster import Cluster  # noqa: E402
from app.models.feature import Feature  # noqa: E402
from app.models.feedback import FeedbackItem  # noqa: E402
from app.models.prd import PRD, CritiqueNote  # noqa: E402
from app.models.roadmap import RoadmapItem  # noqa: E402
from app.synthetic.recipe_app import generate  # noqa: E402

DATA = ROOT / "data"
DATA.mkdir(exist_ok=True)


# ----- INPUT files -----

def _to_row(item) -> dict:
    return {
        "text": item.text,
        "source": item.source,
        "rating": item.rating if item.rating is not None else "",
        "user_segment": item.user_segment,
        "author": item.author,
        "created_at": item.created_at.isoformat() if item.created_at else "",
    }


def export_input_files() -> None:
    items_500 = generate(n=500, seed=42)
    items_50 = items_500[:50]

    csv_500 = DATA / "sample_feedback_500.csv"
    csv_50 = DATA / "sample_feedback_50.csv"
    json_500 = DATA / "sample_feedback.json"

    fieldnames = ["text", "source", "rating", "user_segment", "author", "created_at"]
    for path, items in [(csv_500, items_500), (csv_50, items_50)]:
        with path.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fieldnames)
            w.writeheader()
            for it in items:
                w.writerow(_to_row(it))
        print(f"wrote {path.relative_to(ROOT)}  ({len(items)} items)")

    with json_500.open("w", encoding="utf-8") as f:
        json.dump([_to_row(it) for it in items_500], f, indent=2)
    print(f"wrote {json_500.relative_to(ROOT)}  ({len(items_500)} items)")


# ----- OUTPUT files (snapshot of agent results) -----

def export_output_files(project_id: int) -> None:
    db = SessionLocal()
    try:
        clusters = list(db.scalars(select(Cluster).where(Cluster.project_id == project_id).order_by(Cluster.size.desc())))
        features = list(db.scalars(select(Feature).where(Feature.project_id == project_id).order_by(Feature.rice_score.desc())))
        roadmap = list(db.scalars(select(RoadmapItem).where(RoadmapItem.project_id == project_id).order_by(RoadmapItem.horizon, RoadmapItem.order_index)))

        if not clusters:
            print(f"project {project_id} has no clusters — skipping output snapshot")
            return

        clusters_out = [
            {
                "id": c.id,
                "label": c.label,
                "summary": c.summary,
                "size": c.size,
                "sentiment": {
                    "positive_pct": round(c.positive_pct, 3),
                    "neutral_pct": round(c.neutral_pct, 3),
                    "negative_pct": round(c.negative_pct, 3),
                    "avg_score": round(c.avg_sentiment, 3),
                },
                "sample_feedback_ids": [
                    it.id for it in db.scalars(
                        select(FeedbackItem).where(FeedbackItem.cluster_id == c.id).limit(5)
                    )
                ],
            }
            for c in clusters
        ]

        features_out = [
            {
                "id": f.id,
                "title": f.title,
                "description": f.description,
                "rice_score": f.rice_score,
                "rice_breakdown": {
                    "reach": f.reach,
                    "impact": f.impact,
                    "confidence": f.confidence,
                    "effort_weeks": f.effort,
                },
                "strategy_bucket": f.strategy_bucket,
                "rationale": f.rationale,
                "from_cluster_id": f.cluster_id,
            }
            for f in features
        ]

        feature_titles = {f.id: f.title for f in features}
        roadmap_out: dict = {"now": [], "next": [], "later": []}
        for item in roadmap:
            if item.horizon not in roadmap_out:
                continue
            roadmap_out[item.horizon].append({
                "feature_id": item.feature_id,
                "feature_title": feature_titles.get(item.feature_id, "?"),
                "theme": item.theme,
                "estimated_weeks": item.estimated_weeks,
                "depends_on": item.depends_on,
            })

        # PRDs: take the latest version of each PRD in the project (latest per feature)
        prd_rows = list(
            db.scalars(
                select(PRD)
                .join(Feature, Feature.id == PRD.feature_id)
                .where(Feature.project_id == project_id)
                .order_by(PRD.feature_id, PRD.version.desc())
            )
        )
        latest_per_feature: dict[int, PRD] = {}
        for p in prd_rows:
            latest_per_feature.setdefault(p.feature_id, p)

        prds_out: list[dict] = []
        for prd in latest_per_feature.values():
            feature = next((f for f in features if f.id == prd.feature_id), None)
            notes = list(db.scalars(select(CritiqueNote).where(CritiqueNote.prd_id == prd.id)))
            prds_out.append({
                "id": prd.id,
                "feature_id": prd.feature_id,
                "feature_title": feature.title if feature else None,
                "feature_rice_score": feature.rice_score if feature else None,
                "version": prd.version,
                "status": prd.status,
                "title": prd.title,
                "summary": prd.summary,
                "content": prd.content,
                "source_feedback_ids": prd.source_feedback_ids,
                "critique_notes": [
                    {
                        "section": n.section,
                        "severity": n.severity,
                        "category": n.category,
                        "message": n.message,
                        "suggestion": n.suggestion,
                        "status": n.status,
                    }
                    for n in notes
                ],
            })

        snapshots = [
            ("sample_output_clusters.json", clusters_out),
            ("sample_output_features.json", features_out),
            ("sample_output_roadmap.json", roadmap_out),
            ("sample_output_prds.json", prds_out),
        ]
        for name, payload in snapshots:
            p = DATA / name
            p.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
            print(f"wrote {p.relative_to(ROOT)}")
    finally:
        db.close()


def main() -> None:
    project_id = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    export_input_files()
    print()
    export_output_files(project_id)


if __name__ == "__main__":
    main()
