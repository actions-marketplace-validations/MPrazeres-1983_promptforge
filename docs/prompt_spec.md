# PromptSpec Reference

A PromptSpec is a YAML file that defines a prompt as a versioned, typed artefact.

## Full Schema

```yaml
id: string                  # Unique identifier (snake_case)
version: string             # Semantic version (e.g. "0.3.0")
description: string         # Human-readable purpose
template: string            # Jinja2 template string
inputs:                     # Input variable definitions
  <name>:
    type: string | integer | list
    description: string     # Optional
output:
  format: text | json       # Expected output format
  schema:                   # Optional: expected JSON keys and types
    <key>: { type: string }
params:
  temperature: float        # Default: 0.0
  max_tokens: integer       # Default: 512
  top_p: float              # Optional
tags: [string]              # Optional metadata tags

Example

id: summarizer
version: 0.3.0
description: Summarize customer complaint into structured fields.
template: |
  You are a precise support analyst.

  Complaint:
  {{ text }}

  Return JSON with:
  - category (one of: billing, bug, feature, other)
  - sentiment (negative|neutral|positive)
  - summary (max 35 words)
inputs:
  text:
    type: string
    description: Raw customer complaint text
output:
  format: json
  schema:
    category: { type: string }
    sentiment: { type: string }
    summary: { type: string }
params:
  temperature: 0.0
  max_tokens: 220
tags: [support, json, structured]

Versioning

    Use semantic versioning: MAJOR.MINOR.PATCH.
    PromptForge hashes the template + params fields to detect changes even if version is not bumped.
    A version bump without a template change is valid (e.g. description update).

Template Syntax

Templates use Jinja2. All inputs keys are available as variables.

{{ variable_name }}
{% if condition %}...{% endif %}
{% for item in list %}...{% endfor %}


**`docs/datasets.md`**
```markdown
# Dataset Format

Datasets are golden sets of test cases used to evaluate a prompt.

## YAML Format

```yaml
dataset_id: string
description: string       # Optional
cases:
  - id: string            # Unique case identifier
    input:
      <key>: <value>      # Must match PromptSpec inputs
    expected:             # Optional: hard expected values
      <key>: <value>
    notes: string         # Optional: human annotation

JSONL Format

Each line is a JSON object:

{"id": "c001", "input": {"text": "..."}, "expected": {"category": "billing"}}

Expected vs Rubric Evaluation

    Expected: Hard match. Used by heuristic evaluators (e.g. category == "billing").
    Rubric: Soft scoring. Used by LLM-as-judge when exact match is not possible.

Both can coexist in the same dataset.
Best Practices

    Minimum 20 cases for meaningful regression detection.
    Cover edge cases: empty inputs, multilingual text, adversarial inputs.
    Annotate notes for cases that are known to be ambiguous.
    Never use production PII in datasets. Use synthetic or anonymised data.