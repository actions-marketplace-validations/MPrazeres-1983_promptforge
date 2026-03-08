"""
Exemplo de uso do PromptForge como biblioteca Python.
Corre um eval completo e imprime os resultados programaticamente.
"""
from dotenv import load_dotenv
load_dotenv()

from promptforge import PromptSpec, Dataset, RunConfig, EvalPipeline
from promptforge.store.db import init_db
from promptforge.store.repositories import RunRepository, ScoreRepository
from promptforge.eval.aggregations import aggregate_run_scores

# 1. Inicializar a base de dados
init_db()

# 2. Carregar os ficheiros
ps = PromptSpec.from_yaml("prompts/support_triage.yaml")
ds = Dataset.from_file("datasets/support_golden.yaml")
rc = RunConfig.from_yaml("configs/support_triage.yaml")

print(f"Prompt: {ps.id} v{ps.version}")
print(f"Dataset: {ds.dataset_id} ({len(ds.cases)} casos)")
print(f"Modelo: {rc.model}")
print()

# 3. Correr o eval
pipeline = EvalPipeline(ps, ds, rc)
run_id = pipeline.run()

# 4. Ler os resultados directamente da base de dados
score_repo = ScoreRepository()
scores = score_repo.get_by_run(run_id)
agg = aggregate_run_scores(scores)

# 5. Usar os resultados no código
print(f"Run ID: {run_id}")
print()
print("Resultados:")
for evaluator, stats in agg.items():
    status = "✅" if stats["mean"] >= 0.9 else "⚠️" if stats["mean"] >= 0.7 else "❌"
    print(f"  {status} {evaluator}: {stats['mean']:.1%} (falhas: {stats['failure_rate']:.1%})")

print()

# 6. Lógica de negócio baseada nos scores
all_pass = all(s["mean"] >= 0.9 for s in agg.values())
if all_pass:
    print("✅ Prompt aprovado — pode ser promovido para produção.")
else:
    print("❌ Prompt reprovado — revê os casos que falharam antes de promover.")
    failing = [ev for ev, s in agg.items() if s["mean"] < 0.9]
    print(f"   Evaluadores com problemas: {', '.join(failing)}")
