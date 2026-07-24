from dataclasses import dataclass
from datetime import date
from enum import Enum

#from finance_ai.decision.scoring import decision_score


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

    difficulty_score: float

    time_horizon: TimeHorizon

    reasoning: str

    reversible: bool = True

    @property
    def score(self) -> float:
        from finance_ai.decision.scoring import decision_score

        return decision_score(self)

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