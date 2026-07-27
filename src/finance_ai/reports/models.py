from dataclasses import dataclass, field

from finance_ai.decision.models import FinancialDecision
from finance_ai.finance.confidence import FinancialConfidenceScore
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
    top_decisions: list[FinancialDecision] = field(default_factory=list)
    # Measures data completeness/trustworthiness, not wealth -- defaults to a clean score so
    # existing call sites that don't pass one explicitly (e.g. tests) aren't implying a data
    # problem that was never assessed.
    confidence: FinancialConfidenceScore = field(
        default_factory=lambda: FinancialConfidenceScore(score=100)
    )