"""Anthropic provider adapter."""

from __future__ import annotations

import os
from typing import Any, Dict, Optional

import anthropic
from anthropic.types import TextBlock
from anthropic import Anthropic, NOT_GIVEN
from anthropic._types import Omit

from promptforge.llm.client_base import LLMClient, LLMResponse
from promptforge.core.errors import LLMClientError


class AnthropicClient(LLMClient):
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

    def complete(
        self,
        prompt: str,
        params: Optional[Dict[str, Any]] = None,
        system_prompt: Optional[str] = None,
    ) -> LLMResponse:
        resolved_params = params or self.params

        # Constrói kwargs opcionais — a API Anthropic aceita 'system' como argumento separado
        extra = {}
        if system_prompt and system_prompt.strip():
            extra["system"] = system_prompt

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=resolved_params.get("max_tokens", 512),
                messages=[{"role": "user", "content": prompt}],
                temperature=resolved_params.get("temperature", 0.0),
                system=system_prompt if system_prompt and system_prompt.strip() else Omit(),
            )
        except Exception as e:
            raise LLMClientError(f"Anthropic API error: {e}") from e

        content = next(
            (block.text for block in response.content if isinstance(block, TextBlock)),
            ""
        )

        return LLMResponse(
            content=content,
            prompt_tokens=response.usage.input_tokens,
            completion_tokens=response.usage.output_tokens,
            model=response.model,
        )