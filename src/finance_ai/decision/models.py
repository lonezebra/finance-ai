from dataclasses import dataclass
from datetime import date
from enum import Enum

from finance_ai.decision.scoring import decision_score


class DecisionPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TimeHorizon(str, Enum):
    IMMEDIATE = "immediate"
    SHORT_TERM = "short_term"
    LONG_TERM = "long_term"


@dataclass(frozen=True)
class FinancialDecision:
    title: str
    description: str

    priority: DecisionPriority

    expected_impact_score: float
    confidence_score: float

    # How easy this decision is to actually carry out, as a multiplier: 1.0 is
    # frictionless, lower values mean more effort or disruption. Previously named
    # difficulty_score, which read backwards -- a *higher* value makes a decision rank
    # *higher*, so the number was always measuring ease, not difficulty.
    ease_multiplier: float

    time_horizon: TimeHorizon

    reasoning: str

    reversible: bool = True

    @property
    def score(self) -> float:
        return decision_score(
            self.expected_impact_score,
            self.confidence_score,
            self.ease_multiplier,
        )

@dataclass(frozen=True)
class DecisionSet:
    decisions: list[FinancialDecision]


@dataclass(frozen=True)
class DebtSummary:
    name: str
    balance: float
    interest_rate: float | None
    minimum_payment: float | None = None


@dataclass(frozen=True)
class GoalSummary:
    name: str
    target_amount: float | None
    current_amount: float | None
    target_date: date | None