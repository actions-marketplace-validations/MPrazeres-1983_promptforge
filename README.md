# PromptForge 🔨

> Prompt regression testing for teams that treat prompts like production artefacts.

**PromptForge** is an open-source LLMOps framework for prompt versioning, evaluation and regression testing.

It helps you answer a simple but critical question:

> Did this prompt change actually improve the system, or did it silently break something?

PromptForge treats prompts as testable artefacts: versioned, hashed, evaluated, diffed and auditable.

---

## Why PromptForge Exists

Prompt changes are often tested manually:

1. Edit the prompt.
2. Run it on a few examples.
3. It feels better.
4. Ship it.

The problem is that prompt regressions are usually silent.

A prompt may improve one class of inputs while degrading another. Without a baseline, a golden dataset, measurable scores and a diff between versions, you are relying on intuition instead of evidence.

PromptForge brings software quality practices to prompt engineering:

- Golden datasets
- Reproducible evaluations
- Heuristic evaluators
- Regression detection
- Score history
- Markdown reports
- CI/CD integration

---

## Real Example — Support Ticket Triage

Imagine an AI system that classifies customer support tickets by:

- `category`
- `urgency`
- `responsible_team`

The prompt appears to work. But does it actually meet the expected behaviour?

Running PromptForge against 8 support cases produced this result:

```text
Evaluator             | Mean Score | Failure Rate | Cases
json_validity         |      1.000 |         0.0% |     8   ✅
schema_match          |      1.000 |         0.0% |     8   ✅
field_match_category  |      1.000 |         0.0% |     8   ✅
field_match_urgency   |      0.750 |        25.0% |     8   ⚠️
field_match_team      |      1.000 |         0.0% |     8   ✅
```

PromptForge identified the exact failures:

| Case | Customer Message                                    | Expected   | Got    | Status |
| ---- | --------------------------------------------------- | ---------- | ------ | ------ |
| t004 | "Can't login since yesterday, password is correct." | `critical` | `high` | ❌     |
| t005 | "My subscription was cancelled without warning."    | `critical` | `high` | ❌     |

The issue was not the model. The prompt had no clear definition of what `critical` meant for that business context.

### Prompt v1.1.0

The prompt was updated with explicit urgency definitions:

```text
- critical: user completely blocked OR data loss OR account access lost OR active incorrect charge
- high: important feature broken but workaround exists OR charge resolved but no refund yet
- medium: performance degradation or delays affecting work
- low: feature requests, questions, suggestions
```

Then PromptForge compared the baseline run with the candidate run:

```bash
promptforge diff --baseline <v1.0.0-run> --candidate <v1.1.0-run>
```

```text
Evaluator             | Baseline | Candidate | Delta  | Status
field_match_category  |    1.000 |     1.000 | +0.000 | — unchanged
field_match_team      |    1.000 |     1.000 | +0.000 | — unchanged
field_match_urgency   |    0.750 |     1.000 | +0.250 | ✅ improved
json_validity         |    1.000 |     1.000 | +0.000 | — unchanged
schema_match          |    1.000 |     1.000 | +0.000 | — unchanged

✓ No regressions detected.
```

Result:

```text
+25% improvement on urgency classification.
Zero regressions detected.
```

This is the core value of PromptForge: prompt changes become measurable, reviewable and reproducible.

---

## Core Concepts

| Concept        | Description                                                                                         |
| -------------- | --------------------------------------------------------------------------------------------------- |
| **PromptSpec** | YAML file defining the prompt template, system prompt, inputs, output contract and model parameters |
| **Dataset**    | Golden set of input/expected examples used as the evaluation baseline                               |
| **Run**        | Execution of a PromptSpec against a Dataset                                                         |
| **Evaluator**  | Function that scores each output                                                                    |
| **Diff**       | Comparison between two runs, showing regressions and improvements                                   |
| **Report**     | Markdown report with scores, failure analysis and evaluation summary                                |

---

## Installation

Install the package from PyPI:

```bash
pip install promptforge-llmops
```

The installed CLI command is:

```bash
promptforge
```

---

## Quickstart with Groq

PromptForge currently works with Groq through its OpenAI-compatible API.

Create a `.env` file:

```bash
GROQ_API_KEY=your-groq-api-key
OPENAI_API_KEY=${GROQ_API_KEY}
OPENAI_BASE_URL=https://api.groq.com/openai/v1
```

Alternatively, export the variables directly in your shell:

```bash
export GROQ_API_KEY="your-groq-api-key"
export OPENAI_API_KEY="$GROQ_API_KEY"
export OPENAI_BASE_URL="https://api.groq.com/openai/v1"
```

Create a new prompt evaluation project:

```bash
promptforge new
```

Or initialise a project manually:

```bash
promptforge init
```

Validate your prompt, dataset and config:

```bash
promptforge validate \
  --prompt prompts/my_prompt.yaml \
  --dataset datasets/my_golden.yaml
```

Run an evaluation:

```bash
promptforge eval \
  --prompt prompts/my_prompt.yaml \
  --dataset datasets/my_golden.yaml \
  --config configs/my_config.yaml
```

Compare two runs:

```bash
promptforge diff --baseline <run_id_A> --candidate <run_id_B>
```

View score history:

```bash
promptforge history --prompt my_prompt
```

Generate a Markdown report:

```bash
promptforge report --run <run_id> --out report.md
```

List recent runs:

```bash
promptforge runs
```

---

## Interactive Wizard

The fastest way to start is:

```bash
promptforge new
```

Example:

```text
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
```

Next step:

```bash
promptforge eval \
  --prompt prompts/support_triage.yaml \
  --dataset datasets/support_triage_golden.yaml \
  --config configs/support_triage.yaml
```

---

## PromptSpec Example

PromptForge supports separate `system_prompt` and user `template` fields.

```yaml
id: support_triage
version: 1.2.0

system_prompt: |
  You are a precise support triage agent.
  Always respond with valid JSON only.

template: |
  Classify the following customer message:

  {{ message }}

output_format: json

model:
  provider: openai
  name: llama-3.3-70b-versatile
  temperature: 0
```

Changes to either the `system_prompt` or the `template` are tracked in the prompt hash, so regressions can be detected even when only part of the prompt changes.

---

## Score History

Track how a prompt evolves over time:

```bash
promptforge history --prompt support_triage
```

Example:

```text
📈 Evolution — support_triage
┏━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┓
┃ Version ┃ Date       ┃ fm_urgency ┃ fm_category┃ Trend         ┃
┡━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━━━┩
│ v1.0.0  │ 2026-03-07 │ 0.75 ████░ │ 1.00 █████ │ —             │
│ v1.1.0  │ 2026-03-07 │ 1.00 █████ │ 1.00 █████ │ ↑ 1 improved  │
│ v1.2.0  │ 2026-03-08 │ 1.00 █████ │ 1.00 █████ │ ↑ 3 improved  │
└─────────┴────────────┴────────────┴────────────┴───────────────┘
```

---

## Use as a Python Library

PromptForge can also be used directly in Python:

```python
from dotenv import load_dotenv

from promptforge import PromptSpec, Dataset, RunConfig, EvalPipeline
from promptforge.store.db import init_db
from promptforge.store.repositories import ScoreRepository
from promptforge.eval.aggregations import aggregate_run_scores

load_dotenv()
init_db()

prompt_spec = PromptSpec.from_yaml("prompts/support_triage.yaml")
dataset = Dataset.from_file("datasets/support_golden.yaml")
run_config = RunConfig.from_yaml("configs/support_triage.yaml")

pipeline = EvalPipeline(prompt_spec, dataset, run_config)
run_id = pipeline.run()

scores = ScoreRepository().get_by_run(run_id)
summary = aggregate_run_scores(scores)

all_pass = all(metric["mean"] >= 0.9 for metric in summary.values())

if all_pass:
    print("Prompt approved.")
else:
    print("Prompt failed. Review failures before promotion.")
```

This makes PromptForge usable inside CI/CD pipelines, APIs, internal tools or monitoring workflows.

---

## Typical Workflow

```text
1. Create or update a prompt
   → promptforge new

2. Define a golden dataset
   → real input/expected examples

3. Run evaluation
   → promptforge eval

4. Change the prompt
   → run evaluation again

5. Compare versions
   → promptforge diff

6. Track evolution
   → promptforge history

7. Share results
   → promptforge report
```

---

## Supported Evaluators

| Evaluator       | Type      | What it checks                              |
| --------------- | --------- | ------------------------------------------- |
| `json_validity` | heuristic | Output is valid JSON                        |
| `schema_match`  | heuristic | Required fields are present                 |
| `field_match`   | heuristic | A specific field matches the expected value |
| `keyword_match` | heuristic | Required keywords appear in the output      |
| `length_ok`     | heuristic | Output stays within a character limit       |
| `exact_match`   | heuristic | Output matches the expected text exactly    |

---

## Supported Provider Setup

PromptForge currently uses an OpenAI-compatible provider interface.

| Provider                  | Configuration                                 |
| ------------------------- | --------------------------------------------- |
| Groq                      | `provider: openai` + Groq `OPENAI_BASE_URL`   |
| OpenAI-compatible APIs    | `provider: openai` + custom `OPENAI_BASE_URL` |

For Groq, use:

```bash
OPENAI_BASE_URL=https://api.groq.com/openai/v1
```

And configure your prompt with:

```yaml
model:
  provider: openai
  name: llama-3.3-70b-versatile
  temperature: 0
```

---

## Project Structure

```text
src/promptforge/
  core/        # PromptSpec, Dataset, RunConfig, templating
  llm/         # Provider adapter layer
  eval/        # Heuristics and regression logic
  store/       # SQLite persistence
  reporting/   # Markdown reports and CLI tables
  utils/       # Hashing, redaction, JSONL helpers

prompts/       # PromptSpec YAML files
datasets/      # Golden datasets
configs/       # RunConfig YAML files
.promptforge/  # SQLite database, auto-created
```

---

## CI/CD Integration

PromptForge is available as a GitHub Action.

```yaml
name: Prompt Eval

on:
  push:
    paths:
      - "prompts/**"
      - "datasets/**"
      - "configs/**"

jobs:
  eval:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Run PromptForge eval
        uses: MPrazeres-1983/promptforge@v1
        with:
          prompt: prompts/support_triage.yaml
          dataset: datasets/support_golden.yaml
          config: configs/support_triage.yaml
          openai-api-key: ${{ secrets.OPENAI_API_KEY }}
          openai-base-url: ${{ secrets.OPENAI_BASE_URL }}
          fail-on-regression: "true"
```

The action installs `promptforge-llmops`, runs the evaluation and can fail the workflow when regressions are detected.

Available on GitHub Marketplace:

```text
https://github.com/marketplace/actions/promptforge-eval
```

### Action Inputs

| Input                | Required | Description                                           |
| -------------------- | -------- | ----------------------------------------------------- |
| `prompt`             | yes      | Path to PromptSpec YAML                               |
| `dataset`            | yes      | Path to Dataset YAML or JSONL                         |
| `config`             | yes      | Path to RunConfig YAML                                |
| `openai-api-key`     | yes      | API key for OpenAI or compatible provider             |
| `openai-base-url`    | no       | Base URL for OpenAI-compatible providers              |
| `baseline-run-id`    | no       | Run ID to compare against                             |
| `fail-on-regression` | no       | Fail workflow when regressions are detected           |

---

## Design Philosophy

- **Prompts are artefacts, not strings.**
- **Quality should be measured, not guessed.**
- **Prompt changes need baselines, datasets and diffs.**
- **Regression testing should be part of CI/CD.**
- **Small tools are easier to audit, understand and maintain.**

---

## Documentation

- [Architecture](docs/architecture.md)
- [PromptSpec Reference](docs/prompt_spec.md)
- [Dataset Format](docs/evaluation.md)
- [CLI Reference](docs/cli.md)
- [Roadmap](docs/roadmap.md)

---

## Changelog

### v0.2.0

- `promptforge new` interactive wizard
- `promptforge history` for score evolution
- System prompt support through `system_prompt`
- Markdown code block stripping for JSON outputs

### v0.1.0

- Core evaluation pipeline
- Heuristic evaluators
- `promptforge eval`
- `promptforge diff`
- `promptforge report`
- `promptforge runs`
- `promptforge dashboard`
- `promptforge validate`
- SQLite persistence for runs and scores
- OpenAI-compatible provider interface

---

## License

MIT © Mário Prazeres
