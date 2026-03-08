# src/promptforge/llm/openai_client.py
from __future__ import annotations

import os
from typing import Any, Dict, Optional

from openai import OpenAI

from promptforge.llm.client_base import LLMClient, LLMResponse


class OpenAIClient(LLMClient):
    def __init__(
        self,
        model: str = "gpt-4o-mini",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
        **kwargs,
    ):
        self.model = model
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.base_url = base_url or os.getenv("OPENAI_BASE_URL")

        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
        )

    def complete(
        self,
        prompt: str,
        params: Dict[str, Any],
        system_prompt: Optional[str] = None,
    ) -> LLMResponse:
        completion_params = {
            k: v for k, v in params.items()
            if k not in ("model", "provider")
        }

        messages: list[Any] = []
        if system_prompt and system_prompt.strip():
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            **completion_params,
        )

        content = response.choices[0].message.content or ""
        usage = response.usage
        return LLMResponse(
            content=content,
            prompt_tokens=usage.prompt_tokens if usage else 0,
            completion_tokens=usage.completion_tokens if usage else 0,
            model=self.model,
        )