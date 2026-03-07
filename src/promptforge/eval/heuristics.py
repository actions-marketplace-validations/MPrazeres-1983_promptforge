"""Heuristic evaluators — deterministic, zero API cost."""

from __future__ import annotations

import json
from typing import Any, Callable


EvalFn = Callable[..., tuple[float, str]]


def check_json_validity(
    output_raw: str,
    output_parsed: dict | None,
    expected: dict,
    config: dict,
    prompt_spec: Any,
) -> tuple[float, str]:
    if output_parsed is not None:
        return 1.0, "Valid JSON."
    try:
        json.loads(output_raw.strip())
        return 1.0, "Valid JSON (raw parse)."
    except (json.JSONDecodeError, ValueError):
        return 0.0, "Output is not valid JSON."


def check_schema_match(
    output_raw: str,
    output_parsed: dict | None,
    expected: dict,
    config: dict,
    prompt_spec: Any,
) -> tuple[float, str]:
    if output_parsed is None:
        return 0.0, "Cannot check schema: output is not valid JSON."
    required_keys = list(prompt_spec.output.schema_.keys())
    if not required_keys:
        return 1.0, "No schema defined; skipping."
    missing = [k for k in required_keys if k not in output_parsed]
    if missing:
        return 0.0, f"Missing keys: {missing}"
    return 1.0, "All required keys present."


def check_length_ok(
    output_raw: str,
    output_parsed: dict | None,
    expected: dict,
    config: dict,
    prompt_spec: Any,
) -> tuple[float, str]:
    max_chars = config.get("max_chars", 500)
    length = len(output_raw)
    if length <= max_chars:
        return 1.0, f"Length {length} within limit {max_chars}."
    return 0.0, f"Length {length} exceeds limit {max_chars}."


def check_keyword_match(
    output_raw: str,
    output_parsed: dict | None,
    expected: dict,
    config: dict,
    prompt_spec: Any,
) -> tuple[float, str]:
    keywords = config.get("keywords", [])
    if not keywords:
        return 1.0, "No keywords configured."
    found = [kw for kw in keywords if kw.lower() in output_raw.lower()]
    score = len(found) / len(keywords)
    return score, f"Found {len(found)}/{len(keywords)} keywords: {found}"


def check_field_match(
    output_raw: str,
    output_parsed: dict | None,
    expected: dict,
    config: dict,
    prompt_spec: Any,
) -> tuple[float, str]:
    field = config.get("field")
    if not field:
        return 0.0, "No field configured for field_match."
    if output_parsed is None:
        return 0.0, "Output is not valid JSON."
    if field not in expected:
        return 1.0, f"Field '{field}' not in expected; skipping."
    actual = str(output_parsed.get(field, "")).strip().lower()
    exp = str(expected[field]).strip().lower()
    if actual == exp:
        return 1.0, f"Field '{field}': '{actual}' matches expected."
    return 0.0, f"Field '{field}': got '{actual}', expected '{exp}'."


def check_exact_match(
    output_raw: str,
    output_parsed: dict | None,
    expected: dict,
    config: dict,
    prompt_spec: Any,
) -> tuple[float, str]:
    expected_text = expected.get("text", "")
    if not expected_text:
        return 1.0, "No expected text; skipping."
    if output_raw.strip() == expected_text.strip():
        return 1.0, "Exact match."
    return 0.0, "Output does not match expected text."


# FIX #8: o registry agora aceita nomes prefixados do tipo "field_match_*"
# para permitir múltiplos evaluadores field_match com nomes únicos rastreáveis na DB.
# A função de lookup normaliza o nome antes de procurar no registry.

def _resolve_heuristic(name: str) -> EvalFn | None:
    """Resolve um nome de evaluador, suportando prefixos como field_match_category."""
    if name in HEURISTIC_REGISTRY:
        return HEURISTIC_REGISTRY[name]
    # Suporta nomes do tipo "field_match_category", "field_match_sentiment", etc.
    if name.startswith("field_match_"):
        return HEURISTIC_REGISTRY.get("field_match")
    return None


HEURISTIC_REGISTRY: dict[str, EvalFn] = {
    "json_validity": check_json_validity,
    "schema_match": check_schema_match,
    "length_ok": check_length_ok,
    "keyword_match": check_keyword_match,
    "field_match": check_field_match,
    "exact_match": check_exact_match,
}
