"""Unit tests for heuristic evaluators."""

from __future__ import annotations


from promptforge.eval.heuristics import (
    check_json_validity,
    check_schema_match,
    check_field_match,
    check_length_ok,
    check_keyword_match,
)


class MockPromptSpec:
    class output:
        schema_ = {"category": {"type": "string"}, "sentiment": {"type": "string"}}


SPEC = MockPromptSpec()


# --- json_validity ---

def test_json_validity_valid():
    score, _ = check_json_validity('{"key": "val"}', {"key": "val"}, {}, {}, SPEC)
    assert score == 1.0


def test_json_validity_invalid():
    score, _ = check_json_validity("not json", None, {}, {}, SPEC)
    assert score == 0.0


# --- schema_match ---

def test_schema_match_all_keys_present():
    parsed = {"category": "billing", "sentiment": "negative"}
    score, _ = check_schema_match("", parsed, {}, {}, SPEC)
    assert score == 1.0


def test_schema_match_missing_key():
    parsed = {"category": "billing"}
    score, rationale = check_schema_match("", parsed, {}, {}, SPEC)
    assert score == 0.0
    assert "sentiment" in rationale


def test_schema_match_no_parsed():
    score, _ = check_schema_match("", None, {}, {}, SPEC)
    assert score == 0.0


# --- field_match ---

def test_field_match_correct():
    parsed = {"category": "billing"}
    expected = {"category": "billing"}
    score, _ = check_field_match("", parsed, expected, {"field": "category"}, SPEC)
    assert score == 1.0


def test_field_match_wrong():
    parsed = {"category": "bug"}
    expected = {"category": "billing"}
    score, _ = check_field_match("", parsed, expected, {"field": "category"}, SPEC)
    assert score == 0.0


def test_field_match_case_insensitive():
    parsed = {"category": "Billing"}
    expected = {"category": "billing"}
    score, _ = check_field_match("", parsed, expected, {"field": "category"}, SPEC)
    assert score == 1.0


# --- length_ok ---

def test_length_ok_within_limit():
    score, _ = check_length_ok("short text", None, {}, {"max_chars": 100}, SPEC)
    assert score == 1.0


def test_length_ok_exceeds_limit():
    score, _ = check_length_ok("x" * 200, None, {}, {"max_chars": 100}, SPEC)
    assert score == 0.0


# --- keyword_match ---

def test_keyword_match_all_found():
    score, _ = check_keyword_match(
        "billing issue detected", None, {}, {"keywords": ["billing", "issue"]}, SPEC
    )
    assert score == 1.0


def test_keyword_match_partial():
    score, _ = check_keyword_match(
        "billing only", None, {}, {"keywords": ["billing", "missing"]}, SPEC
    )
    assert score == 0.5


def test_keyword_match_none_found():
    score, _ = check_keyword_match(
        "nothing here", None, {}, {"keywords": ["billing", "bug"]}, SPEC
    )
    assert score == 0.0