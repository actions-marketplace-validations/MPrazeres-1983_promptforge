# Architecture

## Overview

PromptForge is structured as a layered system with clear separation of concerns:


CLI (Typer + Rich)
│
▼
Core Layer ← PromptSpec, Dataset, RunConfig, Templating
│
┌───┴────┐
▼ ▼
LLM Layer Eval Layer ← Providers | Heuristics, Judge, Regression
│ │
└───┬────┘
▼
Store Layer ← SQLite (runs, scores, prompts, datasets)
│
▼
Reporting Layer ← Markdown, CLI tables


## Module Responsibilities

### `core/`
- `prompt_spec.py`: Load, validate, and hash PromptSpec YAML files.
- `templating.py`: Jinja2-based template rendering with input injection.
- `dataset.py`: Load and validate Dataset YAML/JSONL files.
- `run_config.py`: Model, provider, and execution parameters.
- `errors.py`: Domain-specific exceptions.

### `llm/`
- `client_base.py`: Abstract interface for LLM providers.
- `openai_client.py`: OpenAI adapter (chat completions).
- `anthropic_client.py`: Anthropic adapter (messages API).

### `eval/`
- `evaluator_base.py`: Abstract evaluator interface.
- `heuristics.py`: Deterministic scorers (JSON validity, length, keywords, schema).
- `llm_judge.py`: LLM-as-judge scorer using rubrics.
- `rubrics.py`: Rubric loader and validator.
- `regression.py`: Baseline comparison and threshold enforcement.
- `aggregations.py`: Score aggregation (mean, p95, failure rate).

### `store/`
- `db.py`: SQLite connection and migration management.
- `schema.sql`: Table definitions.
- `repositories.py`: CRUD operations for all entities.

### `reporting/`
- `markdown_report.py`: Full run report in Markdown.
- `tables.py`: Rich CLI table renderers.

### `utils/`
- `hashing.py`: SHA-256 content hashing for prompts and datasets.
- `time.py`: Timing utilities.
- `jsonl.py`: JSONL read/write helpers.
- `redaction.py`: PII redaction before storing rationales.

## Data Flow (Single Eval Run)

1. CLI parses args → loads PromptSpec, Dataset, RunConfig.
2. `core/templating.py` renders each case's prompt.
3. `llm/` client sends request, returns raw output + usage metadata.
4. `eval/` evaluators score each output.
5. `store/` persists run, case results, and scores.
6. `reporting/` generates Markdown or CLI table.

## Key Design Decisions

See [design_decisions.md](design_decisions.md).