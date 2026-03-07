# PromptForge 🔨

> I changed a prompt in production. The urgency classifier dropped from 100% to 75%. Nobody noticed for two weeks. That's the problem PromptForge solves.

**PromptForge** is a minimalist, open-source LLMOps framework for prompt versioning, evaluation, and regression testing. Built by someone who wrote [a book on prompt engineering](https://github.com/marioPrazeres/prompt-engineering-book) — and got tired of "vibes-based" quality control.

---

## The Problem

You change a prompt. You run it manually on 3 examples. It "feels better". You ship it.

Two days later, a category of inputs silently degrades. You have no baseline, no metrics, no diff. You have a hunch.

**PromptForge treats prompts like code**: versioned, tested, diffed, and auditable.

---

## Real Example — Support Ticket Triage

Here's a real scenario: an AI system that classifies customer support tickets by **category**, **urgency**, and **responsible team**.

### The prompt was "working". But was it really?

We ran PromptForge against 8 real support cases and discovered:

```
Evaluator             | Mean Score | Failure Rate | Cases
json_validity         |      1.000 |         0.0% |     8   ✅
schema_match          |      1.000 |         0.0% |     8   ✅
field_match_category  |      1.000 |         0.0% |     8   ✅
field_match_urgency   |      0.750 |        25.0% |     8   ⚠️  ← problem found
field_match_team      |      1.000 |         0.0% |     8   ✅
```

**PromptForge pinpointed the exact failures:**

| Case | Customer Message | Expected | Got | Status |
|------|-----------------|----------|-----|--------|
| t004 | "Can't login since yesterday, password is correct." | `critical` | `high` | ❌ |
| t005 | "My subscription was cancelled without warning." | `critical` | `high` | ❌ |

**Root cause:** The prompt had no definition of what `critical` means for this company. The model couldn't distinguish `high` from `critical`.

### The fix: explicit urgency definitions (v1.1.0)

We added a definitions block to the prompt:

```
- "critical": user completely blocked OR data loss OR account access lost OR active incorrect charge
- "high": important feature broken but workaround exists OR charge resolved but no refund yet
- "medium": performance degradation or delays affecting work
- "low": feature requests, questions, suggestions
```

### The result — proved with data, not gut feeling:

```
promptforge diff --baseline <v1.0.0-run> --candidate <v1.1.0-run>

Evaluator             | Baseline | Candidate | Delta  | Status
field_match_category  |    1.000 |     1.000 | +0.000 | — unchanged
field_match_team      |    1.000 |     1.000 | +0.000 | — unchanged
field_match_urgency   |    0.750 |     1.000 | +0.250 | ✅ IMPROVED
json_validity         |    1.000 |     1.000 | +0.000 | — unchanged
schema_match          |    1.000 |     1.000 | +0.000 | — unchanged

✓ No regressions detected.
```

**+25% improvement on urgency. Zero regressions. Proven.**

This is what you normally don't have. Without PromptForge, you change a prompt, test on 2 examples, and ship hoping for the best. With PromptForge, you have written, reproducible proof.

---

## Core Concepts

| Concept | What it is |
|---------|-----------|
| **PromptSpec** | A YAML file defining your prompt template, inputs, output contract, and model params |
| **Dataset** | A golden set of `{input, expected}` cases — real examples with known correct answers |
| **Run** | One execution of a PromptSpec against a Dataset — produces scores per case |
| **Evaluator** | A function that scores each output (heuristic or LLM-as-judge) |
| **Diff** | A comparison between two Runs showing regressions and improvements |
| **Report** | A Markdown report with ASCII charts, failure analysis, and automated insights |

---

## Quickstart

```bash
# Install
pip install -e .

# Set your API key (OpenAI, Anthropic, or any OpenAI-compatible provider like Groq)
# .env file:
# OPENAI_API_KEY=your-key-here
# OPENAI_BASE_URL=https://api.groq.com/openai/v1  ← optional, for Groq (free tier)

# Initialise project
promptforge init

# Validate your files
promptforge validate \
  --prompt examples/quickstart/prompts/summarizer.yaml \
  --dataset examples/quickstart/datasets/summarizer_golden.yaml

# Run evaluation
promptforge eval \
  --prompt examples/quickstart/prompts/summarizer.yaml \
  --dataset examples/quickstart/datasets/summarizer_golden.yaml \
  --config examples/quickstart/configs/openai_gpt4o-mini.yaml

# Compare two runs (detect regressions)
promptforge diff --baseline <run_id_A> --candidate <run_id_B>

# Generate Markdown report
promptforge report --run <run_id> --out report.md

# View recent runs
promptforge runs
```

---

## The Workflow That Changes Everything

```
1. You have a prompt that works
   → create a PromptSpec YAML (2 min)

2. Define 10–20 real input/expected cases
   → golden dataset YAML (done once, reused forever)

3. Run: promptforge eval
   → get scores per case, mean score, failure rate

4. Change the prompt → run eval again
   → promptforge diff shows exactly what improved and what regressed

5. promptforge report
   → Markdown report with ASCII charts to share with your team
```

---

## Supported Evaluators

| Evaluator | Type | What it checks |
|-----------|------|----------------|
| `json_validity` | heuristic | Output is valid JSON |
| `schema_match` | heuristic | All required fields are present |
| `field_match` | heuristic | A specific field matches the expected value |
| `keyword_match` | heuristic | Required keywords appear in output |
| `length_ok` | heuristic | Output is within character limit |
| `exact_match` | heuristic | Output matches expected text exactly |

---

## Supported Providers

| Provider | Config |
|----------|--------|
| OpenAI (GPT-4o, GPT-4o-mini) | `provider: openai` |
| Anthropic (Claude 3, Claude 3.5) | `provider: anthropic` |
| Groq (Llama, Mixtral) — **free tier** | `provider: openai` + `OPENAI_BASE_URL=https://api.groq.com/openai/v1` |
| Any OpenAI-compatible API | `provider: openai` + custom `OPENAI_BASE_URL` |

---

## Project Structure

```
src/promptforge/
  core/       # PromptSpec, Dataset, RunConfig, Templating
  llm/        # Provider adapters (OpenAI, Anthropic)
  eval/       # Heuristics, LLM-as-judge, Regression
  store/      # SQLite persistence
  reporting/  # Markdown reports, CLI tables
  utils/      # Hashing, redaction, JSONL helpers

prompts/      # Your PromptSpec YAML files
datasets/     # Your golden datasets
configs/      # Your RunConfig YAML files
.promptforge/ # SQLite database (auto-created)
```

---

## Design Philosophy

- **Prompts are artefacts, not strings.** Version them. Hash them. Diff them.
- **Quality is measured, not felt.** Every run produces scores. Every change produces a delta.
- **LLM-as-judge is a measuring instrument, not truth.** Use it with rubrics, not blind trust.
- **Minimal dependencies. Maximum auditability.**
- **Works with free-tier providers.** No excuses not to test.

---

## Docs

- [Architecture](docs/architecture.md)
- [PromptSpec Reference](docs/prompt_spec.md)
- [Dataset Format](docs/evaluation.md)
- [CLI Reference](docs/cli.md)
- [Roadmap](docs/roadmap.md)

---

## License

MIT © Mário Prazeres