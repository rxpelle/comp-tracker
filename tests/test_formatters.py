from datetime import date, timedelta
from io import StringIO

from rich.console import Console

from comp_tracker.formatters import (
    display_alerts, display_comps, display_dashboard, display_history,
    display_suggestions, _sparkline,
)
from comp_tracker.models import (
    AlertType, BSRSnapshot, CompAlert, CompSuggestion, CompTitle, Severity,
)


def _capture(fn, *args, **kwargs):
    """Capture Rich console output as string."""
    buf = StringIO()
    import comp_tracker.formatters as fmt
    original = fmt.console
    fmt.console = Console(file=buf, force_terminal=True, width=120)
    try:
        fn(*args, **kwargs)
    finally:
        fmt.console = original
    return buf.getvalue()


class TestDisplayComps:
    def test_renders_table(self):
        comp = CompTitle(title="Test Book", author="Author", asin="B123", genre="Thriller", id=1)
        snap = BSRSnapshot(comp_id=1, snapshot_date=date.today(), bsr=5000)
        output = _capture(display_comps, [(comp, snap, [snap])])
        assert "Test Book" in output
        assert "Author" in output
        assert "5,000" in output

    def test_no_snapshot(self):
        comp = CompTitle(title="No Data", author="Author", id=1)
        output = _capture(display_comps, [(comp, None, [])])
        assert "No Data" in output


class TestDisplayHistory:
    def test_renders_history(self):
        comp = CompTitle(title="Test", author="A", id=1)
        snaps = [
            BSRSnapshot(comp_id=1, snapshot_date=date.today() - timedelta(days=i), bsr=1000 + i * 100)
            for i in range(3)
        ]
        output = _capture(display_history, comp, snaps)
        assert "Test" in output
        assert "1,000" in output

    def test_empty_history(self):
        comp = CompTitle(title="Empty", author="A", id=1)
        output = _capture(display_history, comp, [])
        assert "No BSR history" in output


class TestDisplayAlerts:
    def test_renders_alerts(self):
        alerts = [
            CompAlert(
                comp_title="Test",
                alert_type=AlertType.DECLINING,
                message="BSR rose 60%",
                severity=Severity.CRITICAL,
                snapshot_date=date.today(),
            )
        ]
        output = _capture(display_alerts, alerts)
        assert "Test" in output
        assert "BSR rose 60%" in output

    def test_no_alerts(self):
        output = _capture(display_alerts, [])
        assert "No active alerts" in output


class TestDisplaySuggestions:
    def test_renders_suggestions(self):
        suggestions = [
            CompSuggestion(
                title="New Comp", author="Author", current_bsr=2000,
                relevance_score=85, reasoning="Strong match",
            )
        ]
        output = _capture(display_suggestions, suggestions)
        assert "New Comp" in output
        assert "Strong match" in output

    def test_no_suggestions(self):
        output = _capture(display_suggestions, [])
        assert "No suggestions" in output


class TestDisplayDashboard:
    def test_renders_combined(self):
        comp = CompTitle(title="Dash Test", author="A", id=1)
        snap = BSRSnapshot(comp_id=1, snapshot_date=date.today(), bsr=3000)
        alert = CompAlert(
            comp_title="Dash Test",
            alert_type=AlertType.STALE,
            message="Stale data",
            severity=Severity.WARNING,
            snapshot_date=date.today(),
        )
        output = _capture(display_dashboard, [(comp, snap, [snap])], [alert])
        assert "Dash Test" in output
        assert "Stale data" in output


class TestSparkline:
    def test_basic(self):
        result = _sparkline([1000, 2000, 3000, 2000, 1000])
        assert len(result) == 5

    def test_constant(self):
        result = _sparkline([5000, 5000, 5000])
        assert len(result) == 3

    def test_empty(self):
        assert _sparkline([]) == ""
