"""Parses uploaded CSV/JSON into FeedbackItem rows. Tolerant of column names."""
from __future__ import annotations

import csv
import io
import json
import logging
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from app.models.feedback import FeedbackItem

log = logging.getLogger(__name__)

TEXT_KEYS = ["text", "body", "comment", "review", "feedback", "message", "content"]
SOURCE_KEYS = ["source", "channel", "origin", "platform"]
RATING_KEYS = ["rating", "stars", "score"]
SEGMENT_KEYS = ["user_segment", "segment", "persona", "tier"]
AUTHOR_KEYS = ["author", "user", "username", "name"]
DATE_KEYS = ["created_at", "date", "timestamp", "submitted_at"]


def _first_match(row: dict[str, Any], keys: list[str]) -> Any:
    lowered = {k.lower(): v for k, v in row.items()}
    for k in keys:
        if k in lowered and lowered[k] not in (None, "", "null"):
            return lowered[k]
    return None


def _to_int(v: Any) -> int | None:
    try:
        return int(v) if v is not None and str(v).strip() != "" else None
    except (TypeError, ValueError):
        return None


def _to_datetime(v: Any) -> datetime | None:
    if v is None or v == "":
        return None
    if isinstance(v, datetime):
        return v
    s = str(v).strip()
    for fmt in ("%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        return None


def _row_to_item(project_id: int, row: dict[str, Any]) -> FeedbackItem | None:
    text = _first_match(row, TEXT_KEYS)
    if not text or not str(text).strip():
        return None
    return FeedbackItem(
        project_id=project_id,
        text=str(text).strip(),
        source=(str(_first_match(row, SOURCE_KEYS)) if _first_match(row, SOURCE_KEYS) else None),
        rating=_to_int(_first_match(row, RATING_KEYS)),
        user_segment=(str(_first_match(row, SEGMENT_KEYS)) if _first_match(row, SEGMENT_KEYS) else None),
        author=(str(_first_match(row, AUTHOR_KEYS)) if _first_match(row, AUTHOR_KEYS) else None),
        created_at=_to_datetime(_first_match(row, DATE_KEYS)),
    )


def ingest_csv(db: Session, project_id: int, content: bytes) -> tuple[int, int, int]:
    reader = csv.DictReader(io.StringIO(content.decode("utf-8-sig", errors="ignore")))
    return _bulk_insert(db, project_id, list(reader))


def ingest_json(db: Session, project_id: int, content: bytes) -> tuple[int, int, int]:
    data = json.loads(content.decode("utf-8", errors="ignore"))
    if isinstance(data, dict):
        # accept {"items": [...]} or {"feedback": [...]}
        for key in ("items", "feedback", "data", "results"):
            if key in data and isinstance(data[key], list):
                data = data[key]
                break
    if not isinstance(data, list):
        raise ValueError("JSON must be a list of objects, or an object containing an 'items'/'feedback' list")
    return _bulk_insert(db, project_id, data)


def _bulk_insert(db: Session, project_id: int, rows: list[dict[str, Any]]) -> tuple[int, int, int]:
    inserted, skipped = 0, 0
    for raw in rows:
        if not isinstance(raw, dict):
            skipped += 1
            continue
        item = _row_to_item(project_id, raw)
        if item is None:
            skipped += 1
            continue
        db.add(item)
        inserted += 1
    db.commit()
    return inserted, skipped, inserted + skipped
