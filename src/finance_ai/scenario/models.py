from dataclasses import dataclass, field
from enum import Enum

from finance_ai.decision.models import DecisionSet
from finance_ai.finance.metrics import FinancialSnapshot
from finance_ai.history.models import SnapshotComparison


class AdjustmentType(str, Enum):
    INCOME_CHANGE = "income_change"
    RECURRING_EXPENSE_CHANGE = "recurring_expense_change"
    EXTRA_DEBT_PAYMENT = "extra_debt_payment"
    CONTRIBUTION_CHANGE = "contribution_change"
    ONE_TIME_PURCHASE = "one_time_purchase"
    ONE_TIME_WINDFALL = "one_time_windfall"


@dataclass(frozen=True)
class ScenarioAdjustment:
    type: AdjustmentType
    amount: float
    label: str


@dataclass(frozen=True)
class Scenario:
    name: str
    adjustments: list[ScenarioAdjustment] = field(default_factory=list)


@dataclass(frozen=True)
class ScenarioResult:
    scenario: Scenario
    baseline_snapshot: FinancialSnapshot
    projected_snapshot: FinancialSnapshot
    comparison: SnapshotComparison
    projected_decisions: DecisionSet
    scenario_facts: list[str] = field(default_factory=list)
