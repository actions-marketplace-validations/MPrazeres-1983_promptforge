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

| Case | Customer Message                                    | Expected   | Got    | Status |
| ---- | --------------------------------------------------- | ---------- | ------ | ------ |
| t004 | "Can't login since yesterday, password is correct." | `critical` | `high` | ❌     |
| t005 | "My subscription was cancelled without warning."    | `critical` | `high` | ❌     |

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

| Concept        | What it is                                                                                          |
| -------------- | --------------------------------------------------------------------------------------------------- |
| **PromptSpec** | A YAML file defining your prompt template, system prompt, inputs, output contract, and model params |
| **Dataset**    | A golden set of `{input, expected}` cases — real examples with known correct answers                |
| **Run**        | One execution of a PromptSpec against a Dataset — produces scores per case                          |
| **Evaluator**  | A function that scores each output (heuristic or LLM-as-judge)                                      |
| **Diff**       | A comparison between two Runs showing regressions and improvements                                  |
| **Report**     | A Markdown report with ASCII charts, failure analysis, and automated insights                       |

---

## Quickstart

```bash
# Install
pip install promptforge-llmops

# Set your API key (OpenAI, Anthropic, or any OpenAI-compatible provider like Groq)
# .env file:
# OPENAI_API_KEY=your-key-here
# OPENAI_BASE_URL=https://api.groq.com/openai/v1  ← optional, for Groq (free tier available)

# Scaffold a new prompt interactively
promptforge new

# Or initialise a project manually
promptforge init

# Validate your files
promptforge validate \
  --prompt prompts/my_prompt.yaml \
  --dataset datasets/my_golden.yaml

# Run evaluation
promptforge eval \
  --prompt prompts/my_prompt.yaml \
  --dataset datasets/my_golden.yaml \
  --config configs/my_config.yaml

# Compare two runs (detect regressions)
promptforge diff --baseline <run_id_A> --candidate <run_id_B>

# View score evolution across versions
promptforge history --prompt my_prompt

# Generate Markdown report
promptforge report --run <run_id> --out report.md

# View recent runs
promptforge runs
```

---

## `promptforge new` — Interactive Wizard

The fastest way to get started. One command creates all three files you need:

```
$ promptforge new

🔨 PromptForge — New Prompt Wizard

  Prompt name: support_triage
  Description: Classifies customer support tickets
  Provider [openai]: openai
  Model [llama-3.3-70b-versatile]:
  Output format (text/json) [json]: json
  Version [0.1.0]:

  ✓ Created prompts/support_triage.yaml
  ✓ Created datasets/support_triage_golden.yaml
  ✓ Created configs/support_triage.yaml

Next step:
  promptforge eval \
    --prompt prompts/support_triage.yaml \
    --dataset datasets/support_triage_golden.yaml \
    --config configs/support_triage.yaml
```

---

## System Prompt Support

Define a `system_prompt` separately from your user template — the way modern models work best:

```yaml
id: support_triage
version: 1.2.0
system_prompt: "You are a precise support triage agent. Always respond with valid JSON only."
template: |
  Classify the following message: {{ message }}
```

PromptForge sends them as separate messages to the API. Changes to either the system prompt or the template are tracked in the content hash — so a diff will catch regressions even if only the system prompt changed.

---

## LLM-as-Judge Evaluators

Beyond heuristics, PromptForge supports **LLM-as-judge** evaluation using rubrics. Define a rubric YAML:

```yaml
# rubrics/support_quality.yaml
rubric_id: support_quality
judge_model: llama-3.3-70b-versatile
dimensions:
  - name: clarity
    scale: [1, 2, 3, 4, 5]
    instruction: "Is the reason field clear and easy to understand for a support agent?"
  - name: accuracy
    scale: [1, 2, 3, 4, 5]
    instruction: "Does the classification correctly reflect the customer's problem?"
  - name: completeness
    scale: [1, 2, 3, 4, 5]
    instruction: "Does the response include all required fields with meaningful values?"
```

Add it to your config:

```yaml
evaluators:
  - type: heuristic
    name: json_validity
  - type: judge
    name: quality
    config:
      rubric: rubrics/support_quality.yaml
```

Each dimension generates a separate normalised score (0.0–1.0) in the run summary:

```
Evaluator             | Mean Score | Failure Rate | Cases
json_validity         |      1.000 |         0.0% |     8   ✅
field_match_urgency   |      1.000 |         0.0% |     8   ✅
quality_clarity       |      1.000 |         0.0% |     8   ✅
quality_accuracy      |      1.000 |         0.0% |     8   ✅
quality_completeness  |      1.000 |         0.0% |     8   ✅
```

---

## Score History

Track how your prompt evolves over time:

```
$ promptforge history --prompt support_triage

📈 Evolution — support_triage
┏━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┓
┃ Version ┃ Date       ┃ fm_urgency ┃ fm_cat...  ┃ Trend         ┃
┡━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━━━┩
│ v1.0.0  │ 2026-03-07 │ 0.75 ████░ │ 1.00 █████ │ —             │
│ v1.1.0  │ 2026-03-07 │ 1.00 █████ │ 1.00 █████ │ ↑ 1 improved  │
│ v1.2.0  │ 2026-03-08 │ 1.00 █████ │ 1.00 █████ │ ↑ 3 improved  │
└─────────┴────────────┴────────────┴────────────┴───────────────┘
```

---

## Use as a Library

PromptForge can also be used directly in Python — no CLI required:

```python
from dotenv import load_dotenv
load_dotenv()

from promptforge import PromptSpec, Dataset, RunConfig, EvalPipeline
from promptforge.store.db import init_db
from promptforge.store.repositories import ScoreRepository
from promptforge.eval.aggregations import aggregate_run_scores

init_db()

ps = PromptSpec.from_yaml("prompts/support_triage.yaml")
ds = Dataset.from_file("datasets/support_golden.yaml")
rc = RunConfig.from_yaml("configs/support_triage.yaml")

pipeline = EvalPipeline(ps, ds, rc)
run_id = pipeline.run()

scores = ScoreRepository().get_by_run(run_id)
agg = aggregate_run_scores(scores)

all_pass = all(s["mean"] >= 0.9 for s in agg.values())
if all_pass:
    print("✅ Prompt approved — safe to promote to production.")
else:
    print("❌ Prompt failed — review failures before promoting.")
```

This makes it easy to integrate PromptForge into CI/CD pipelines, APIs, or monitoring systems.

---

## The Workflow That Changes Everything

```
1. You have a prompt that works
   → promptforge new (2 min to scaffold everything)

2. Define 10–20 real input/expected cases
   → golden dataset YAML (done once, reused forever)

3. Run: promptforge eval
   → get scores per case, mean score, failure rate

4. Change the prompt → run eval again
   → promptforge diff shows exactly what improved and what regressed

5. promptforge history --prompt <name>
   → see the full evolution of your prompt over time

6. promptforge report
   → Markdown report with ASCII charts to share with your team
```

---

## Supported Evaluators

| Evaluator       | Type         | What it checks                              |
| --------------- | ------------ | ------------------------------------------- |
| `json_validity` | heuristic    | Output is valid JSON                        |
| `schema_match`  | heuristic    | All required fields are present             |
| `field_match`   | heuristic    | A specific field matches the expected value |
| `keyword_match` | heuristic    | Required keywords appear in output          |
| `length_ok`     | heuristic    | Output is within character limit            |
| `exact_match`   | heuristic    | Output matches expected text exactly        |
| `judge`         | LLM-as-judge | Semantic quality scored by a rubric         |

---

## Supported Providers

| Provider                              | Config                                                                |
| ------------------------------------- | --------------------------------------------------------------------- |
| OpenAI (GPT-4o, GPT-4o-mini)          | `provider: openai`                                                    |
| Anthropic (Claude 3, Claude 3.5)      | `provider: anthropic`                                                 |
| Groq (Llama, Mixtral) — **free tier** | `provider: openai` + `OPENAI_BASE_URL=https://api.groq.com/openai/v1` |
| Any OpenAI-compatible API             | `provider: openai` + custom `OPENAI_BASE_URL`                         |

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
rubrics/      # Your LLM-as-judge rubric YAML files
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

## Changelog

### v0.2.0

- LLM-as-judge evaluators with rubric YAML support
- `promptforge new` — interactive wizard to scaffold prompts, datasets and configs
- `promptforge history` — visual score evolution across prompt versions
- System prompt support (`system_prompt` field in PromptSpec)
- Automatic markdown code block stripping in JSON outputs

### v0.1.0

- Core eval pipeline with heuristic evaluators
- `promptforge eval`, `diff`, `report`, `runs`, `dashboard`, `validate`
- SQLite persistence for runs and scores
- OpenAI and Anthropic provider adapters

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
