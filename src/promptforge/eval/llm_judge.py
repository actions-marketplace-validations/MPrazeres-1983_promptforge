"""LLM-as-judge evaluator."""

from __future__ import annotations

import json
import os
from typing import Any

from openai import OpenAI

from promptforge.eval.rubrics import Rubric
from promptforge.utils.redaction import redact


JUDGE_SYSTEM_PROMPT = """You are a precise evaluation judge.
You will be given an AI output and a rubric.
Score the output on each dimension.
Return ONLY a JSON object where each key is a dimension name and each value is an object with:
  - "score": integer score
  - "rationale": one sentence explaining the score
Do not add anything outside the JSON."""


def judge_output(
    output: str,
    input_context: str,
    rubric: Rubric,
) -> dict[str, Any]:
    """Score an output using LLM-as-judge with a rubric.

    Returns dict of {dimension_name: {"score": int, "rationale": str}}
    """
    # Respeita OPENAI_BASE_URL para compatibilidade com Groq e outros providers
    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_BASE_URL")
    client = OpenAI(api_key=api_key, base_url=base_url)

    dimensions_text = "\n".join(
        f"- {d.name} (scale {d.scale[0]}-{d.scale[-1]}): {d.instruction}"
        for d in rubric.dimensions
    )

    user_prompt = f"""Input context:
---
{redact(input_context[:2000])}
---

AI Output:
---
{redact(output[:2000])}
---

Rubric dimensions:
{dimensions_text}

Return JSON: {{"dimension_name": {{"score": int, "rationale": "string"}}, ...}}"""

    response = client.chat.completions.create(
        model=rubric.judge_model,
        messages=[
            {"role": "system", "content": JUDGE_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.0,
        max_tokens=512,
    )

    raw = response.choices[0].message.content or "{}"

    # Limpa markdown code blocks se o modelo os incluir
    clean = raw.strip()
    if clean.startswith("```"):
        clean = "\n".join(clean.split("\n")[1:])
    if clean.endswith("```"):
        clean = "\n".join(clean.split("\n")[:-1])

    try:
        return json.loads(clean.strip())
    except json.JSONDecodeError:
        return {}