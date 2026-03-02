"""Regression engine: compare two runs and detect regressions."""

from __future__ import annotations

from dataclasses import dataclass, field

from promptforge.store.repositories import ScoreRepository, RunRepository
from promptforge.eval.aggregations import aggregate_run_scores


@dataclass
class DimensionDiff:
    evaluator: str
    baseline_mean: float
    candidate_mean: float
    delta: float
    is_regression: bool
    threshold: float


@dataclass
class RegressionResult:
    baseline_run_id: str
    candidate_run_id: str
    diffs: list[DimensionDiff] = field(default_factory=list)

    @property
    def has_regressions(self) -> bool:
        return any(d.is_regression for d in self.diffs)

    @property
    def regressions(self) -> list[DimensionDiff]:
        return [d for d in self.diffs if d.is_regression]


class RegressionEngine:
    DEFAULT_THRESHOLD = 0.05

    def __init__(self) -> None:
        self.score_repo = ScoreRepository()
        self.run_repo = RunRepository()

    def compare(
        self,
        baseline_run_id: str,
        candidate_run_id: str,
        thresholds: dict[str, float] | None = None,
    ) -> RegressionResult:
        thresholds = thresholds or {}

        baseline_scores = self.score_repo.get_by_run(baseline_run_id)
        candidate_scores = self.score_repo.get_by_run(candidate_run_id)

        baseline_agg = aggregate_run_scores(baseline_scores)
        candidate_agg = aggregate_run_scores(candidate_scores)

        all_evaluators = set(baseline_agg) | set(candidate_agg)
        diffs = []

        for ev in sorted(all_evaluators):
            b_mean = baseline_agg.get(ev, {}).get("mean", 0.0)
            c_mean = candidate_agg.get(ev, {}).get("mean", 0.0)
            delta = c_mean - b_mean
            threshold = thresholds.get(ev, self.DEFAULT_THRESHOLD)
            is_regression = delta < -threshold

            diffs.append(DimensionDiff(
                evaluator=ev,
                baseline_mean=b_mean,
                candidate_mean=c_mean,
                delta=delta,
                is_regression=is_regression,
                threshold=threshold,
            ))

        return RegressionResult(
            baseline_run_id=baseline_run_id,
            candidate_run_id=candidate_run_id,
            diffs=diffs,
        )