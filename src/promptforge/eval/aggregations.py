"""Score aggregation utilities."""

from __future__ import annotations

import statistics
from typing import Any


def mean_score(scores: list[float]) -> float:
    if not scores:
        return 0.0
    return statistics.mean(scores)


def p95_latency(latencies_ms: list[float]) -> float:
    if not latencies_ms:
        return 0.0
    sorted_l = sorted(latencies_ms)
    idx = int(len(sorted_l) * 0.95)
    return sorted_l[min(idx, len(sorted_l) - 1)]


def failure_rate(scores: list[float], threshold: float = 0.5) -> float:
    if not scores:
        return 0.0
    failures = sum(1 for s in scores if s < threshold)
    return failures / len(scores)

def generate_ascii_bar(score: float, width: int = 20) -> str:
    """Generates a visual progress bar: [##########----------]"""
    filled = int(score * width)
    return "█" * filled + "░" * (width - filled)


def aggregate_run_scores(
    scores: list[dict[str, Any]],
) -> dict[str, dict[str, float]]:
    """Aggregate scores by evaluator/dimension.
    
    Returns: {evaluator: {"mean": float, "failure_rate": float, "count": int}}
    """
    by_evaluator: dict[str, list[float]] = {}
    for s in scores:
        ev = s["evaluator"]
        by_evaluator.setdefault(ev, []).append(float(s["score"]))

    result = {}
    for ev, vals in by_evaluator.items():
        result[ev] = {
            "mean": mean_score(vals),
            "failure_rate": failure_rate(vals),
            "count": len(vals),
        }
    return result