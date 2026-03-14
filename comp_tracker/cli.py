import click
from rich.console import Console

from comp_tracker.config import Config
from comp_tracker.db import (
    CompTitleRepository, SnapshotRepository, get_connection,
)
from comp_tracker.formatters import (
    display_alerts, display_comps, display_dashboard, display_history,
)
from comp_tracker.models import BSRSnapshot, CompTitle
from comp_tracker.parsers import parse_bsr_snapshot_csv, parse_comp_csv, parse_comp_yaml
from comp_tracker.tracker import analyze_trend, detect_alerts

console = Console()


def _get_repos(db_path: str = None):
    path = db_path or Config.DB_PATH
    conn = get_connection(path)
    return CompTitleRepository(conn), SnapshotRepository(conn)


@click.group()
@click.option('--db', envvar='COMP_TRACKER_DB', default=None, help='Path to SQLite database')
@click.pass_context
def main(ctx, db):
    ctx.ensure_object(dict)
    ctx.obj['db_path'] = db


@main.command()
@click.argument('title')
@click.option('--author', required=True, help='Author name')
@click.option('--asin', default=None, help='Amazon ASIN')
@click.option('--genre', default=None, help='Genre/category')
@click.option('--notes', default=None, help='Notes')
@click.pass_context
def add(ctx, title, author, asin, genre, notes):
    """Add a comp title to track."""
    comp_repo, _ = _get_repos(ctx.obj['db_path'])

    existing = comp_repo.find_by_title(title)
    if existing:
        console.print(f"[yellow]Comp '{title}' already exists (id={existing.id})[/yellow]")
        return

    comp = CompTitle(title=title, author=author, asin=asin, genre=genre, notes=notes)
    comp = comp_repo.add(comp)
    console.print(f"[green]Added comp: {comp.title} by {comp.author} (id={comp.id})[/green]")


@main.command(name='import')
@click.argument('file', type=click.Path(exists=True))
@click.pass_context
def import_comps(ctx, file):
    """Bulk import comp titles from CSV or YAML file."""
    comp_repo, _ = _get_repos(ctx.obj['db_path'])

    if file.endswith(('.yml', '.yaml')):
        comps = parse_comp_yaml(file)
    else:
        with open(file, 'r') as f:
            comps = parse_comp_csv(f.read())

    added = 0
    skipped = 0
    for comp in comps:
        existing = comp_repo.find_by_title(comp.title)
        if existing:
            skipped += 1
            continue
        comp_repo.add(comp)
        added += 1

    console.print(f"[green]Imported {added} comps[/green] ({skipped} skipped as duplicates)")


@main.command(name='list')
@click.option('--active-only', is_flag=True, help='Show only active comps')
@click.pass_context
def list_comps(ctx, active_only):
    """List all tracked comp titles with latest BSR."""
    comp_repo, snap_repo = _get_repos(ctx.obj['db_path'])
    comps = comp_repo.list_active() if active_only else comp_repo.list_all()

    if not comps:
        console.print("[dim]No comps tracked yet. Use 'comp-tracker add' to get started.[/dim]")
        return

    latest_map = snap_repo.get_all_latest()
    data = []
    for comp in comps:
        latest = latest_map.get(comp.id)
        snapshots = snap_repo.get_history(comp.id) if comp.id else []
        data.append((comp, latest, snapshots))

    display_comps(data)


@main.command()
@click.argument('title_or_asin')
@click.option('--bsr', required=True, type=int, help='Best Seller Rank')
@click.option('--price', default=None, type=float, help='Current price')
@click.option('--rating', default=None, type=float, help='Average rating')
@click.option('--reviews', default=None, type=int, help='Number of reviews')
@click.option('--ku', is_flag=True, help='In Kindle Unlimited')
@click.option('--date', '-d', default=None, help='Snapshot date (YYYY-MM-DD), defaults to today')
@click.pass_context
def record(ctx, title_or_asin, bsr, price, rating, reviews, ku, date):
    """Record a BSR snapshot for a comp title."""
    comp_repo, snap_repo = _get_repos(ctx.obj['db_path'])
    comp = comp_repo.find_by_title_or_asin(title_or_asin)

    if not comp:
        console.print(f"[red]Comp not found: {title_or_asin}[/red]")
        return

    snapshot = BSRSnapshot(
        comp_id=comp.id,
        snapshot_date=date,
        bsr=bsr,
        price=price,
        rating=rating,
        reviews=reviews,
        kindle_unlimited=ku,
    )
    snap_repo.add(snapshot)
    console.print(f"[green]Recorded BSR {bsr:,} for {comp.title}[/green]")


@main.command(name='record-bulk')
@click.argument('file', type=click.Path(exists=True))
@click.pass_context
def record_bulk(ctx, file):
    """Import BSR snapshots from a CSV file."""
    comp_repo, snap_repo = _get_repos(ctx.obj['db_path'])

    with open(file, 'r') as f:
        entries = parse_bsr_snapshot_csv(f.read())

    recorded = 0
    not_found = 0
    for identifier, snapshot in entries:
        comp = comp_repo.find_by_title_or_asin(identifier)
        if not comp:
            console.print(f"[yellow]Comp not found: {identifier}[/yellow]")
            not_found += 1
            continue
        snapshot.comp_id = comp.id
        snap_repo.add(snapshot)
        recorded += 1

    console.print(f"[green]Recorded {recorded} snapshots[/green] ({not_found} not found)")


@main.command()
@click.argument('title_or_asin')
@click.option('--days', default=30, help='Analysis period in days')
@click.pass_context
def analyze(ctx, title_or_asin, days):
    """Show trend analysis for a comp title."""
    comp_repo, snap_repo = _get_repos(ctx.obj['db_path'])
    comp = comp_repo.find_by_title_or_asin(title_or_asin)

    if not comp:
        console.print(f"[red]Comp not found: {title_or_asin}[/red]")
        return

    snapshots = snap_repo.get_history(comp.id, days=days)
    trend = analyze_trend(snapshots, days=days)

    console.print(f"\n[bold]{comp.title}[/bold] — {days}-day analysis")
    console.print(f"  Direction: {trend['direction']}")
    console.print(f"  Change:    {trend['pct_change']:+.1f}%")
    console.print(f"  Avg BSR:   {trend['avg_bsr']:,}")
    console.print(f"  Min BSR:   {trend['min_bsr']:,}")
    console.print(f"  Max BSR:   {trend['max_bsr']:,}")


@main.command()
@click.pass_context
def dashboard(ctx):
    """Overview of all comps + active alerts."""
    comp_repo, snap_repo = _get_repos(ctx.obj['db_path'])
    comps = comp_repo.list_active()

    if not comps:
        console.print("[dim]No comps tracked yet.[/dim]")
        return

    latest_map = snap_repo.get_all_latest()
    all_alerts = []
    data = []

    for comp in comps:
        latest = latest_map.get(comp.id)
        snapshots = snap_repo.get_history(comp.id)
        data.append((comp, latest, snapshots))
        all_alerts.extend(detect_alerts(comp, snapshots))

    display_dashboard(data, all_alerts)


@main.command()
@click.pass_context
def alerts(ctx):
    """Show active alerts for all tracked comps."""
    comp_repo, snap_repo = _get_repos(ctx.obj['db_path'])
    comps = comp_repo.list_active()
    all_alerts = []

    for comp in comps:
        snapshots = snap_repo.get_history(comp.id)
        all_alerts.extend(detect_alerts(comp, snapshots))

    display_alerts(all_alerts)


@main.command()
@click.argument('title_or_asin')
@click.pass_context
def deactivate(ctx, title_or_asin):
    """Mark a comp as inactive."""
    comp_repo, _ = _get_repos(ctx.obj['db_path'])
    comp = comp_repo.find_by_title_or_asin(title_or_asin)

    if not comp:
        console.print(f"[red]Comp not found: {title_or_asin}[/red]")
        return

    comp_repo.deactivate(comp.id)
    console.print(f"[yellow]Deactivated: {comp.title}[/yellow]")


@main.command()
@click.argument('title_or_asin')
@click.option('--days', default=90, help='Number of days of history')
@click.pass_context
def history(ctx, title_or_asin, days):
    """Show BSR history for a comp title."""
    comp_repo, snap_repo = _get_repos(ctx.obj['db_path'])
    comp = comp_repo.find_by_title_or_asin(title_or_asin)

    if not comp:
        console.print(f"[red]Comp not found: {title_or_asin}[/red]")
        return

    snapshots = snap_repo.get_history(comp.id, days=days)
    display_history(comp, snapshots)


@main.command()
@click.argument('title_or_asin')
@click.option('--confirm', is_flag=True, required=True, help='Confirm deletion')
@click.pass_context
def delete(ctx, title_or_asin, confirm):
    """Permanently delete a comp and all its data."""
    comp_repo, _ = _get_repos(ctx.obj['db_path'])
    comp = comp_repo.find_by_title_or_asin(title_or_asin)

    if not comp:
        console.print(f"[red]Comp not found: {title_or_asin}[/red]")
        return

    comp_repo.delete(comp.id)
    console.print(f"[red]Deleted: {comp.title} and all snapshot data[/red]")
