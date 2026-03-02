# Roadmap

## v0.1.0 (Current)
- [x] PromptSpec YAML loader and validator
- [x] Dataset loader (YAML + JSONL)
- [x] Heuristic evaluators
- [x] LLM-as-judge with rubrics
- [x] SQLite store
- [x] Regression engine
- [x] Markdown report generator
- [x] CLI: eval, diff, report, dashboard, validate, init
- [x] OpenAI and Anthropic adapters
- [x] GitHub Actions CI

## v0.2.0 (Next)
- [ ] GitHub PR comment integration (post diff as PR comment)
- [ ] JSONL export for runs and scores
- [ ] Async batch execution for large datasets
- [ ] `promptforge watch` — re-run eval on file change

## v0.3.0
- [ ] Plugin system for custom evaluators
- [ ] LangGraph agent eval support
- [ ] HTML report with charts
- [ ] Dataset versioning and lineage

## v1.0.0
- [ ] PostgreSQL backend option
- [ ] Web dashboard (optional, lightweight)
- [ ] Multi-provider parallel eval (same prompt, different models)
- [ ] Prompt A/B testing with statistical significance