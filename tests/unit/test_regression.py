"""Unit tests for the regression engine."""

from __future__ import annotations


from promptforge.eval.regression import RegressionEngine


class MockScoreRepo:
    def __init__(self, data: dict):
        self._data = data

    def get_by_run(self, run_id: str):
        return self._data.get(run_id, [])


def _make_scores(run_id: str, evaluator: str, values: list[float]) -> list[dict]:
    return [
        {"run_id": run_id, "case_id": f"c{i:03d}", "evaluator": evaluator,
         "dimension": evaluator, "score": v, "rationale": ""}
        for i, v in enumerate(values)
    ]


def test_no_regression_when_scores_stable():
    engine = RegressionEngine()
    engine.score_repo = MockScoreRepo({
        "run_a": _make_scores("run_a", "json_validity", [1.0, 1.0, 1.0]),
        "run_b": _make_scores("run_b", "json_validity", [1.0, 1.0, 1.0]),
    })
    result = engine.compare("run_a", "run_b")
    assert not result.has_regressions


def test_regression_detected_when_score_drops():
    engine = RegressionEngine()
    engine.score_repo = MockScoreRepo({
        "run_a": _make_scores("run_a", "json_validity", [1.0, 1.0, 1.0]),
        "run_b": _make_scores("run_b", "json_validity", [0.5, 0.5, 0.5]),
    })
    result = engine.compare("run_a", "run_b")
    assert result.has_regressions
    assert result.regressions[0].evaluator == "json_validity"


def test_improvement_not_flagged_as_regression():
    engine = RegressionEngine()
    engine.score_repo = MockScoreRepo({
        "run_a": _make_scores("run_a", "json_validity", [0.5, 0.5, 0.5]),
        "run_b": _make_scores("run_b", "json_validity", [1.0, 1.0, 1.0]),
    })
    result = engine.compare("run_a", "run_b")
    assert not result.has_regressions


def test_custom_threshold_respected():
    engine = RegressionEngine()
    engine.score_repo = MockScoreRepo({
        "run_a": _make_scores("run_a", "json_validity", [1.0, 1.0, 1.0]),
        "run_b": _make_scores("run_b", "json_validity", [0.97, 0.97, 0.97]),
    })
    # Delta = -0.03, default threshold = 0.05 → no regression
    result = engine.compare("run_a", "run_b")
    assert not result.has_regressions

    # With tight threshold = 0.01 → regression
    result2 = engine.compare("run_a", "run_b", thresholds={"json_validity": 0.01})
    assert result2.has_regressions


def test_delta_values_are_correct():
    engine = RegressionEngine()
    engine.score_repo = MockScoreRepo({
        "run_a": _make_scores("run_a", "json_validity", [1.0, 1.0]),
        "run_b": _make_scores("run_b", "json_validity", [0.8, 0.8]),
    })
    result = engine.compare("run_a", "run_b")
    diff = result.diffs[0]
    assert abs(diff.delta - (-0.2)) < 0.001
    assert abs(diff.baseline_mean - 1.0) < 0.001
    assert abs(diff.candidate_mean - 0.8) < 0.001