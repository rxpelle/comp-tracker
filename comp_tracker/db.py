import sqlite3
from datetime import date, timedelta
from pathlib import Path
from typing import Optional

from comp_tracker.models import CompTitle, BSRSnapshot


SCHEMA = """
CREATE TABLE IF NOT EXISTS comp_titles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    author TEXT NOT NULL,
    asin TEXT,
    genre TEXT,
    added_date TEXT NOT NULL,
    notes TEXT,
    active INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS bsr_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    comp_id INTEGER NOT NULL,
    snapshot_date TEXT NOT NULL,
    bsr INTEGER NOT NULL,
    price REAL,
    rating REAL,
    reviews INTEGER,
    kindle_unlimited INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (comp_id) REFERENCES comp_titles(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_snapshots_comp_id ON bsr_snapshots(comp_id);
CREATE INDEX IF NOT EXISTS idx_snapshots_date ON bsr_snapshots(snapshot_date);
"""


def get_connection(db_path: str) -> sqlite3.Connection:
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA)
    return conn


def _row_to_comp(row) -> CompTitle:
    return CompTitle(
        id=row[0],
        title=row[1],
        author=row[2],
        asin=row[3],
        genre=row[4],
        added_date=date.fromisoformat(row[5]),
        notes=row[6],
        active=bool(row[7]),
    )


def _row_to_snapshot(row) -> BSRSnapshot:
    return BSRSnapshot(
        id=row[0],
        comp_id=row[1],
        snapshot_date=date.fromisoformat(row[2]),
        bsr=row[3],
        price=row[4],
        rating=row[5],
        reviews=row[6],
        kindle_unlimited=bool(row[7]),
    )


class CompTitleRepository:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def add(self, comp: CompTitle) -> CompTitle:
        cursor = self.conn.execute(
            "INSERT INTO comp_titles (title, author, asin, genre, added_date, notes, active) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (comp.title, comp.author, comp.asin, comp.genre,
             comp.added_date.isoformat(), comp.notes, int(comp.active)),
        )
        self.conn.commit()
        comp.id = cursor.lastrowid
        return comp

    def find_by_title(self, title: str) -> Optional[CompTitle]:
        row = self.conn.execute(
            "SELECT * FROM comp_titles WHERE title = ? COLLATE NOCASE", (title,)
        ).fetchone()
        return _row_to_comp(row) if row else None

    def find_by_asin(self, asin: str) -> Optional[CompTitle]:
        row = self.conn.execute(
            "SELECT * FROM comp_titles WHERE asin = ? COLLATE NOCASE", (asin,)
        ).fetchone()
        return _row_to_comp(row) if row else None

    def find_by_title_or_asin(self, identifier: str) -> Optional[CompTitle]:
        comp = self.find_by_asin(identifier)
        if comp:
            return comp
        return self.find_by_title(identifier)

    def list_all(self) -> list[CompTitle]:
        rows = self.conn.execute(
            "SELECT * FROM comp_titles ORDER BY title"
        ).fetchall()
        return [_row_to_comp(r) for r in rows]

    def list_active(self) -> list[CompTitle]:
        rows = self.conn.execute(
            "SELECT * FROM comp_titles WHERE active = 1 ORDER BY title"
        ).fetchall()
        return [_row_to_comp(r) for r in rows]

    def deactivate(self, comp_id: int) -> bool:
        cursor = self.conn.execute(
            "UPDATE comp_titles SET active = 0 WHERE id = ?", (comp_id,)
        )
        self.conn.commit()
        return cursor.rowcount > 0

    def delete(self, comp_id: int) -> bool:
        self.conn.execute("DELETE FROM bsr_snapshots WHERE comp_id = ?", (comp_id,))
        cursor = self.conn.execute("DELETE FROM comp_titles WHERE id = ?", (comp_id,))
        self.conn.commit()
        return cursor.rowcount > 0


class SnapshotRepository:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def add(self, snapshot: BSRSnapshot) -> BSRSnapshot:
        cursor = self.conn.execute(
            "INSERT INTO bsr_snapshots (comp_id, snapshot_date, bsr, price, rating, reviews, kindle_unlimited) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (snapshot.comp_id, snapshot.snapshot_date.isoformat(), snapshot.bsr,
             snapshot.price, snapshot.rating, snapshot.reviews,
             int(snapshot.kindle_unlimited)),
        )
        self.conn.commit()
        snapshot.id = cursor.lastrowid
        return snapshot

    def bulk_add(self, snapshots: list[BSRSnapshot]) -> list[BSRSnapshot]:
        result = []
        for s in snapshots:
            result.append(self.add(s))
        return result

    def get_history(self, comp_id: int, days: int = 90) -> list[BSRSnapshot]:
        cutoff = (date.today() - timedelta(days=days)).isoformat()
        rows = self.conn.execute(
            "SELECT * FROM bsr_snapshots WHERE comp_id = ? AND snapshot_date >= ? "
            "ORDER BY snapshot_date ASC",
            (comp_id, cutoff),
        ).fetchall()
        return [_row_to_snapshot(r) for r in rows]

    def get_latest(self, comp_id: int) -> Optional[BSRSnapshot]:
        row = self.conn.execute(
            "SELECT * FROM bsr_snapshots WHERE comp_id = ? ORDER BY snapshot_date DESC LIMIT 1",
            (comp_id,),
        ).fetchone()
        return _row_to_snapshot(row) if row else None

    def get_all_latest(self) -> dict[int, BSRSnapshot]:
        rows = self.conn.execute(
            "SELECT b.* FROM bsr_snapshots b "
            "INNER JOIN (SELECT comp_id, MAX(snapshot_date) as max_date FROM bsr_snapshots GROUP BY comp_id) g "
            "ON b.comp_id = g.comp_id AND b.snapshot_date = g.max_date"
        ).fetchall()
        return {r[1]: _row_to_snapshot(r) for r in rows}
