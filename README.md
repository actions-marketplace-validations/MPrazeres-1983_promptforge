# PromptForge 🔨

> I broke a prompt in production. Nobody noticed for three days. That's the problem PromptForge solves.

**PromptForge** is a minimalist, open-source LLMOps framework for prompt versioning, evaluation, and regression testing. Built by someone who wrote [a book on prompt engineering](https://github.com/marioPrazeres/prompt-engineering-book) — and got tired of "vibes-based" quality control.

---

## The Problem

You change a prompt. You run it manually on 3 examples. It "feels better". You ship it.

Two days later, a category of inputs silently degrades. You have no baseline, no metrics, no diff. You have a hunch.

**PromptForge treats prompts like code**: versioned, tested, diffed, and auditable.

---

## Core Concepts

| Concept | What it is |
|---|---|
| **PromptSpec** | A YAML file defining your prompt template, inputs, output contract, and model params |
| **Dataset** | A golden set of `{input, expected}` cases |
| **Run** | One execution of a PromptSpec against a Dataset |
| **Evaluator** | A function that scores each output (heuristic or LLM-as-judge) |
| **Report** | A Markdown diff between two Runs showing regressions and improvements |

---

## Quickstart

```bash
# Install
pip install promptforge

# Set your API key
export OPENAI_API_KEY=sk-...

# Run evaluation
promptforge eval \
  --prompt examples/quickstart/prompts/summarizer.yaml \
  --dataset examples/quickstart/datasets/summarizer_golden.yaml \
  --config examples/quickstart/configs/openai_gpt4o-mini.yaml

# Compare two runs
promptforge diff --baseline <run_id_A> --candidate <run_id_B>

# Generate report
promptforge report --run <run_id> --out report.md

# Dashboard
promptforge dashboard --run <run_id>

Project Structure

src/promptforge/
  core/       # PromptSpec, Dataset, RunConfig, Templating
  llm/        # Provider adapters (OpenAI, Anthropic)
  eval/       # Heuristics, LLM-as-judge, Regression
  store/      # SQLite persistence
  reporting/  # Markdown reports, CLI tables
  utils/      # Hashing, redaction, JSONL helpers

Design Philosophy

    Prompts are artefacts, not strings. Version them. Hash them. Diff them.
    Quality is measured, not felt. Every run produces scores. Every change produces a delta.
    LLM-as-judge is a measuring instrument, not truth. Use it with rubrics, not blind trust.
    Minimal dependencies. Maximum auditability.

Docs

    Architecture
    PromptSpec Reference
    Dataset Format
    Evaluation
    CLI Reference
    Threat Model
    Roadmap

License

MIT © Mário Prazeres


---