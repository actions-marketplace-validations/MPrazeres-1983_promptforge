# Changelog

All notable changes to PromptForge will be documented in this file.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

## [0.1.0] - 2025-01-01
### Added
- Initial project structure
- PromptSpec YAML loader and validator
- Dataset loader (YAML + JSONL)
- Heuristic evaluators: json_validity, length, keyword_match, schema_match
- LLM-as-judge evaluator with rubric support
- SQLite store with full run/score traceability
- Regression engine with configurable thresholds
- Markdown report generator
- CLI commands: eval, diff, report, dashboard, validate, init
- OpenAI and Anthropic client adapters
- GitHub Actions CI pipeline