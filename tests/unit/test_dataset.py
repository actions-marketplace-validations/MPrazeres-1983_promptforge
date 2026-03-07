"""Unit tests for Dataset loader."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from promptforge.core.dataset import Dataset
from promptforge.core.errors import DatasetError


@pytest.fixture
def valid_yaml_dataset(tmp_path: Path) -> Path:
    content = {
        "dataset_id": "test_ds",
        "description": "Test dataset",
        "cases": [
            {"id": "c001", "input": {"text": "Hello"}, "expected": {"category": "billing"}},
            {"id": "c002", "input": {"text": "World"}, "expected": {"category": "bug"}},
        ],
    }
    p = tmp_path / "test_ds.yaml"
    p.write_text(yaml.dump(content), encoding="utf-8")
    return p


@pytest.fixture
def valid_jsonl_dataset(tmp_path: Path) -> Path:
    p = tmp_path / "test_ds.jsonl"
    records = [
        {"id": "c001", "input": {"text": "Hello"}, "expected": {"category": "billing"}},
        {"id": "c002", "input": {"text": "World"}, "expected": {"category": "bug"}},
    ]
    p.write_text("\n".join(json.dumps(r) for r in records), encoding="utf-8")
    return p


def test_load_yaml_dataset(valid_yaml_dataset: Path) -> None:
    ds = Dataset.from_file(valid_yaml_dataset)
    assert ds.dataset_id == "test_ds"
    assert len(ds.cases) == 2
    assert ds.content_hash != ""


def test_load_jsonl_dataset(valid_jsonl_dataset: Path) -> None:
    ds = Dataset.from_file(valid_jsonl_dataset)
    assert ds.dataset_id == "test_ds"
    assert len(ds.cases) == 2


def test_content_hash_is_stable(valid_yaml_dataset: Path) -> None:
    ds1 = Dataset.from_file(valid_yaml_dataset)
    ds2 = Dataset.from_file(valid_yaml_dataset)
    assert ds1.content_hash == ds2.content_hash


def test_missing_file_raises_error() -> None:
    with pytest.raises(DatasetError, match="not found"):
        Dataset.from_file("/nonexistent/dataset.yaml")


def test_unsupported_format_raises_error(tmp_path: Path) -> None:
    p = tmp_path / "data.csv"
    p.write_text("id,text\nc001,hello", encoding="utf-8")
    with pytest.raises(DatasetError, match="Unsupported"):
        Dataset.from_file(p)


def test_case_expected_defaults_to_empty(tmp_path: Path) -> None:
    content = {
        "dataset_id": "minimal",
        "cases": [{"id": "c001", "input": {"text": "hi"}}],
    }
    p = tmp_path / "minimal.yaml"
    p.write_text(yaml.dump(content), encoding="utf-8")
    ds = Dataset.from_file(p)
    assert ds.cases[0].expected == {}