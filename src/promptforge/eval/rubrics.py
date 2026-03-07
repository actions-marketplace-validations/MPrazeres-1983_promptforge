"""Rubric loader and validator for LLM-as-judge."""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, Field

from promptforge.core.errors import EvaluatorError


class RubricDimension(BaseModel):
    name: str
    scale: list[int]
    instruction: str


class Rubric(BaseModel):
    rubric_id: str
    judge_model: str = "gpt-4o"
    dimensions: list[RubricDimension] = Field(default_factory=list)

    @classmethod
    def from_yaml(cls, path: str | Path) -> "Rubric":
        p = Path(path)
        if not p.exists():
            raise EvaluatorError(f"Rubric file not found: {path}")
        try:
            raw = yaml.safe_load(p.read_text(encoding="utf-8"))
            return cls.model_validate(raw)
        except Exception as e:
            raise EvaluatorError(f"Rubric load error: {e}") from e