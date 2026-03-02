# Evaluation

PromptForge supports two evaluation strategies: **heuristic** and **LLM-as-judge**.

## Heuristic Evaluators

Fast, deterministic, zero API cost.

| Evaluator | Score | Description |
|---|---|---|
| `json_validity` | 0.0 / 1.0 | Output is valid JSON |
| `schema_match` | 0.0 / 1.0 | JSON contains all required keys |
| `length_ok` | 0.0 / 1.0 | Output length within configured bounds |
| `keyword_match` | 0.0 – 1.0 | Fraction of required keywords present |
| `exact_match` | 0.0 / 1.0 | Output matches expected exactly |
| `field_match` | 0.0 / 1.0 | Specific JSON field matches expected value |

## LLM-as-Judge

Uses a secondary LLM call to score output quality against a rubric.

**Important:** LLM-as-judge is a measuring instrument, not ground truth. Use it for dimensions that cannot be measured deterministically (e.g. tone, coherence, helpfulness).

### Rubric Format

```yaml
rubric_id: summarizer_quality_v1
judge_model: gpt-4o
dimensions:
  - name: correctness
    scale: [1, 2, 3, 4, 5]
    instruction: "Are the fields consistent with the complaint text?"
  - name: brevity
    scale: [1, 2, 3, 4, 5]
    instruction: "Is the summary concise and under 35 words?"
  - name: json_validity
    scale: [0, 1]
    instruction: "Is the output valid JSON matching the required schema?"

Aggregations

Per run, PromptForge computes:

    Mean score per evaluator/dimension
    P95 latency across cases
    Failure rate: fraction of cases scoring below threshold
    Total tokens and estimated cost

Regression Detection

See regression policy.