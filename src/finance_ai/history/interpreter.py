from dataclasses import dataclass
from enum import Enum

from finance_ai.history.models import SnapshotComparison, SnapshotDifference


class ChangeDirection(str, Enum):
    IMPROVED = "improved"
    WORSENED = "worsened"
    NEUTRAL = "neutral"


class ChangeSignificance(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass(frozen=True)
class InterpretedChange:
    metric: str
    previous: float
    current: float
    change: float
    percent_change: float
    direction: ChangeDirection
    significance: ChangeSignificance


IMPROVES_WHEN_INCREASED = {
    "Total Assets",
    "Net Worth",
    "Cash Balance",
    "Monthly Income",
    "Monthly Cash Flow",
    "Savings Rate",
    "Emergency Fund Months",
}

IMPROVES_WHEN_DECREASED = {
    "Total Debt",
    "Monthly Expenses",
    "Debt-to-Income Ratio",
}


def interpret_comparison(comparison: SnapshotComparison) -> list[InterpretedChange]:
    return [interpret_difference(diff) for diff in comparison.differences]


def interpret_difference(diff: SnapshotDifference) -> InterpretedChange:
    return InterpretedChange(
        metric=diff.metric,
        previous=diff.previous,
        current=diff.current,
        change=diff.change,
        percent_change=diff.percent_change,
        direction=_direction(diff),
        significance=_significance(diff),
    )


def _direction(diff: SnapshotDifference) -> ChangeDirection:
    if diff.change == 0:
        return ChangeDirection.NEUTRAL

    if diff.metric in IMPROVES_WHEN_INCREASED:
        return ChangeDirection.IMPROVED if diff.change > 0 else ChangeDirection.WORSENED

    if diff.metric in IMPROVES_WHEN_DECREASED:
        return ChangeDirection.IMPROVED if diff.change < 0 else ChangeDirection.WORSENED

    return ChangeDirection.NEUTRAL


def _significance(diff: SnapshotDifference) -> ChangeSignificance:
    abs_percent = abs(diff.percent_change)

    if abs_percent >= 0.10:
        return ChangeSignificance.HIGH

    if abs_percent >= 0.03:
        return ChangeSignificance.MEDIUM

    return ChangeSignificance.LOW