import csv
import io
from datetime import date
from typing import Optional

import yaml

from comp_tracker.models import BSRSnapshot, CompTitle


def parse_comp_csv(text: str) -> list[CompTitle]:
    """Parse CSV text with columns: title, author, asin, genre."""
    reader = csv.DictReader(io.StringIO(text.strip()))
    comps = []
    for row in reader:
        comps.append(CompTitle(
            title=row['title'].strip(),
            author=row['author'].strip(),
            asin=row.get('asin', '').strip() or None,
            genre=row.get('genre', '').strip() or None,
        ))
    return comps


def parse_comp_yaml(path: str) -> list[CompTitle]:
    """Parse comp titles from a YAML file with a comp_titles list."""
    with open(path, 'r') as f:
        data = yaml.safe_load(f)

    comps = []
    for item in data.get('comp_titles', []):
        comps.append(CompTitle(
            title=item['title'].strip(),
            author=item['author'].strip(),
            asin=item.get('asin', '').strip() if item.get('asin') else None,
            genre=item.get('genre', '').strip() if item.get('genre') else None,
        ))
    return comps


def parse_bsr_snapshot_csv(text: str) -> list[tuple[str, BSRSnapshot]]:
    """Parse BSR snapshot CSV. Returns list of (asin_or_title, snapshot).

    CSV columns: asin_or_title, bsr, price, rating, reviews
    The comp_id will be 0 (placeholder) and must be resolved by the caller.
    """
    reader = csv.DictReader(io.StringIO(text.strip()))
    results = []
    for row in reader:
        identifier = row['asin_or_title'].strip()
        price = row.get('price', '').strip()
        rating = row.get('rating', '').strip()
        reviews = row.get('reviews', '').strip()

        snapshot = BSRSnapshot(
            comp_id=0,  # placeholder
            snapshot_date=date.today(),
            bsr=int(row['bsr'].strip()),
            price=float(price) if price else None,
            rating=float(rating) if rating else None,
            reviews=int(reviews) if reviews else None,
        )
        results.append((identifier, snapshot))
    return results
