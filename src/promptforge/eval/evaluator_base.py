"""Abstract evaluator interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class EvalScore:
    evaluator: str
    dimension: str
    score: float
    rationale: str = ""
    metadata: dict[str, Any] | None = None


class EvaluatorBase(ABC):
    name: str = "base"

    @abstractmethod
    def evaluate(
        self,
        output_raw: str,
        output_parsed: dict | None,
        expected: dict,
        config: dict,
        prompt_spec: Any,
    ) -> EvalScore:
        ...