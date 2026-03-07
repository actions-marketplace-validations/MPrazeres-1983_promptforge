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