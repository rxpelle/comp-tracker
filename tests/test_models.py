from datetime import date
from comp_tracker.models import (
    AlertType, BSRSnapshot, CompAlert, CompSuggestion, CompTitle, Severity,
)


class TestCompTitle:
    def test_creation_defaults(self):
        comp = CompTitle(title="Test Book", author="Test Author")
        assert comp.title == "Test Book"
        assert comp.author == "Test Author"
        assert comp.asin is None
        assert comp.genre is None
        assert comp.added_date == date.today()
        assert comp.notes is None
        assert comp.active is True
        assert comp.id is None

    def test_creation_full(self):
        comp = CompTitle(
            title="Test", author="Author", asin="B123",
            genre="Thriller", notes="Good comp", active=False, id=5,
        )
        assert comp.asin == "B123"
        assert comp.genre == "Thriller"
        assert comp.active is False
        assert comp.id == 5


class TestBSRSnapshot:
    def test_creation_defaults(self):
        snap = BSRSnapshot(comp_id=1, snapshot_date=date.today(), bsr=5000)
        assert snap.comp_id == 1
        assert snap.bsr == 5000
        assert snap.price is None
        assert snap.rating is None
        assert snap.reviews is None
        assert snap.kindle_unlimited is False
        assert snap.id is None

    def test_creation_full(self):
        snap = BSRSnapshot(
            comp_id=1, snapshot_date=date(2026, 1, 1), bsr=500,
            price=9.99, rating=4.2, reviews=1000, kindle_unlimited=True, id=10,
        )
        assert snap.price == 9.99
        assert snap.kindle_unlimited is True


class TestCompAlert:
    def test_creation(self):
        alert = CompAlert(
            comp_title="Test",
            alert_type=AlertType.DECLINING,
            message="BSR rose 60%",
            severity=Severity.CRITICAL,
            snapshot_date=date.today(),
        )
        assert alert.alert_type == AlertType.DECLINING
        assert alert.severity == Severity.CRITICAL


class TestCompSuggestion:
    def test_creation_defaults(self):
        s = CompSuggestion(title="New Book", author="Author")
        assert s.relevance_score == 0.0
        assert s.reasoning == ""


class TestEnums:
    def test_alert_types(self):
        assert AlertType.DECLINING.value == "declining"
        assert AlertType.STALE.value == "stale"
        assert AlertType.SURGING.value == "surging"
        assert AlertType.PRICE_CHANGE.value == "price_change"

    def test_severity(self):
        assert Severity.INFO.value == "info"
        assert Severity.WARNING.value == "warning"
        assert Severity.CRITICAL.value == "critical"
