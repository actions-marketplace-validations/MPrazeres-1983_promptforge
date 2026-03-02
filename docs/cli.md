# CLI Reference

## Commands

### `promptforge init`
Scaffold a new PromptForge project in the current directory.
```bash
promptforge init

promptforge validate

Validate PromptSpec and Dataset YAML files.

promptforge validate --prompt prompts/summarizer.yaml --dataset datasets/golden.yaml

promptforge eval

Run evaluation of a prompt against a dataset.

promptforge eval \
  --prompt prompts/summarizer.yaml \
  --dataset datasets/golden.yaml \
  --config configs/openai_gpt4o-mini.yaml

  Options:

    --prompt: Path to PromptSpec YAML
    --dataset: Path to Dataset YAML or JSONL
    --config: Path to RunConfig YAML
    --out: Optional output path for JSON results

promptforge diff

Compare two runs and show regressions/improvements.

promptforge diff --baseline <run_id> --candidate <run_id>

promptforge report

Generate a Markdown report for a run.

promptforge report --run <run_id> --out report.md

promptforge dashboard

Show a CLI dashboard for a run (top failures, scores, cost).

promptforge dashboard --run <run_id>

promptforge runs

List recent runs.

promptforge runs --limit 10

