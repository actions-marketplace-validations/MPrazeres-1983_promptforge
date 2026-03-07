"""Anthropic provider adapter."""

from __future__ import annotations

import os
from typing import Any, Dict, Optional

import anthropic

from promptforge.llm.client_base import LLMClient, LLMResponse   # FIX #1: era LLMClientBase
from promptforge.core.errors import LLMClientError


class AnthropicClient(LLMClient):                                  # FIX #1: era LLMClientBase
    def __init__(
        self,
        model: str = "claude-3-haiku-20240307",
        params: Optional[Dict[str, Any]] = None,
    ) -> None:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise LLMClientError("ANTHROPIC_API_KEY environment variable not set.")
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model
        self.params = params or {"temperature": 0.0, "max_tokens": 512}

    def complete(self, prompt: str, params: Dict[str, Any] | None = None) -> LLMResponse:
        # FIX #2: era `complete(self, prompt: str)` — faltava o parâmetro `params`
        # O pipeline chama client.complete(rendered, self.rc.params) — 2 argumentos
        resolved_params = params or self.params
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=resolved_params.get("max_tokens", 512),
                messages=[{"role": "user", "content": prompt}],
                temperature=resolved_params.get("temperature", 0.0),
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
