# src/promptforge/reporting/tables.py
"""Rich CLI table renderers."""

from __future__ import annotations

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from promptforge.store.repositories import RunRepository, ScoreRepository, CaseResultRepository
from promptforge.eval.aggregations import aggregate_run_scores, p95_latency, generate_ascii_bar
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


def render_prompt_history(prompt_id: str, console: Console) -> None:
    """Mostra a evolução dos scores ao longo das versões de um prompt."""
    run_repo = RunRepository()
    score_repo = ScoreRepository()

    # Buscar todos os runs deste prompt, ordenados por data
    all_runs = run_repo.list_runs(limit=50)
    prompt_runs = [r for r in all_runs if r["prompt_id"] == prompt_id]

    if not prompt_runs:
        console.print(f"[yellow]Nenhum run encontrado para o prompt '{prompt_id}'.[/yellow]")
        return

    # Ordenar do mais antigo para o mais recente
    prompt_runs = sorted(prompt_runs, key=lambda r: r["started_at"])

    # Recolher todos os evaluadores únicos
    all_evaluators: set = set()
    runs_data = []
    for run in prompt_runs:
        scores = score_repo.get_by_run(run["run_id"])
        agg = aggregate_run_scores(scores)
        all_evaluators.update(agg.keys())
        runs_data.append((run, agg))

    # Ordenar evaluadores para consistência
    evaluators = sorted(all_evaluators)

    # Construir tabela
    table = Table(
        title=f"📈 Evolution — {prompt_id}",
        show_lines=True,
    )
    table.add_column("Version", style="cyan")
    table.add_column("Date")
    table.add_column("Model", style="dim")

    # Uma coluna por evaluador
    for ev in evaluators:
        short = ev.replace("field_match_", "fm_").replace("quality_", "q_")
        table.add_column(short, justify="right")

    table.add_column("Trend")

    prev_agg = None
    for run, agg in runs_data:
        date_str = run["started_at"][:10]

        # Calcular trend em relação ao run anterior
        if prev_agg is None:
            trend = "[dim]—[/dim]"
        else:
            improvements = sum(1 for ev in evaluators if agg.get(ev, {}).get("mean", 0) > prev_agg.get(ev, {}).get("mean", 0))
            regressions = sum(1 for ev in evaluators if agg.get(ev, {}).get("mean", 0) < prev_agg.get(ev, {}).get("mean", 0))
            if regressions > 0:
                trend = f"[red]↓ {regressions} regressed[/red]"
            elif improvements > 0:
                trend = f"[green]↑ {improvements} improved[/green]"
            else:
                trend = "[dim]= stable[/dim]"

        # Scores por evaluador com barra visual
        score_cells = []
        for ev in evaluators:
            mean = agg.get(ev, {}).get("mean", None)
            if mean is None:
                score_cells.append("[dim]n/a[/dim]")
            else:
                bar = generate_ascii_bar(mean, width=8)
                color = "green" if mean >= 0.8 else "yellow" if mean >= 0.5 else "red"
                score_cells.append(f"[{color}]{mean:.2f}[/{color}] {bar}")

        table.add_row(
            f"v{run['prompt_version']}",
            date_str,
            run["model"],
            *score_cells,
            trend,
        )

        prev_agg = agg

    console.print(table)
    console.print(f"[dim]  {len(prompt_runs)} run(s) encontrados para '{prompt_id}'[/dim]\n")