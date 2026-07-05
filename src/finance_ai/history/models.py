from dataclasses import dataclass
from datetime import datetime
from sqlalchemy import Column, Date, DateTime, Float, ForeignKey, Integer, String
from finance_ai.finance.metrics import FinancialSnapshot


@dataclass(frozen=True)
class SnapshotRecord:
    id: int | None
    created_at: datetime
    snapshot: FinancialSnapshot


@dataclass(frozen=True)
class SnapshotDifference:
    metric: str
    previous: float
    current: float
    change: float
    percent_change: float


@dataclass(frozen=True)
class SnapshotComparison:
    previous: SnapshotRecord
    current: SnapshotRecord
    differences: list[SnapshotDifference]

