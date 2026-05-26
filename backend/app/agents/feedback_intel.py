"""Agent 1: Feedback Intelligence.
Pipeline: ensure embeddings -> cluster -> classify sentiment -> label clusters with LLM.
Persists Cluster rows and updates FeedbackItem.cluster_id + sentiment.
"""
from __future__ import annotations

import logging
from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agents import llm, prompts
from app.models.cluster import Cluster
from app.models.feedback import FeedbackItem
from app.services.clustering import cluster_embeddings
from app.services.embeddings import embed_missing

log = logging.getLogger(__name__)


def _classify_sentiment(items: list[FeedbackItem]) -> None:
    """Batch sentiment classification with the LLM. Mutates items in place."""
    BATCH = 25
    for i in range(0, len(items), BATCH):
        chunk = items[i : i + BATCH]
        listing = "\n".join(f"{idx + 1}. {it.text}" for idx, it in enumerate(chunk))
        try:
            result = llm.chat_json(
                prompts.SENTIMENT_SYSTEM,
                prompts.SENTIMENT_USER.format(n=len(chunk), items=listing),
                temperature=0.0,
            )
        except ValueError:
            log.warning("sentiment batch %d failed; defaulting to neutral", i)
            for it in chunk:
                it.sentiment = "neutral"
                it.sentiment_score = 0.0
            continue

        # result expected to be {"items": [...]} or just [...] — handle both
        if isinstance(result, dict) and "items" in result:
            result = result["items"]
        elif isinstance(result, dict) and "results" in result:
            result = result["results"]

        by_idx = {}
        if isinstance(result, list):
            for entry in result:
                if isinstance(entry, dict) and "i" in entry:
                    by_idx[int(entry["i"])] = entry

        for idx, it in enumerate(chunk, start=1):
            entry = by_idx.get(idx, {})
            label = str(entry.get("label", "neutral")).lower()
            if label not in {"positive", "neutral", "negative"}:
                label = "neutral"
            try:
                score = float(entry.get("score", 0.0))
            except (TypeError, ValueError):
                score = 0.0
            it.sentiment = label
            it.sentiment_score = max(-1.0, min(1.0, score))


def _label_cluster(samples: list[str], n: int) -> tuple[str, str]:
    sample_n = min(len(samples), 8)
    samples_str = "\n".join(f"- {s}" for s in samples[:sample_n])
    try:
        result = llm.chat_json(
            prompts.CLUSTER_LABEL_SYSTEM,
            prompts.CLUSTER_LABEL_USER.format(n=n, sample_n=sample_n, samples=samples_str),
            temperature=0.3,
        )
        return str(result.get("label", "Unlabeled"))[:200], str(result.get("summary", ""))[:1000]
    except Exception as e:  # noqa: BLE001
        log.warning("cluster labeling failed: %s", e)
        return "Unlabeled cluster", ""


def run(db: Session, project_id: int) -> dict:
    """Run the full feedback intelligence pipeline. Returns a small status dict."""
    # 1. Embeddings
    embedded = embed_missing(db, project_id)
    log.info("project %d: embedded %d new items", project_id, embedded)

    # 2. Load all items with embeddings
    items: list[FeedbackItem] = list(
        db.scalars(
            select(FeedbackItem).where(
                FeedbackItem.project_id == project_id,
                FeedbackItem.embedding.is_not(None),
            )
        )
    )
    if not items:
        return {"clusters": 0, "items": 0}

    # 3. Cluster
    embeddings = [list(it.embedding) for it in items]  # type: ignore[arg-type]
    labels = cluster_embeddings(embeddings)

    # 4. Sentiment (classify items missing sentiment)
    needs_sent = [it for it in items if it.sentiment is None]
    if needs_sent:
        _classify_sentiment(needs_sent)
        db.commit()

    # 5. Wipe old clusters for this project, rebuild
    db.query(Cluster).filter(Cluster.project_id == project_id).delete()
    db.flush()

    by_label: dict[int, list[FeedbackItem]] = defaultdict(list)
    for it, lbl in zip(items, labels):
        by_label[lbl].append(it)

    created = 0
    for raw_label, group in by_label.items():
        if raw_label == -1 or len(group) < 3:
            # Noise / tiny clusters: leave items without a cluster
            for it in group:
                it.cluster_id = None
            continue

        # Sentiment stats
        sentiments = [it.sentiment or "neutral" for it in group]
        scores = [it.sentiment_score or 0.0 for it in group]
        n = len(group)
        pos = sum(1 for s in sentiments if s == "positive") / n
        neu = sum(1 for s in sentiments if s == "neutral") / n
        neg = sum(1 for s in sentiments if s == "negative") / n
        avg = sum(scores) / n

        samples = [it.text for it in group[:8]]
        label_text, summary = _label_cluster(samples, n)

        cluster = Cluster(
            project_id=project_id,
            label=label_text,
            summary=summary,
            size=n,
            positive_pct=pos,
            neutral_pct=neu,
            negative_pct=neg,
            avg_sentiment=avg,
        )
        db.add(cluster)
        db.flush()  # get id
        for it in group:
            it.cluster_id = cluster.id
        created += 1

    db.commit()
    return {"clusters": created, "items": len(items)}
