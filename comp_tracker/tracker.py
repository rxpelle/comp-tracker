from datetime import date, timedelta

from comp_tracker.config import Config
from comp_tracker.models import (
    AlertType, BSRSnapshot, CompAlert, CompTitle, Severity,
)


def analyze_trend(snapshots: list[BSRSnapshot], days: int = 30) -> dict:
    """Analyze BSR trend over the given period.

    Returns dict with: direction, pct_change, avg_bsr, min_bsr, max_bsr.
    """
    if not snapshots:
        return {
            "direction": "insufficient_data",
            "pct_change": 0.0,
            "avg_bsr": 0,
            "min_bsr": 0,
            "max_bsr": 0,
        }

    cutoff = date.today() - timedelta(days=days)
    recent = [s for s in snapshots if s.snapshot_date >= cutoff]

    if len(recent) < 2:
        bsr_values = [s.bsr for s in snapshots]
        return {
            "direction": "insufficient_data",
            "pct_change": 0.0,
            "avg_bsr": sum(bsr_values) // len(bsr_values),
            "min_bsr": min(bsr_values),
            "max_bsr": max(bsr_values),
        }

    recent_sorted = sorted(recent, key=lambda s: s.snapshot_date)
    first_bsr = recent_sorted[0].bsr
    last_bsr = recent_sorted[-1].bsr
    bsr_values = [s.bsr for s in recent_sorted]

    if first_bsr == 0:
        pct_change = 0.0
    else:
        # BSR rising = book declining; BSR falling = book improving
        pct_change = ((last_bsr - first_bsr) / first_bsr) * 100

    if pct_change > 10:
        direction = "rising"  # BSR going up = book losing relevance
    elif pct_change < -10:
        direction = "falling"  # BSR going down = book gaining relevance
    else:
        direction = "stable"

    return {
        "direction": direction,
        "pct_change": round(pct_change, 1),
        "avg_bsr": sum(bsr_values) // len(bsr_values),
        "min_bsr": min(bsr_values),
        "max_bsr": max(bsr_values),
    }


def detect_alerts(
    comp_title: CompTitle,
    snapshots: list[BSRSnapshot],
    config: Config = None,
) -> list[CompAlert]:
    """Check for alert conditions on a comp title."""
    if config is None:
        config = Config()

    alerts = []

    if not snapshots:
        return alerts

    sorted_snaps = sorted(snapshots, key=lambda s: s.snapshot_date)
    latest = sorted_snaps[-1]

    # Stale check: no snapshot in STALE_DAYS
    days_since = (date.today() - latest.snapshot_date).days
    if days_since >= config.STALE_DAYS:
        alerts.append(CompAlert(
            comp_title=comp_title.title,
            alert_type=AlertType.STALE,
            message=f"No BSR data in {days_since} days. Record a new snapshot.",
            severity=Severity.WARNING,
            snapshot_date=latest.snapshot_date,
        ))

    # Need at least 2 snapshots for trend-based alerts
    if len(sorted_snaps) < 2:
        return alerts

    # Declining: BSR rose >ALERT_DECLINE_THRESHOLD% over 30 days
    thirty_days_ago = date.today() - timedelta(days=30)
    recent = [s for s in sorted_snaps if s.snapshot_date >= thirty_days_ago]
    if len(recent) >= 2:
        first_bsr = recent[0].bsr
        last_bsr = recent[-1].bsr
        if first_bsr > 0:
            change_pct = ((last_bsr - first_bsr) / first_bsr) * 100
            if change_pct > config.ALERT_DECLINE_THRESHOLD:
                alerts.append(CompAlert(
                    comp_title=comp_title.title,
                    alert_type=AlertType.DECLINING,
                    message=f"BSR rose {change_pct:.0f}% in 30 days ({first_bsr:,} -> {last_bsr:,}). Comp losing relevance.",
                    severity=Severity.CRITICAL,
                    snapshot_date=latest.snapshot_date,
                ))
            elif change_pct < -config.ALERT_SURGE_THRESHOLD:
                alerts.append(CompAlert(
                    comp_title=comp_title.title,
                    alert_type=AlertType.SURGING,
                    message=f"BSR dropped {abs(change_pct):.0f}% in 30 days ({first_bsr:,} -> {last_bsr:,}). Comp is surging!",
                    severity=Severity.INFO,
                    snapshot_date=latest.snapshot_date,
                ))

    # Price change: last two snapshots have different prices
    if len(sorted_snaps) >= 2:
        prev = sorted_snaps[-2]
        if prev.price is not None and latest.price is not None and prev.price != latest.price:
            alerts.append(CompAlert(
                comp_title=comp_title.title,
                alert_type=AlertType.PRICE_CHANGE,
                message=f"Price changed from ${prev.price:.2f} to ${latest.price:.2f}.",
                severity=Severity.INFO,
                snapshot_date=latest.snapshot_date,
            ))

    return alerts


def calculate_relevance_score(
    comp: CompTitle,
    snapshots: list[BSRSnapshot],
) -> float:
    """Score 0-100 based on BSR recency, review velocity, rating stability, tracking duration."""
    if not snapshots:
        return 0.0

    sorted_snaps = sorted(snapshots, key=lambda s: s.snapshot_date)
    latest = sorted_snaps[-1]

    score = 0.0

    # BSR component (40 points): lower BSR = higher score
    if latest.bsr <= 5000:
        score += 40
    elif latest.bsr <= 20000:
        score += 35
    elif latest.bsr <= 50000:
        score += 25
    elif latest.bsr <= 100000:
        score += 15
    elif latest.bsr <= 500000:
        score += 5
    # >500k = 0 points

    # Freshness component (20 points): days since last snapshot
    days_old = (date.today() - latest.snapshot_date).days
    if days_old <= 3:
        score += 20
    elif days_old <= 7:
        score += 15
    elif days_old <= 14:
        score += 10
    elif days_old <= 30:
        score += 5
    # >30 days = 0 points

    # Review velocity (20 points): based on review count
    if latest.reviews is not None:
        if latest.reviews >= 10000:
            score += 20
        elif latest.reviews >= 1000:
            score += 15
        elif latest.reviews >= 100:
            score += 10
        elif latest.reviews >= 10:
            score += 5

    # Tracking duration (20 points): longer tracking = more data = more useful
    if len(sorted_snaps) >= 2:
        tracking_days = (sorted_snaps[-1].snapshot_date - sorted_snaps[0].snapshot_date).days
        if tracking_days >= 90:
            score += 20
        elif tracking_days >= 60:
            score += 15
        elif tracking_days >= 30:
            score += 10
        elif tracking_days >= 7:
            score += 5

    return min(score, 100.0)


def rank_comps(
    comps_with_snapshots: list[tuple[CompTitle, list[BSRSnapshot]]],
    threshold: float = None,
) -> list[tuple[CompTitle, float, bool]]:
    """Rank comps by relevance score. Returns (comp, score, below_threshold)."""
    if threshold is None:
        threshold = Config.RELEVANCE_THRESHOLD

    results = []
    for comp, snapshots in comps_with_snapshots:
        score = calculate_relevance_score(comp, snapshots)
        below = score < threshold
        results.append((comp, score, below))

    results.sort(key=lambda x: x[1], reverse=True)
    return results
