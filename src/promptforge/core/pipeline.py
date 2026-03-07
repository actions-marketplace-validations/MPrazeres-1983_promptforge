"""EvalPipeline: orchestrates a full evaluation run."""

from __future__ import annotations

import json
import time
import uuid
from typing import Any

from rich.console import Console
from rich.progress import track

from promptforge.core.prompt_spec import PromptSpec
from promptforge.core.dataset import Dataset, TestCase
from promptforge.core.run_config import RunConfig
from promptforge.core.templating import render_template
from promptforge.llm.client_base import LLMResponse
from promptforge.eval.heuristics import _resolve_heuristic
from promptforge.store.repositories import RunRepository, CaseResultRepository, ScoreRepository


def _build_llm_client(config: RunConfig):
    if config.provider == "openai":
        from promptforge.llm.openai_client import OpenAIClient
        return OpenAIClient(model=config.model, params=config.params)
    elif config.provider == "anthropic":
        from promptforge.llm.anthropic_client import AnthropicClient
        return AnthropicClient(model=config.model, params=config.params)
    else:
        raise ValueError(f"Unknown provider: {config.provider}")


class EvalPipeline:
    def __init__(
        self,
        prompt_spec: PromptSpec,
        dataset: Dataset,
        run_config: RunConfig,
        console: Console | None = None,
    ) -> None:
        self.ps = prompt_spec
        self.ds = dataset
        self.rc = run_config
        self.console = console or Console()
        self.run_repo = RunRepository()
        self.case_repo = CaseResultRepository()
        self.score_repo = ScoreRepository()

    def run(self) -> str:
        run_id = str(uuid.uuid4())

        self.run_repo.create_run(
            run_id=run_id,
            prompt_id=self.ps.id,
            prompt_version=self.ps.version,
            prompt_hash=self.ps.content_hash,
            dataset_id=self.ds.dataset_id,
            dataset_hash=self.ds.content_hash,
            model=self.rc.model,
            provider=self.rc.provider,
            params=self.rc.params,
        )

        client = _build_llm_client(self.rc)
        total_tokens = 0

        for case in track(self.ds.cases, description="Evaluating...", console=self.console):
            rendered = render_template(self.ps.template, case.input)
            t0 = time.time()
            response: LLMResponse = client.complete(rendered, self.rc.params)
            latency_ms = (time.time() - t0) * 1000
            total_tokens += response.total_tokens

            parsed = self._try_parse_json(response.content)

            self.case_repo.save(
                run_id=run_id,
                case_id=case.id,
                input_json=json.dumps(case.input),
                output_raw=response.content,
                output_parsed_json=json.dumps(parsed) if parsed else None,
                latency_ms=latency_ms,
                tokens_in=response.prompt_tokens,
                tokens_out=response.completion_tokens,
            )

            scores = self._evaluate(case, response.content, parsed)
            for evaluator_name, score, rationale in scores:
                self.score_repo.save(
                    run_id=run_id,
                    case_id=case.id,
                    evaluator=evaluator_name,
                    dimension=evaluator_name,
                    score=score,
                    rationale=rationale,
                )

        self.run_repo.finish_run(run_id, total_tokens=total_tokens)
        return run_id

    def _try_parse_json(self, text: str) -> dict | None:
        try:
            return json.loads(text.strip())
        except (json.JSONDecodeError, ValueError):
            return None

    def _evaluate(
        self,
        case: TestCase,
        output_raw: str,
        output_parsed: dict | None,
    ) -> list[tuple[str, float, str]]:
        results = []
        for ev_conf in self.rc.evaluators:
            if ev_conf.type == "heuristic":
                fn = _resolve_heuristic(ev_conf.name)  # suporta field_match_category, etc.
                if fn is None:
                    self.console.print(
                        f"[yellow]⚠ Unknown heuristic evaluator: '{ev_conf.name}'. Skipping.[/yellow]"
                    )
                    continue
                score, rationale = fn(
                    output_raw=output_raw,
                    output_parsed=output_parsed,
                    expected=case.expected,
                    config=ev_conf.config,
                    prompt_spec=self.ps,
                )
                results.append((ev_conf.name, score, rationale))
            elif ev_conf.type == "judge":
                self.console.print(
                    f"[yellow]⚠ LLM-as-judge evaluator '{ev_conf.name}' não está ainda "
                    f"ligado ao pipeline. Skipping.[/yellow]"
                )
            else:
                self.console.print(
                    f"[yellow]⚠ Tipo de evaluador desconhecido: '{ev_conf.type}'. Skipping.[/yellow]"
                )
        return results

    def export_json(self, run_id: str, path: str) -> None:
        from pathlib import Path
        data = {
            "run_id": run_id,
            "cases": self.case_repo.get_by_run(run_id),
            "scores": self.score_repo.get_by_run(run_id),
        }
        Path(path).write_text(json.dumps(data, indent=2), encoding="utf-8")