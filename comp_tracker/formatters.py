from __future__ import annotations

from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from comp_tracker.models import (
    AlertType, BSRSnapshot, CompAlert, CompSuggestion, CompTitle, Severity,
)
from comp_tracker.tracker import analyze_trend, calculate_relevance_score

console = Console()


def _trend_arrow(direction: str) -> str:
    arrows = {
        "rising": "[red]▲ Rising[/red]",
        "falling": "[green]▼ Falling[/green]",
        "stable": "[yellow]● Stable[/yellow]",
        "insufficient_data": "[dim]— No data[/dim]",
    }
    return arrows.get(direction, "—")


def _severity_color(severity: Severity) -> str:
    return {
        Severity.INFO: "blue",
        Severity.WARNING: "yellow",
        Severity.CRITICAL: "red",
    }[severity]


def _sparkline(bsr_values: list[int], width: int = 10) -> str:
    """Simple text sparkline for BSR history."""
    if not bsr_values:
        return ""
    blocks = " ▁▂▃▄▅▆▇█"
    mn, mx = min(bsr_values), max(bsr_values)
    if mn == mx:
        return blocks[4] * min(len(bsr_values), width)

    # Sample down to width
    if len(bsr_values) > width:
        step = len(bsr_values) / width
        sampled = [bsr_values[int(i * step)] for i in range(width)]
    else:
        sampled = bsr_values

    # Invert: lower BSR = taller bar (better rank)
    result = ""
    for v in sampled:
        normalized = (mx - v) / (mx - mn)  # invert
        idx = int(normalized * (len(blocks) - 1))
        result += blocks[idx]
    return result


def display_comps(comps_with_latest: list[tuple[CompTitle, BSRSnapshot | None, list[BSRSnapshot]]]):
    """Display all comps with current BSR, trend, and relevance score."""
    table = Table(title="Tracked Comp Titles")
    table.add_column("Title", style="bold")
    table.add_column("Author")
    table.add_column("ASIN", style="dim")
    table.add_column("Genre")
    table.add_column("BSR", justify="right")
    table.add_column("Trend")
    table.add_column("Score", justify="right")
    table.add_column("Active")

    for comp, latest, snapshots in comps_with_latest:
        bsr_str = f"{latest.bsr:,}" if latest else "—"
        trend = analyze_trend(snapshots)
        arrow = _trend_arrow(trend["direction"])
        score = calculate_relevance_score(comp, snapshots)
        score_style = "green" if score >= 60 else "yellow" if score >= 40 else "red"
        active_str = "[green]Yes[/green]" if comp.active else "[dim]No[/dim]"

        table.add_row(
            comp.title,
            comp.author,
            comp.asin or "—",
            comp.genre or "—",
            bsr_str,
            arrow,
            f"[{score_style}]{score:.0f}[/{score_style}]",
            active_str,
        )

    console.print(table)


def display_history(comp_title: CompTitle, snapshots: list[BSRSnapshot]):
    """Display BSR history for one comp."""
    if not snapshots:
        console.print(f"[dim]No BSR history for {comp_title.title}[/dim]")
        return

    table = Table(title=f"BSR History: {comp_title.title}")
    table.add_column("Date")
    table.add_column("BSR", justify="right")
    table.add_column("Price", justify="right")
    table.add_column("Rating", justify="right")
    table.add_column("Reviews", justify="right")
    table.add_column("KU")

    for s in snapshots:
        table.add_row(
            str(s.snapshot_date),
            f"{s.bsr:,}",
            f"${s.price:.2f}" if s.price else "—",
            f"{s.rating:.1f}" if s.rating else "—",
            f"{s.reviews:,}" if s.reviews else "—",
            "Yes" if s.kindle_unlimited else "No",
        )

    bsr_values = [s.bsr for s in snapshots]
    spark = _sparkline(bsr_values)

    console.print(table)
    if spark:
        console.print(f"\nTrend: {spark}  (taller = better rank)")


def display_alerts(alerts: list[CompAlert]):
    """Display color-coded alerts."""
    if not alerts:
        console.print("[green]No active alerts.[/green]")
        return

    for alert in alerts:
        color = _severity_color(alert.severity)
        icon = {
            AlertType.DECLINING: "📉",
            AlertType.STALE: "⏰",
            AlertType.SURGING: "🚀",
            AlertType.PRICE_CHANGE: "💰",
        }.get(alert.alert_type, "•")

        panel = Panel(
            f"{alert.message}\n[dim]{alert.snapshot_date}[/dim]",
            title=f"{icon} {alert.comp_title} — {alert.alert_type.value.upper()}",
            border_style=color,
        )
        console.print(panel)


def display_suggestions(suggestions: list[CompSuggestion]):
    """Display replacement comp suggestions."""
    if not suggestions:
        console.print("[dim]No suggestions available.[/dim]")
        return

    table = Table(title="Replacement Comp Suggestions")
    table.add_column("Title", style="bold")
    table.add_column("Author")
    table.add_column("ASIN", style="dim")
    table.add_column("BSR", justify="right")
    table.add_column("Rating", justify="right")
    table.add_column("Reviews", justify="right")
    table.add_column("Score", justify="right")
    table.add_column("Reasoning")

    for s in suggestions:
        table.add_row(
            s.title,
            s.author,
            s.asin or "—",
            f"{s.current_bsr:,}" if s.current_bsr else "—",
            f"{s.rating:.1f}" if s.rating else "—",
            f"{s.reviews:,}" if s.reviews else "—",
            f"{s.relevance_score:.0f}",
            s.reasoning,
        )

    console.print(table)


def display_dashboard(
    comps_with_data: list[tuple[CompTitle, BSRSnapshot | None, list[BSRSnapshot]]],
    alerts: list[CompAlert],
):
    """Combined overview: all comps + active alerts."""
    console.print()
    display_comps(comps_with_data)
    console.print()

    if alerts:
        console.print(f"\n[bold]Alerts ({len(alerts)})[/bold]")
        display_alerts(alerts)
    else:
        console.print("\n[green]No active alerts.[/green]")
