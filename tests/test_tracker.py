from datetime import date, timedelta
import pytest

from comp_tracker.config import Config
from comp_tracker.models import AlertType, BSRSnapshot, CompTitle, Severity
from comp_tracker.tracker import (
    analyze_trend, calculate_relevance_score, detect_alerts, rank_comps,
)


class TestAnalyzeTrend:
    def test_empty_snapshots(self):
        result = analyze_trend([])
        assert result["direction"] == "insufficient_data"

    def test_single_snapshot(self):
        snaps = [BSRSnapshot(comp_id=1, snapshot_date=date.today(), bsr=5000)]
        result = analyze_trend(snaps)
        assert result["direction"] == "insufficient_data"
        assert result["avg_bsr"] == 5000

    def test_falling_trend(self):
        """BSR dropping = book getting more popular."""
        today = date.today()
        snaps = [
            BSRSnapshot(comp_id=1, snapshot_date=today - timedelta(days=20), bsr=10000),
            BSRSnapshot(comp_id=1, snapshot_date=today, bsr=5000),
        ]
        result = analyze_trend(snaps, days=30)
        assert result["direction"] == "falling"
        assert result["pct_change"] < 0

    def test_rising_trend(self):
        """BSR rising = book losing relevance."""
        today = date.today()
        snaps = [
            BSRSnapshot(comp_id=1, snapshot_date=today - timedelta(days=20), bsr=5000),
            BSRSnapshot(comp_id=1, snapshot_date=today, bsr=10000),
        ]
        result = analyze_trend(snaps, days=30)
        assert result["direction"] == "rising"
        assert result["pct_change"] > 0

    def test_stable_trend(self):
        today = date.today()
        snaps = [
            BSRSnapshot(comp_id=1, snapshot_date=today - timedelta(days=20), bsr=5000),
            BSRSnapshot(comp_id=1, snapshot_date=today, bsr=5200),
        ]
        result = analyze_trend(snaps, days=30)
        assert result["direction"] == "stable"

    def test_min_max_avg(self):
        today = date.today()
        snaps = [
            BSRSnapshot(comp_id=1, snapshot_date=today - timedelta(days=20), bsr=2000),
            BSRSnapshot(comp_id=1, snapshot_date=today - timedelta(days=10), bsr=8000),
            BSRSnapshot(comp_id=1, snapshot_date=today, bsr=5000),
        ]
        result = analyze_trend(snaps, days=30)
        assert result["min_bsr"] == 2000
        assert result["max_bsr"] == 8000
        assert result["avg_bsr"] == 5000


class TestDetectAlerts:
    def _make_comp(self):
        return CompTitle(title="Test Book", author="Test Author", id=1)

    def test_no_snapshots(self):
        alerts = detect_alerts(self._make_comp(), [])
        assert alerts == []

    def test_declining(self):
        today = date.today()
        snaps = [
            BSRSnapshot(comp_id=1, snapshot_date=today - timedelta(days=20), bsr=10000),
            BSRSnapshot(comp_id=1, snapshot_date=today, bsr=20000),
        ]
        alerts = detect_alerts(self._make_comp(), snaps)
        types = [a.alert_type for a in alerts]
        assert AlertType.DECLINING in types

    def test_surging(self):
        today = date.today()
        snaps = [
            BSRSnapshot(comp_id=1, snapshot_date=today - timedelta(days=20), bsr=10000),
            BSRSnapshot(comp_id=1, snapshot_date=today, bsr=5000),
        ]
        alerts = detect_alerts(self._make_comp(), snaps)
        types = [a.alert_type for a in alerts]
        assert AlertType.SURGING in types

    def test_stale(self):
        snaps = [
            BSRSnapshot(comp_id=1, snapshot_date=date.today() - timedelta(days=20), bsr=5000),
        ]
        alerts = detect_alerts(self._make_comp(), snaps)
        types = [a.alert_type for a in alerts]
        assert AlertType.STALE in types

    def test_price_change(self):
        today = date.today()
        snaps = [
            BSRSnapshot(comp_id=1, snapshot_date=today - timedelta(days=5), bsr=5000, price=12.99),
            BSRSnapshot(comp_id=1, snapshot_date=today, bsr=5000, price=9.99),
        ]
        alerts = detect_alerts(self._make_comp(), snaps)
        types = [a.alert_type for a in alerts]
        assert AlertType.PRICE_CHANGE in types

    def test_no_alerts_stable(self):
        today = date.today()
        snaps = [
            BSRSnapshot(comp_id=1, snapshot_date=today - timedelta(days=5), bsr=5000, price=12.99),
            BSRSnapshot(comp_id=1, snapshot_date=today, bsr=5500, price=12.99),
        ]
        alerts = detect_alerts(self._make_comp(), snaps)
        assert len(alerts) == 0

    def test_declining_severity_critical(self):
        today = date.today()
        snaps = [
            BSRSnapshot(comp_id=1, snapshot_date=today - timedelta(days=20), bsr=10000),
            BSRSnapshot(comp_id=1, snapshot_date=today, bsr=20000),
        ]
        alerts = detect_alerts(self._make_comp(), snaps)
        declining = [a for a in alerts if a.alert_type == AlertType.DECLINING]
        assert declining[0].severity == Severity.CRITICAL


class TestRelevanceScore:
    def test_empty_snapshots(self):
        comp = CompTitle(title="Test", author="A")
        assert calculate_relevance_score(comp, []) == 0.0

    def test_high_score(self):
        """Low BSR + fresh data + lots of reviews + long tracking = high score."""
        today = date.today()
        comp = CompTitle(title="Test", author="A")
        snaps = [
            BSRSnapshot(comp_id=1, snapshot_date=today - timedelta(days=100), bsr=3000, reviews=50000),
            BSRSnapshot(comp_id=1, snapshot_date=today, bsr=2000, reviews=55000),
        ]
        score = calculate_relevance_score(comp, snaps)
        assert score >= 80

    def test_low_score(self):
        """High BSR + old data + no reviews = low score."""
        comp = CompTitle(title="Test", author="A")
        snaps = [
            BSRSnapshot(comp_id=1, snapshot_date=date.today() - timedelta(days=60), bsr=800000),
        ]
        score = calculate_relevance_score(comp, snaps)
        assert score < 20


class TestRankComps:
    def test_ranks_by_score(self):
        today = date.today()
        good_comp = CompTitle(title="Good", author="A")
        bad_comp = CompTitle(title="Bad", author="B")

        good_snaps = [
            BSRSnapshot(comp_id=1, snapshot_date=today - timedelta(days=100), bsr=1000, reviews=20000),
            BSRSnapshot(comp_id=1, snapshot_date=today, bsr=1000, reviews=22000),
        ]
        bad_snaps = [
            BSRSnapshot(comp_id=2, snapshot_date=today - timedelta(days=60), bsr=900000),
        ]

        results = rank_comps([(good_comp, good_snaps), (bad_comp, bad_snaps)])
        assert results[0][0].title == "Good"
        assert results[0][1] > results[1][1]

    def test_flags_below_threshold(self):
        comp = CompTitle(title="Weak", author="A")
        snaps = [BSRSnapshot(comp_id=1, snapshot_date=date.today() - timedelta(days=60), bsr=900000)]
        results = rank_comps([(comp, snaps)], threshold=50)
        assert results[0][2] is True  # below threshold
