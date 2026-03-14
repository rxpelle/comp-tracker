import os
from pathlib import Path


class Config:
    DB_PATH: str = os.environ.get(
        'COMP_TRACKER_DB',
        str(Path.home() / '.comp-tracker' / 'comps.db')
    )
    ALERT_DECLINE_THRESHOLD: int = 50   # BSR rose >50% = declining
    ALERT_SURGE_THRESHOLD: int = 30     # BSR dropped >30% = surging
    STALE_DAYS: int = 14                # No snapshot in 14+ days = stale
    DEFAULT_ANALYSIS_DAYS: int = 30
    DEFAULT_HISTORY_DAYS: int = 90
    RELEVANCE_THRESHOLD: float = 40.0   # Below this = flagged
