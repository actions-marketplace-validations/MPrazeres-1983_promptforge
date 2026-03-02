# src/promptforge/reporting/tables.py
"""Rich CLI table renderers."""

from __future__ import annotations

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from promptforge.store.repositories import RunRepository, ScoreRepository, CaseResultRepository
from promptforge.eval.aggregations import aggregate_run_scores, p95_latency
from promptforge.eval.regression import RegressionResult


def render_run_summary(run_id: str, console: Console) -> None:
    run_repo = RunRepository()
    score_repo = ScoreRepository()
    case_repo = CaseResultRepository()

    run = run_repo.get_run(run_id)
    if not run:
        console.print(f"[red]Run not found: {run_id}[/red]")
        return

    scores = score_repo.get_by_run(run_id)
    cases = case_repo.get_by_run(run_id)
    agg = aggregate_run_scores(scores)
    latencies = [c["latency_ms"] for c in cases]

    table = Table(title=f"Run Summary — {run_id[:8]}...", show_lines=True)
    table.add_column("Evaluator", style="cyan")
    table.add_column("Mean Score", justify="right")
    table.add_column("Failure Rate", justify="right")
    table.add_column("Cases", justify="right")

    for ev, stats in agg.items():
        color = "green" if stats["mean"] >= 0.8 else "yellow" if stats["mean"] >= 0.5 else "red"
        table.add_row(
            ev,
            f"[{color}]{stats['mean']:.3f}[/{color}]",
            f"{stats['failure_rate']:.1%}",
            str(stats["count"]),
        )

    console.print(table)

    p95 = p95_latency(latencies) if latencies else 0
    mean_lat = sum(latencies) / len(latencies) if latencies else 0
    console.print(Panel(
        f"[bold]Tokens:[/bold] {run['total_tokens']}  |  "
        f"[bold]Mean Latency:[/bold] {mean_lat:.0f}ms  |  "
        f"[bold]P95 Latency:[/bold] {p95:.0f}ms",
        title="Cost & Latency",
    ))


def render_diff_table(result: RegressionResult, console: Console) -> None:
    table = Table(title="Regression Diff", show_lines=True)
    table.add_column("Evaluator", style="cyan")
    table.add_column("Baseline", justify="right")
    table.add_column("Candidate", justify="right")
    table.add_column("Delta", justify="right")
    table.add_column("Status")

    for d in result.diffs:
        delta_str = f"{d.delta:+.3f}"
        if d.is_regression:
            status = "[bold red]❌ REGRESSION[/bold red]"
            delta_color = "red"
        elif d.delta > 0:
            status = "[bold green]✅ IMPROVED[/bold green]"
            delta_color = "green"
        else:
            status = "[dim]— unchanged[/dim]"
            delta_color = "dim"

        table.add_row(
            d.evaluator,
            f"{d.baseline_mean:.3f}",
            f"{d.candidate_mean:.3f}",
            f"[{delta_color}]{delta_str}[/{delta_color}]",
            status,
        )

    console.print(table)


def render_top_failures(run_id: str, console: Console, limit: int = 10) -> None:
    score_repo = ScoreRepository()
    scores = score_repo.get_by_run(run_id)
    failures = sorted(
        [s for s in scores if s["score"] < 0.5],
        key=lambda x: x["score"],
    )[:limit]

    if not failures:
        console.print("[green]✓ No failures in this run.[/green]")
        return

    table = Table(title=f"Top {limit} Failures", show_lines=True)
    table.add_column("Case ID", style="cyan")
    table.add_column("Evaluator")
    table.add_column("Score", justify="right")
    table.add_column("Rationale")

    for f in failures:
        table.add_row(
            f["case_id"],
            f["evaluator"],
            f"[red]{f['score']:.2f}[/red]",
            (f["rationale"] or "")[:80],
        )

    console.print(table)