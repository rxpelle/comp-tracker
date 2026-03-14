from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Optional


class AlertType(Enum):
    DECLINING = "declining"
    STALE = "stale"
    SURGING = "surging"
    PRICE_CHANGE = "price_change"


class Severity(Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class CompTitle:
    title: str
    author: str
    asin: Optional[str] = None
    genre: Optional[str] = None
    added_date: Optional[date] = None
    notes: Optional[str] = None
    active: bool = True
    id: Optional[int] = None

    def __post_init__(self):
        if self.added_date is None:
            self.added_date = date.today()


@dataclass
class BSRSnapshot:
    comp_id: int
    snapshot_date: date
    bsr: int
    price: Optional[float] = None
    rating: Optional[float] = None
    reviews: Optional[int] = None
    kindle_unlimited: bool = False
    id: Optional[int] = None

    def __post_init__(self):
        if self.snapshot_date is None:
            self.snapshot_date = date.today()


@dataclass
class CompAlert:
    comp_title: str
    alert_type: AlertType
    message: str
    severity: Severity
    snapshot_date: date


@dataclass
class CompSuggestion:
    title: str
    author: str
    asin: Optional[str] = None
    genre: Optional[str] = None
    current_bsr: Optional[int] = None
    rating: Optional[float] = None
    reviews: Optional[int] = None
    relevance_score: float = 0.0
    reasoning: str = ""
