"""PromptSpec: versioned, typed prompt definition."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field

from promptforge.utils.hashing import hash_content
from promptforge.core.errors import PromptSpecError


class InputDef(BaseModel):
    type: str = "string"
    description: str = ""


class OutputDef(BaseModel):
    format: str = "text"  # "text" | "json"
    schema_: dict[str, Any] = Field(default_factory=dict, alias="schema")

    model_config = {"populate_by_name": True}


class PromptSpec(BaseModel):
    id: str
    version: str
    description: str
    template: str
    inputs: dict[str, InputDef] = Field(default_factory=dict)
    output: OutputDef = Field(default_factory=OutputDef)
    params: dict[str, Any] = Field(default_factory=lambda: {"temperature": 0.0, "max_tokens": 512})
    tags: list[str] = Field(default_factory=list)

    # Computed after load
    source_path: str = ""
    content_hash: str = ""

    @classmethod
    def from_yaml(cls, path: str | Path) -> "PromptSpec":
        p = Path(path)
        if not p.exists():
            raise PromptSpecError(f"PromptSpec file not found: {path}")
        try:
            raw = yaml.safe_load(p.read_text(encoding="utf-8"))
        except yaml.YAMLError as e:
            raise PromptSpecError(f"YAML parse error in {path}: {e}") from e

        try:
            spec = cls.model_validate(raw)
        except Exception as e:
            raise PromptSpecError(f"Validation error in {path}: {e}") from e

        spec.source_path = str(p.resolve())
        spec.content_hash = hash_content(
            spec.template + yaml.dump(spec.params, sort_keys=True)
        )
        return spec

    def input_names(self) -> list[str]:
        return list(self.inputs.keys())