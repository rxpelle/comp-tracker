import sqlite3
import pytest

from comp_tracker.db import get_connection, CompTitleRepository, SnapshotRepository
from comp_tracker.models import CompTitle, BSRSnapshot
from datetime import date, timedelta


@pytest.fixture
def db_conn(tmp_path):
    """In-memory database connection with schema initialized."""
    db_path = str(tmp_path / "test.db")
    conn = get_connection(db_path)
    yield conn
    conn.close()


@pytest.fixture
def comp_repo(db_conn):
    return CompTitleRepository(db_conn)


@pytest.fixture
def snap_repo(db_conn):
    return SnapshotRepository(db_conn)


@pytest.fixture
def sample_comp():
    return CompTitle(
        title="The Silent Patient",
        author="Alex Michaelides",
        asin="B07HKGJN9C",
        genre="Thriller",
    )


@pytest.fixture
def sample_snapshots():
    """Generate 5 snapshots over 30 days for comp_id=1."""
    today = date.today()
    return [
        BSRSnapshot(comp_id=1, snapshot_date=today - timedelta(days=30), bsr=5000, price=12.99, rating=4.5, reviews=90000),
        BSRSnapshot(comp_id=1, snapshot_date=today - timedelta(days=20), bsr=4500, price=12.99, rating=4.5, reviews=91000),
        BSRSnapshot(comp_id=1, snapshot_date=today - timedelta(days=10), bsr=4000, price=12.99, rating=4.5, reviews=92000),
        BSRSnapshot(comp_id=1, snapshot_date=today - timedelta(days=5), bsr=3500, price=11.99, rating=4.5, reviews=93000),
        BSRSnapshot(comp_id=1, snapshot_date=today, bsr=3000, price=11.99, rating=4.5, reviews=95000),
    ]
