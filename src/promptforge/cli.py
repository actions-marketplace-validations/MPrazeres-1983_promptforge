"""PromptForge CLI — entry point for all commands."""

from __future__ import annotations

from dotenv import load_dotenv

load_dotenv()  # Must run before other imports to load env vars

import typer  # noqa: E402
from rich.console import Console  # noqa: E402

from promptforge.core.prompt_spec import PromptSpec  # noqa: E402
from promptforge.core.dataset import Dataset  # noqa: E402
from promptforge.core.run_config import RunConfig  # noqa: E402
from promptforge.store.db import init_db  # noqa: E402
from promptforge.store.repositories import RunRepository  # noqa: E402
from promptforge.eval.regression import RegressionEngine  # noqa: E402
from promptforge.reporting.markdown_report import MarkdownReporter  # noqa: E402
from promptforge.reporting.tables import (  # noqa: E402
    render_run_summary,
    render_diff_table,
    render_top_failures,
)

app = typer.Typer(
    name="promptforge",
    help="Minimalist LLMOps for prompt versioning, evaluation and regression testing.",
    add_completion=False,
)
console = Console()


@app.command()
def init() -> None:
    """Scaffold a new PromptForge project in the current directory."""
    from pathlib import Path

    dirs = [
        "prompts", "datasets", "configs",
        "reports", ".promptforge",
    ]
    for d in dirs:
        Path(d).mkdir(exist_ok=True)
        console.print(f"[green]✓[/green] Created {d}/")

    init_db()
    console.print("[bold green]✓ PromptForge project initialised.[/bold green]")


@app.command()
def new() -> None:
    """Interactive wizard to scaffold a new prompt, dataset and config."""
    from pathlib import Path
    import yaml

    console.print("\n[bold cyan]🔨 PromptForge — New Prompt Wizard[/bold cyan]\n")

    # 1. Recolher informação
    name = typer.prompt("  Prompt name (e.g. support_triage)")
    description = typer.prompt("  Description")
    provider = typer.prompt("  Provider", default="openai")
    model = typer.prompt("  Model", default="llama-3.3-70b-versatile")
    output_format = typer.prompt("  Output format (text/json)", default="json")
    version = typer.prompt("  Version", default="0.1.0")

    slug = name.strip().lower().replace(" ", "_")

    # 2. Criar pasta rubrics se não existir
    Path("prompts").mkdir(exist_ok=True)
    Path("datasets").mkdir(exist_ok=True)
    Path("configs").mkdir(exist_ok=True)

    # 3. Criar PromptSpec YAML
    prompt_path = Path(f"prompts/{slug}.yaml")
    if prompt_path.exists():
        overwrite = typer.confirm(f"  ⚠ {prompt_path} already exists. Overwrite?", default=False)
        if not overwrite:
            console.print("[yellow]  Skipped prompt file.[/yellow]")
        else:
            _write_prompt(prompt_path, slug, version, description, output_format)
    else:
        _write_prompt(prompt_path, slug, version, description, output_format)

    # 4. Criar Dataset YAML
    dataset_path = Path(f"datasets/{slug}_golden.yaml")
    if dataset_path.exists():
        overwrite = typer.confirm(f"  ⚠ {dataset_path} already exists. Overwrite?", default=False)
        if not overwrite:
            console.print("[yellow]  Skipped dataset file.[/yellow]")
        else:
            _write_dataset(dataset_path, slug)
    else:
        _write_dataset(dataset_path, slug)

    # 5. Criar Config YAML
    config_path = Path(f"configs/{slug}.yaml")
    if config_path.exists():
        overwrite = typer.confirm(f"  ⚠ {config_path} already exists. Overwrite?", default=False)
        if not overwrite:
            console.print("[yellow]  Skipped config file.[/yellow]")
        else:
            _write_config(config_path, provider, model, output_format)
    else:
        _write_config(config_path, provider, model, output_format)

    # 6. Resumo final
    console.print(f"\n[bold green]✓ Done![/bold green] Files created:\n")
    console.print(f"  [cyan]prompts/{slug}.yaml[/cyan]          ← edit your prompt template here")
    console.print(f"  [cyan]datasets/{slug}_golden.yaml[/cyan]  ← add your test cases here")
    console.print(f"  [cyan]configs/{slug}.yaml[/cyan]           ← adjust model and evaluators here")
    console.print(f"\n[bold]Next step:[/bold]")
    console.print(f"  promptforge eval \\")
    console.print(f"    --prompt prompts/{slug}.yaml \\")
    console.print(f"    --dataset datasets/{slug}_golden.yaml \\")
    console.print(f"    --config configs/{slug}.yaml\n")


def _write_prompt(path, slug: str, version: str, description: str, output_format: str) -> None:
    """Escreve um PromptSpec YAML com template de exemplo."""
    content = f"""id: {slug}
version: {version}
description: {description}
template: |
  # TODO: escreve aqui o teu prompt
  # Usa {{{{ variavel }}}} para inputs dinâmicos. Exemplo:
  #
  # Analisa o seguinte texto e responde em JSON:
  # {{{{ text }}}}

inputs:
  text:
    type: string
    description: Input text to process
output:
  format: {output_format}
{"  schema:" if output_format == "json" else ""}
{"    field1: { type: string }" if output_format == "json" else ""}
{"    field2: { type: string }" if output_format == "json" else ""}
params:
  temperature: 0.0
  max_tokens: 300
tags: []
"""
    path.write_text(content, encoding="utf-8")
    console.print(f"  [green]✓[/green] Created {path}")


def _write_dataset(path, slug: str) -> None:
    """Escreve um Dataset YAML com casos de exemplo."""
    content = f"""dataset_id: {slug}_golden
description: Golden dataset for {slug}
cases:
  - id: c001
    input:
      text: "TODO: substitui pelo teu input real"
    expected:
      field1: "valor esperado"
      field2: "valor esperado"
    notes: Exemplo de caso de teste.

  - id: c002
    input:
      text: "TODO: substitui pelo teu segundo input real"
    expected:
      field1: "valor esperado"
      field2: "valor esperado"
    notes: Segundo caso de teste.
"""
    path.write_text(content, encoding="utf-8")
    console.print(f"  [green]✓[/green] Created {path}")


def _write_config(path, provider: str, model: str, output_format: str) -> None:
    """Escreve um RunConfig YAML com evaluadores base."""
    evaluators = """evaluators:
  - type: heuristic
    name: json_validity
  - type: heuristic
    name: schema_match
  - type: heuristic
    name: length_ok
    config:
      max_chars: 500
""" if output_format == "json" else """evaluators:
  - type: heuristic
    name: length_ok
    config:
      max_chars: 500
  - type: heuristic
    name: keyword_match
    config:
      keywords: []
"""

    content = f"""provider: {provider}
model: {model}
params:
  temperature: 0.0
  max_tokens: 300
{evaluators}
regression:
  thresholds:
    json_validity: 0.05
    schema_match: 0.05
"""
    path.write_text(content, encoding="utf-8")
    console.print(f"  [green]✓[/green] Created {path}")


@app.command()
def validate(
    prompt: str = typer.Option(..., help="Path to PromptSpec YAML"),
    dataset: str = typer.Option(..., help="Path to Dataset YAML or JSONL"),
) -> None:
    """Validate PromptSpec and Dataset files."""
    try:
        ps = PromptSpec.from_yaml(prompt)
        console.print(f"[green]✓[/green] PromptSpec valid: {ps.id} v{ps.version}")
    except Exception as e:
        console.print(f"[red]✗ PromptSpec error:[/red] {e}")
        raise typer.Exit(1)

    try:
        ds = Dataset.from_file(dataset)
        console.print(f"[green]✓[/green] Dataset valid: {ds.dataset_id} ({len(ds.cases)} cases)")
    except Exception as e:
        console.print(f"[red]✗ Dataset error:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def eval(
    prompt: str = typer.Option(..., help="Path to PromptSpec YAML"),
    dataset: str = typer.Option(..., help="Path to Dataset YAML or JSONL"),
    config: str = typer.Option(..., help="Path to RunConfig YAML"),
    out: str = typer.Option(None, help="Optional JSON output path"),
) -> None:
    """Run evaluation of a prompt against a dataset."""
    from promptforge.core.pipeline import EvalPipeline

    init_db()
    ps = PromptSpec.from_yaml(prompt)
    ds = Dataset.from_file(dataset)
    rc = RunConfig.from_yaml(config)

    console.print(f"[bold]Running eval:[/bold] {ps.id} v{ps.version} | {ds.dataset_id} | {rc.model}")

    pipeline = EvalPipeline(ps, ds, rc, console=console)
    run_id = pipeline.run()

    console.print(f"\n[bold green]✓ Run complete.[/bold green] run_id=[cyan]{run_id}[/cyan]")
    render_run_summary(run_id, console)

    if out:
        pipeline.export_json(run_id, out)
        console.print(f"[green]✓[/green] Results exported to {out}")


@app.command()
def diff(
    baseline: str = typer.Option(..., help="Baseline run ID"),
    candidate: str = typer.Option(..., help="Candidate run ID"),
) -> None:
    """Compare two runs and show regressions/improvements."""
    init_db()
    engine = RegressionEngine()
    result = engine.compare(baseline, candidate)
    render_diff_table(result, console)

    if result.has_regressions:
        console.print("[bold red]✗ Regressions detected.[/bold red]")
        raise typer.Exit(1)
    else:
        console.print("[bold green]✓ No regressions detected.[/bold green]")


@app.command()
def report(
    run: str = typer.Option(..., help="Run ID"),
    out: str = typer.Option("report.md", help="Output Markdown file path"),
) -> None:
    """Generate a Markdown report for a run."""
    init_db()
    reporter = MarkdownReporter()
    reporter.generate(run, out)
    console.print(f"[green]✓[/green] Report written to {out}")


@app.command()
def dashboard(
    run: str = typer.Option(..., help="Run ID"),
) -> None:
    """Show CLI dashboard for a run."""
    init_db()
    render_run_summary(run, console)
    render_top_failures(run, console)


@app.command()
def runs(
    limit: int = typer.Option(10, help="Number of recent runs to show"),
) -> None:
    """List recent runs."""
    init_db()
    repo = RunRepository()
    recent = repo.list_runs(limit=limit)
    from rich.table import Table
    table = Table(title="Recent Runs")
    table.add_column("run_id", style="cyan")
    table.add_column("prompt")
    table.add_column("version")
    table.add_column("model")
    table.add_column("cases")
    table.add_column("started_at")
    for r in recent:
        table.add_row(
            r["run_id"][:8] + "...",
            r["prompt_id"],
            r["prompt_version"],
            r["model"],
            str(r["total_cases"]),
            r["started_at"],
        )
    console.print(table)


if __name__ == "__main__":
    app()