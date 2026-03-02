# src/promptforge/llm/client_base.py
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class LLMResponse:
    content: str
    prompt_tokens: int
    completion_tokens: int
    model: str

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens


class LLMClient(ABC):
    @abstractmethod
    def complete(self, prompt: str, params: Dict[str, Any]) -> LLMResponse:
        """Send a prompt and return a structured response."""
        ...