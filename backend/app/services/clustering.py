"""HDBSCAN clustering on feedback embeddings.

Why HDBSCAN: density-based clustering finds groups of arbitrary shape, doesn't
need k specified up-front, and labels low-density items as noise (-1) which we
keep as an 'Uncategorized' bucket.
"""
from __future__ import annotations

import logging

import numpy as np
from sklearn.cluster import HDBSCAN

log = logging.getLogger(__name__)


def cluster_embeddings(
    embeddings: list[list[float]],
    min_cluster_size: int = 8,
    min_samples: int | None = None,
) -> list[int]:
    """Return a label per input (label -1 = noise/uncategorized)."""
    if not embeddings:
        return []
    X = np.array(embeddings, dtype=np.float32)
    # Normalize for cosine-like behavior under euclidean
    norms = np.linalg.norm(X, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    X = X / norms

    n = len(embeddings)
    # Scale min_cluster_size to dataset size; never below 3
    effective_min = max(3, min(min_cluster_size, max(3, n // 20)))

    model = HDBSCAN(
        min_cluster_size=effective_min,
        min_samples=min_samples,
        metric="euclidean",
        cluster_selection_method="eom",
    )
    labels = model.fit_predict(X)
    log.info(
        "HDBSCAN: %d items -> %d clusters (+ %d noise) with min_cluster_size=%d",
        n,
        len({l for l in labels if l != -1}),
        int((labels == -1).sum()),
        effective_min,
    )
    return [int(l) for l in labels]
