"""Timing utilities."""

from __future__ import annotations

import time
from contextlib import contextmanager
from dataclasses import dataclass


@dataclass
class Timer:
    elapsed_ms: float = 0.0


@contextmanager
def measure():
    """Context manager that measures elapsed time in milliseconds."""
    t = Timer()
    start = time.perf_counter()
    try:
        yield t
    finally:
        t.elapsed_ms = (time.perf_counter() - start) * 1000