"""Integration test: full eval pipeline with SQLite store."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml

from promptforge.core.prompt_spec import PromptSpec
from promptforge.core.dataset import Dataset
from promptforge.core.run_config import RunConfig
from promptforge.core.pipeline import EvalPipeline
from promptforge.store.db import init_db
from promptforge.store.repositories import RunRepository, ScoreRepository


@pytest.fixture(autouse=True)
def use_temp_db(tmp_path, monkeypatch):
    """Redirect DB to a temp directory for each test."""
    import promptforge.store.db as db_module
    db_module.DB_PATH = tmp_path / ".promptforge" / "test.db"
    init_db()
    yield


@pytest.fixture
def prompt_spec_file(tmp_path: Path) -> Path:
    content = {
        "id": "test_summarizer",
        "version": "0.1.0",
        "description": "Test prompt",
        "template": "Summarise: {{ text }}",
        "inputs": {"text": {"type": "string"}},
        "output": {"format": "json", "schema": {"category": {"type": "string"}}},
        "params": {"temperature": 0.0, "max_tokens": 100},
        "tags": [],
    }
    p = tmp_path / "prompt.yaml"
    p.write_text(yaml.dump(content), encoding="utf-8")
    return p


@pytest.fixture
def dataset_file(tmp_path: Path) -> Path:
    content = {
        "dataset_id": "test_golden",
        "cases": [
            {"id": "c001", "input": {"text": "I was charged twice."}, "expected": {"category": "billing"}},
            {"id": "c002", "input": {"text": "App crashes on export."}, "expected": {"category": "bug"}},
        ],
    }
    p = tmp_path / "dataset.yaml"
    p.write_text(yaml.dump(content), encoding="utf-8")
    return p


@pytest.fixture
def run_config_file(tmp_path: Path) -> Path:
    content = {
        "provider": "openai",
        "model": "gpt-4o-mini",
        "params": {"temperature": 0.0, "max_tokens": 100},
        "evaluators": [
            {"type": "heuristic", "name": "json_validity"},
            {"type": "heuristic", "name": "schema_match"},
            {"type": "heuristic", "name": "field_match", "config": {"field": "category"}},
        ],
        "regression": {"thresholds": {"json_validity": 0.05}},
    }
    p = tmp_path / "config.yaml"
    p.write_text(yaml.dump(content), encoding="utf-8")
    return p


def _mock_llm_response(text: str):
    from promptforge.llm.client_base import LLMResponse
    return LLMResponse(
        content=text,
        prompt_tokens=10,
        completion_tokens=20,
        model="gpt-4o-mini",
    )


@patch("promptforge.core.pipeline._build_llm_client")
def test_full_pipeline_stores_run_and_scores(
    mock_build_client,
    prompt_spec_file,
    dataset_file,
    run_config_file,
):
    mock_client = MagicMock()
    mock_client.complete.side_effect = [
        _mock_llm_response('{"category": "billing", "sentiment": "negative"}'),
        _mock_llm_response('{"category": "bug", "sentiment": "negative"}'),
    ]
    mock_build_client.return_value = mock_client

    ps = PromptSpec.from_yaml(prompt_spec_file)
    ds = Dataset.from_file(dataset_file)
    rc = RunConfig.from_yaml(run_config_file)

    pipeline = EvalPipeline(ps, ds, rc)
    run_id = pipeline.run()

    run_repo = RunRepository()
    run = run_repo.get_run(run_id)
    assert run is not None
    assert run["prompt_id"] == "test_summarizer"
    assert run["total_cases"] == 2

    score_repo = ScoreRepository()
    scores = score_repo.get_by_run(run_id)
    assert len(scores) > 0

    json_scores = [s for s in scores if s["evaluator"] == "json_validity"]
    assert all(s["score"] == 1.0 for s in json_scores)


@patch("promptforge.core.pipeline._build_llm_client")
def test_pipeline_handles_invalid_json_output(
    mock_build_client,
    prompt_spec_file,
    dataset_file,
    run_config_file,
):
    mock_client = MagicMock()
    mock_client.complete.side_effect = [
        _mock_llm_response("This is not JSON at all."),
        _mock_llm_response("Also not JSON."),
    ]
    mock_build_client.return_value = mock_client

    ps = PromptSpec.from_yaml(prompt_spec_file)
    ds = Dataset.from_file(dataset_file)
    rc = RunConfig.from_yaml(run_config_file)

    pipeline = EvalPipeline(ps, ds, rc)
    run_id = pipeline.run()

    score_repo = ScoreRepository()
    scores = score_repo.get_by_run(run_id)
    json_scores = [s for s in scores if s["evaluator"] == "json_validity"]
    assert all(s["score"] == 0.0 for s in json_scores)