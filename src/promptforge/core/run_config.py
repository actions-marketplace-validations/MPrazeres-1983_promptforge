"""RunConfig: model, provider, evaluator, and regression configuration."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field

from promptforge.core.errors import RunConfigError


class EvaluatorConfig(BaseModel):
    type: str  # "heuristic" | "judge"
    name: str
    config: dict[str, Any] = Field(default_factory=dict)


class RegressionConfig(BaseModel):
    thresholds: dict[str, float] = Field(default_factory=dict)


class RunConfig(BaseModel):
    provider: str = "openai"
    model: str = "gpt-4o-mini"
    params: dict[str, Any] = Field(default_factory=lambda: {"temperature": 0.0, "max_tokens": 512})
    evaluators: list[EvaluatorConfig] = Field(default_factory=list)
    regression: RegressionConfig = Field(default_factory=RegressionConfig)

    @classmethod
    def from_yaml(cls, path: str | Path) -> "RunConfig":
        p = Path(path)
        if not p.exists():
            raise RunConfigError(f"RunConfig file not found: {path}")
        try:
            raw = yaml.safe_load(p.read_text(encoding="utf-8"))
        except yaml.YAMLError as e:
            raise RunConfigError(f"YAML parse error: {e}") from e
        try:
            return cls.model_validate(raw)
        except Exception as e:
            raise RunConfigError(f"Validation error: {e}") from e