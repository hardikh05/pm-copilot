"""Agent 5: PRD Critic. Reviews a PRD, writes CritiqueNote rows, and optionally
triggers a revision loop via prd_generator until passes or max_iterations reached."""
from __future__ import annotations

import json
import logging

from sqlalchemy.orm import Session

from app.agents import llm, prd_generator, prompts
from app.models.prd import PRD, CritiqueNote

log = logging.getLogger(__name__)

VALID_SECTIONS = {"problem", "goal", "user_stories", "success_metrics", "requirements", "edge_cases"}
VALID_SEVERITY = {"low", "medium", "high"}
VALID_CATEGORIES = {"ambiguity", "missing_metric", "unclear_requirement", "untestable"}


def critique(db: Session, prd_id: int) -> tuple[list[CritiqueNote], bool]:
    prd: PRD | None = db.get(PRD, prd_id)
    if prd is None:
        raise ValueError(f"PRD {prd_id} not found")

    ai = llm.chat_json(
        prompts.PRD_CRITIC_SYSTEM,
        prompts.PRD_CRITIC_USER.format(prd_json=json.dumps(prd.content, indent=2)),
        temperature=0.2,
    )

    notes_raw = ai.get("notes", []) if isinstance(ai, dict) else []
    passes = bool(ai.get("passes", False)) if isinstance(ai, dict) else False

    created: list[CritiqueNote] = []
    has_high = False
    for entry in notes_raw:
        if not isinstance(entry, dict):
            continue
        section = str(entry.get("section", "")).lower()
        severity = str(entry.get("severity", "low")).lower()
        category = str(entry.get("category", "ambiguity")).lower()
        if section not in VALID_SECTIONS:
            section = "problem"
        if severity not in VALID_SEVERITY:
            severity = "low"
        if category not in VALID_CATEGORIES:
            category = "ambiguity"
        if severity == "high":
            has_high = True

        note = CritiqueNote(
            prd_id=prd.id,
            section=section,
            severity=severity,
            category=category,
            message=str(entry.get("message", ""))[:2000],
            suggestion=str(entry.get("suggestion", ""))[:2000] or None,
        )
        db.add(note)
        created.append(note)

    db.commit()
    for n in created:
        db.refresh(n)
    return created, (passes and not has_high)


def critique_with_revisions(
    db: Session,
    prd_id: int,
    max_iterations: int = 2,
) -> dict:
    """Loop: critique -> if high-severity notes, regenerate -> critique again."""
    prd = db.get(PRD, prd_id)
    if prd is None:
        raise ValueError(f"PRD {prd_id} not found")
    feature_id = prd.feature_id

    iterations: list[dict] = []
    current_prd_id = prd_id
    for i in range(max_iterations + 1):
        notes, passed = critique(db, current_prd_id)
        iterations.append({
            "prd_id": current_prd_id,
            "note_count": len(notes),
            "high_severity_count": sum(1 for n in notes if n.severity == "high"),
            "passed": passed,
        })
        if passed or i == max_iterations:
            break
        # Regenerate by re-running the generator (it bumps version)
        log.info("PRD %d failed critic, regenerating (iter %d)", current_prd_id, i + 1)
        new_prd = prd_generator.run(db, feature_id)
        current_prd_id = new_prd.id

    return {"iterations": iterations, "final_prd_id": current_prd_id}
