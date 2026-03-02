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
Return ONLY a JSON object with dimension names as keys and integer scores as values.
Do not add explanation outside the JSON."""


def judge_output(
    output: str,
    input_context: str,
    rubric: Rubric,
) -> dict[str, Any]:
    """Score an output using LLM-as-judge with a rubric.
    
    Returns dict of {dimension_name: {"score": int, "rationale": str}}
    """
    api_key = os.getenv("OPENAI_API_KEY")
    client = OpenAI(api_key=api_key)

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

Return JSON: {{"dimension_name": score, ...}}"""

    response = client.chat.completions.create(
        model=rubric.judge_model,
        messages=[
            {"role": "system", "content": JUDGE_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.0,
        max_tokens=256,
    )

    raw = response.choices[0].message.content or "{}"
    try:
        scores = json.loads(raw.strip())
    except json.JSONDecodeError:
        scores = {}

    return scores