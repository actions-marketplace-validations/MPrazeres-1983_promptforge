.PHONY: eval diff report dashboard validate

PROMPT=prompts/summarizer.yaml
DATASET=datasets/summarizer_golden.yaml
CONFIG=configs/openai_gpt4o-mini.yaml

validate:
	promptforge validate --prompt $(PROMPT) --dataset $(DATASET)

eval:
	promptforge eval --prompt $(PROMPT) --dataset $(DATASET) --config $(CONFIG)

report:
	promptforge report --run $(RUN_ID) --out report.md

dashboard:
	promptforge dashboard --run $(RUN_ID)

diff:
	promptforge diff --baseline $(BASELINE) --candidate $(CANDIDATE)