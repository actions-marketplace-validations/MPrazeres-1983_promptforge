"""Dataset: golden set of test cases."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field

from promptforge.utils.hashing import hash_content
from promptforge.core.errors import DatasetError


class TestCase(BaseModel):
    id: str
    input: dict[str, Any]
    expected: dict[str, Any] = Field(default_factory=dict)
    notes: str = ""


class Dataset(BaseModel):
    dataset_id: str
    description: str = ""
    cases: list[TestCase]
    content_hash: str = ""
    source_path: str = ""

    @classmethod
    def from_file(cls, path: str | Path) -> "Dataset":
        p = Path(path)
        if not p.exists():
            raise DatasetError(f"Dataset file not found: {path}")

        if p.suffix in (".yaml", ".yml"):
            return cls._from_yaml(p)
        elif p.suffix == ".jsonl":
            return cls._from_jsonl(p)
        else:
            raise DatasetError(f"Unsupported dataset format: {p.suffix}")

    @classmethod
    def _from_yaml(cls, p: Path) -> "Dataset":
        try:
            raw = yaml.safe_load(p.read_text(encoding="utf-8"))
        except yaml.YAMLError as e:
            raise DatasetError(f"YAML parse error: {e}") from e
        try:
            ds = cls.model_validate(raw)
        except Exception as e:
            raise DatasetError(f"Validation error: {e}") from e
        ds.source_path = str(p.resolve())
        ds.content_hash = hash_content(json.dumps(
            [c.model_dump() for c in ds.cases], sort_keys=True
        ))
        return ds

    @classmethod
    def _from_jsonl(cls, p: Path) -> "Dataset":
        cases = []
        for i, line in enumerate(p.read_text(encoding="utf-8").splitlines()):
            line = line.strip()
            if not line:
                continue
            try:
                cases.append(TestCase.model_validate(json.loads(line)))
            except Exception as e:
                raise DatasetError(f"JSONL parse error at line {i+1}: {e}") from e
        ds = cls(dataset_id=p.stem, cases=cases)
        ds.source_path = str(p.resolve())
        ds.content_hash = hash_content(json.dumps(
            [c.model_dump() for c in ds.cases], sort_keys=True
        ))
        return ds