from datetime import date, timedelta
import pytest

from comp_tracker.models import CompTitle, BSRSnapshot


class TestCompTitleRepository:
    def test_add_and_find_by_title(self, comp_repo, sample_comp):
        added = comp_repo.add(sample_comp)
        assert added.id is not None

        found = comp_repo.find_by_title("The Silent Patient")
        assert found is not None
        assert found.title == "The Silent Patient"
        assert found.author == "Alex Michaelides"

    def test_find_by_title_case_insensitive(self, comp_repo, sample_comp):
        comp_repo.add(sample_comp)
        found = comp_repo.find_by_title("the silent patient")
        assert found is not None

    def test_find_by_asin(self, comp_repo, sample_comp):
        comp_repo.add(sample_comp)
        found = comp_repo.find_by_asin("B07HKGJN9C")
        assert found is not None
        assert found.title == "The Silent Patient"

    def test_find_by_title_or_asin(self, comp_repo, sample_comp):
        comp_repo.add(sample_comp)
        assert comp_repo.find_by_title_or_asin("B07HKGJN9C") is not None
        assert comp_repo.find_by_title_or_asin("The Silent Patient") is not None
        assert comp_repo.find_by_title_or_asin("nonexistent") is None

    def test_list_all(self, comp_repo):
        comp_repo.add(CompTitle(title="Book A", author="Author A"))
        comp_repo.add(CompTitle(title="Book B", author="Author B"))
        all_comps = comp_repo.list_all()
        assert len(all_comps) == 2

    def test_list_active(self, comp_repo):
        c1 = comp_repo.add(CompTitle(title="Active", author="A"))
        c2 = comp_repo.add(CompTitle(title="Inactive", author="B"))
        comp_repo.deactivate(c2.id)

        active = comp_repo.list_active()
        assert len(active) == 1
        assert active[0].title == "Active"

    def test_deactivate(self, comp_repo, sample_comp):
        added = comp_repo.add(sample_comp)
        result = comp_repo.deactivate(added.id)
        assert result is True

        found = comp_repo.find_by_title("The Silent Patient")
        assert found.active is False

    def test_deactivate_nonexistent(self, comp_repo):
        assert comp_repo.deactivate(999) is False

    def test_delete(self, comp_repo, snap_repo, sample_comp):
        added = comp_repo.add(sample_comp)
        snap_repo.add(BSRSnapshot(comp_id=added.id, snapshot_date=date.today(), bsr=1000))

        result = comp_repo.delete(added.id)
        assert result is True
        assert comp_repo.find_by_title("The Silent Patient") is None
        assert snap_repo.get_latest(added.id) is None

    def test_delete_nonexistent(self, comp_repo):
        assert comp_repo.delete(999) is False


class TestSnapshotRepository:
    def test_add_and_get_latest(self, comp_repo, snap_repo, sample_comp):
        comp = comp_repo.add(sample_comp)
        snap_repo.add(BSRSnapshot(comp_id=comp.id, snapshot_date=date.today() - timedelta(days=1), bsr=5000))
        snap_repo.add(BSRSnapshot(comp_id=comp.id, snapshot_date=date.today(), bsr=4000))

        latest = snap_repo.get_latest(comp.id)
        assert latest is not None
        assert latest.bsr == 4000

    def test_get_history(self, comp_repo, snap_repo, sample_comp):
        comp = comp_repo.add(sample_comp)
        for i in range(5):
            snap_repo.add(BSRSnapshot(
                comp_id=comp.id,
                snapshot_date=date.today() - timedelta(days=i * 10),
                bsr=1000 + i * 500,
            ))

        history = snap_repo.get_history(comp.id, days=30)
        assert len(history) == 4  # 0, 10, 20, 30 days ago

    def test_get_history_ordered(self, comp_repo, snap_repo, sample_comp):
        comp = comp_repo.add(sample_comp)
        snap_repo.add(BSRSnapshot(comp_id=comp.id, snapshot_date=date.today(), bsr=1000))
        snap_repo.add(BSRSnapshot(comp_id=comp.id, snapshot_date=date.today() - timedelta(days=5), bsr=2000))

        history = snap_repo.get_history(comp.id, days=30)
        assert history[0].bsr == 2000  # older first
        assert history[1].bsr == 1000

    def test_bulk_add(self, comp_repo, snap_repo, sample_comp):
        comp = comp_repo.add(sample_comp)
        snapshots = [
            BSRSnapshot(comp_id=comp.id, snapshot_date=date.today(), bsr=1000),
            BSRSnapshot(comp_id=comp.id, snapshot_date=date.today() - timedelta(days=1), bsr=1100),
        ]
        result = snap_repo.bulk_add(snapshots)
        assert len(result) == 2
        assert all(s.id is not None for s in result)

    def test_get_all_latest(self, comp_repo, snap_repo):
        c1 = comp_repo.add(CompTitle(title="A", author="A"))
        c2 = comp_repo.add(CompTitle(title="B", author="B"))
        snap_repo.add(BSRSnapshot(comp_id=c1.id, snapshot_date=date.today(), bsr=100))
        snap_repo.add(BSRSnapshot(comp_id=c2.id, snapshot_date=date.today(), bsr=200))

        latest = snap_repo.get_all_latest()
        assert len(latest) == 2
        assert latest[c1.id].bsr == 100
        assert latest[c2.id].bsr == 200

    def test_get_latest_none(self, snap_repo):
        assert snap_repo.get_latest(999) is None
