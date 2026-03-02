"""CRUD repositories for all PromptForge entities."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from promptforge.store.db import get_connection


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class RunRepository:
    def create_run(
        self,
        run_id: str,
        prompt_id: str,
        prompt_version: str,
        prompt_hash: str,
        dataset_id: str,
        dataset_hash: str,
        model: str,
        provider: str,
        params: dict[str, Any],
    ) -> None:
        with get_connection() as conn:
            conn.execute(
                """INSERT INTO runs
                   (run_id, prompt_id, prompt_version, prompt_hash,
                    dataset_id, dataset_hash, model, provider,
                    params_json, started_at)
                   VALUES (?,?,?,?,?,?,?,?,?,?)""",
                (
                    run_id, prompt_id, prompt_version, prompt_hash,
                    dataset_id, dataset_hash, model, provider,
                    json.dumps(params), _now(),
                ),
            )

    def finish_run(self, run_id: str, total_tokens: int) -> None:
        with get_connection() as conn:
            conn.execute(
                """UPDATE runs
                   SET finished_at = ?, total_tokens = ?,
                       total_cases = (
                           SELECT COUNT(DISTINCT case_id)
                           FROM case_results WHERE run_id = ?
                       )
                   WHERE run_id = ?""",
                (_now(), total_tokens, run_id, run_id),
            )

    def get_run(self, run_id: str) -> dict | None:
        with get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM runs WHERE run_id = ?", (run_id,)
            ).fetchone()
            return dict(row) if row else None

    def list_runs(self, limit: int = 10) -> list[dict]:
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM runs ORDER BY started_at DESC LIMIT ?", (limit,)
            ).fetchall()
            return [dict(r) for r in rows]


class CaseResultRepository:
    def save(
        self,
        run_id: str,
        case_id: str,
        input_json: str,
        output_raw: str,
        output_parsed_json: str | None,
        latency_ms: float,
        tokens_in: int,
        tokens_out: int,
    ) -> None:
        with get_connection() as conn:
            conn.execute(
                """INSERT INTO case_results
                   (run_id, case_id, input_json, output_raw,
                    output_parsed_json, latency_ms, tokens_in, tokens_out)
                   VALUES (?,?,?,?,?,?,?,?)""",
                (
                    run_id, case_id, input_json, output_raw,
                    output_parsed_json, latency_ms, tokens_in, tokens_out,
                ),
            )

    def get_by_run(self, run_id: str) -> list[dict]:
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM case_results WHERE run_id = ?", (run_id,)
            ).fetchall()
            return [dict(r) for r in rows]


class ScoreRepository:
    def save(
        self,
        run_id: str,
        case_id: str,
        evaluator: str,
        dimension: str,
        score: float,
        rationale: str = "",
        metadata: dict | None = None,
    ) -> None:
        with get_connection() as conn:
            conn.execute(
                """INSERT INTO scores
                   (run_id, case_id, evaluator, dimension, score, rationale, metadata_json)
                   VALUES (?,?,?,?,?,?,?)""",
                (
                    run_id, case_id, evaluator, dimension, score,
                    rationale, json.dumps(metadata) if metadata else None,
                ),
            )

    def get_by_run(self, run_id: str) -> list[dict]:
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM scores WHERE run_id = ?", (run_id,)
            ).fetchall()
            return [dict(r) for r in rows]

    def get_by_run_and_evaluator(self, run_id: str, evaluator: str) -> list[dict]:
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM scores WHERE run_id = ? AND evaluator = ?",
                (run_id, evaluator),
            ).fetchall()
            return [dict(r) for r in rows]