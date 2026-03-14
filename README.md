# Comp Title Decay Tracker

Monitor comp title BSR over time, detect when comps lose relevance, and surface replacement suggestions.

## Features

- **Track comp titles** — add books you're competing against with ASIN, genre, notes
- **Record BSR snapshots** — log BSR, price, rating, reviews over time
- **Trend analysis** — rising, falling, or stable with percentage change
- **Smart alerts** — declining relevance, stale data, surging comps, price changes
- **Relevance scoring** — 0-100 score based on BSR, review velocity, tracking history
- **Bulk import** — CSV or YAML import for comps and snapshots
- **SQLite storage** — all data stored locally, no API keys needed

## Installation

```bash
pip install -e .
```

## Quick Start

```bash
# Add a comp title
comp-tracker add "The Silent Patient" --author "Alex Michaelides" --asin B07HKGJN9C --genre "Thriller"

# Bulk import from CSV
comp-tracker import comps.csv

# Record a BSR snapshot
comp-tracker record "The Silent Patient" --bsr 523 --price 12.99 --rating 4.5 --reviews 95000

# Bulk record snapshots
comp-tracker record-bulk snapshots.csv

# View all tracked comps
comp-tracker list

# Analyze trend for one comp
comp-tracker analyze "The Silent Patient" --days 30

# Full dashboard with alerts
comp-tracker dashboard

# View alerts only
comp-tracker alerts

# View BSR history
comp-tracker history "The Silent Patient" --days 90

# Deactivate a comp
comp-tracker deactivate "The Silent Patient"

# Delete a comp permanently
comp-tracker delete "The Silent Patient" --confirm
```

## CSV Formats

### Comp titles (for `import`):

```csv
title,author,asin,genre
The Silent Patient,Alex Michaelides,B07HKGJN9C,Thriller
Gone Girl,Gillian Flynn,B006LSZECO,Thriller
```

### BSR snapshots (for `record-bulk`):

```csv
asin_or_title,bsr,price,rating,reviews
B07HKGJN9C,523,12.99,4.5,95000
Gone Girl,2150,11.99,4.1,120000
```

## YAML Format (for `import`):

```yaml
comp_titles:
  - title: The Silent Patient
    author: Alex Michaelides
    asin: B07HKGJN9C
    genre: Thriller
```

## License

MIT
