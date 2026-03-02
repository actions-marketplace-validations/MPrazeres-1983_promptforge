"""Domain-specific exceptions for PromptForge."""


class PromptForgeError(Exception):
    """Base exception."""


class PromptSpecError(PromptForgeError):
    """Invalid or missing PromptSpec."""


class DatasetError(PromptForgeError):
    """Invalid or missing Dataset."""


class RunConfigError(PromptForgeError):
    """Invalid RunConfig."""


class LLMClientError(PromptForgeError):
    """LLM provider error."""


class EvaluatorError(PromptForgeError):
    """Evaluator configuration or execution error."""


class StoreError(PromptForgeError):
    """Database persistence error."""


class RegressionError(PromptForgeError):
    """Regression threshold exceeded."""