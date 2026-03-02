"""Best-effort PII redaction for judge rationales and stored outputs."""

from __future__ import annotations

import re

# Patterns: email, phone (international), simple name-like patterns
_PATTERNS = [
    (re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"), "[EMAIL]"),
    (re.compile(r"\+?[\d\s\-().]{7,15}\d"), "[PHONE]"),
    (re.compile(r"\b[A-Z][a-z]+ [A-Z][a-z]+\b"), "[NAME]"),
    (re.compile(r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b"), "[CARD]"),
    (re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), "[SSN]"),
]


def redact(text: str) -> str:
    """Apply regex-based PII redaction to a string.

    This is a best-effort measure. Do not rely on this as the sole
    PII control in production deployments.
    """
    for pattern, replacement in _PATTERNS:
        text = pattern.sub(replacement, text)
    return text