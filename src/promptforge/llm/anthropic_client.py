"""Anthropic provider adapter."""

from __future__ import annotations

import os
from typing import Any

import anthropic

from promptforge.llm.client_base import LLMClientBase, LLMResponse
from promptforge.core.errors import LLMClientError


class AnthropicClient(LLMClientBase):
    def __init__(self, model: str = "claude-3-haiku-20240307", params: dict[str, Any] | None = None) -> None:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise LLMClientError("ANTHROPIC_API_KEY environment variable not set.")
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model
        self.params = params or {"temperature": 0.0, "max_tokens": 512}

    def complete(self, prompt: str) -> LLMResponse:
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.params.get("max_tokens", 512),
                messages=[{"role": "user", "content": prompt}],
                temperature=self.params.get("temperature", 0.0),
            )
        except Exception as e:
            raise LLMClientError(f"Anthropic API error: {e}") from e

        content = response.content[0].text if response.content else ""
        return LLMResponse(
            content=content,
            prompt_tokens=response.usage.input_tokens,
            completion_tokens=response.usage.output_tokens,
            model=response.model,
        )