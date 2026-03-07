# FIX #9: exportar API pública para que `from promptforge import PromptSpec` funcione
from promptforge.core.prompt_spec import PromptSpec
from promptforge.core.dataset import Dataset
from promptforge.core.run_config import RunConfig
from promptforge.core.pipeline import EvalPipeline

__version__ = "0.1.0"
__all__ = ["PromptSpec", "Dataset", "RunConfig", "EvalPipeline"]
