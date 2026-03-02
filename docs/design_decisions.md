# Design Decisions

## Why SQLite?

SQLite provides zero-infrastructure persistence with full SQL query capability. For a developer tool used locally or in CI, it is the right tradeoff. Migration to PostgreSQL is possible via SQLAlchemy if needed.

## Why YAML for PromptSpecs?

YAML is human-readable, diff-friendly, and supports multi-line strings cleanly (critical for prompt templates). JSON lacks multi-line readability; TOML lacks ecosystem adoption in this domain.

## Why Jinja2 for templating?

Jinja2 is the de-facto Python templating standard. It supports conditionals, loops, and filters — all useful for dynamic prompt construction. It is already a transitive dependency of many Python projects.

## Why Pydantic for validation?

Pydantic v2 provides fast, type-safe validation with clear error messages. It integrates naturally with YAML-loaded dicts and produces structured errors that the CLI can surface cleanly.

## Why Typer + Rich for CLI?

Typer provides type-annotated CLI commands with zero boilerplate. Rich provides beautiful terminal output (tables, progress bars, panels) that makes the tool feel professional.

## Regression Policy

A regression is defined as a drop in mean score for any evaluator dimension that exceeds the configured threshold (default: 0.05). The CI pipeline fails if any regression is detected. Thresholds are configurable per evaluator in RunConfig.

## Hashing Strategy

PromptSpecs and Datasets are SHA-256 hashed on their canonical content (template + params for prompts; sorted case list for datasets). This allows detecting "silent" changes where the version string was not bumped.

## LLM-as-Judge Bias Mitigation

- Judge model is configurable and separate from the evaluated model.
- Rationales are stored for human review.
- Position bias is mitigated by randomising output order when comparing two candidates.
- PII in rationales is redacted before storage.

## PII Redaction

The `utils/redaction.py` module applies regex-based redaction for common PII patterns (email, phone, names) before storing judge rationales. This is a best-effort measure; production deployments should apply additional controls.