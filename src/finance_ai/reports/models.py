from dataclasses import dataclass, field

from finance_ai.finance.metrics import FinancialSnapshot
from finance_ai.history.interpreter import InterpretedChange


@dataclass(frozen=True)
class ExecutiveReport:
    month: str
    snapshot: FinancialSnapshot
    important_changes: list[InterpretedChange] = field(default_factory=list)
    strengths: list[str] = field(default_factory=list)
    concerns: list[str] = field(default_factory=list)
    recommended_focus: str | None = None