from dataclasses import dataclass, field

from finance_ai.finance.confidence import FinancialConfidenceScore, calculate_financial_confidence_score
from finance_ai.finance.metrics import FinancialSnapshot, create_financial_snapshot


@dataclass(frozen=True)
class ActionItem:
    priority: str
    title: str
    reason: str


@dataclass(frozen=True)
class OpenCFOBriefing:
    snapshot: FinancialSnapshot
    confidence: FinancialConfidenceScore
    action_items: list[ActionItem] = field(default_factory=list)

    @property
    def headline(self) -> str:
        if self.confidence.score < 50:
            return "Your data needs attention before Open CFO can give strong recommendations."

        if self.snapshot.monthly_cash_flow < 0:
            return "Your current snapshot shows negative monthly cash flow."

        if self.snapshot.emergency_fund_months < 3:
            return "Your emergency fund appears below the recommended minimum."

        return "Your financial snapshot appears stable based on current data."


def generate_action_items(
    snapshot: FinancialSnapshot,
    confidence: FinancialConfidenceScore,
) -> list[ActionItem]:
    action_items: list[ActionItem] = []

    if confidence.score < 70:
        action_items.append(
            ActionItem(
                priority="high",
                title="Improve data quality",
                reason="Open CFO needs more complete data before making high-confidence recommendations.",
            )
        )

    if snapshot.monthly_cash_flow < 0:
        action_items.append(
            ActionItem(
                priority="high",
                title="Review monthly spending",
                reason="Monthly expenses are higher than monthly income.",
            )
        )

    if snapshot.emergency_fund_months < 3:
        action_items.append(
            ActionItem(
                priority="high",
                title="Build emergency fund",
                reason="Cash reserves appear below 3 months of expenses.",
            )
        )
    elif snapshot.emergency_fund_months < 6:
        action_items.append(
            ActionItem(
                priority="medium",
                title="Continue building emergency fund",
                reason="Emergency fund is below the preferred 6-month target.",
            )
        )

    if snapshot.debt_to_income_ratio > 0.36:
        action_items.append(
            ActionItem(
                priority="medium",
                title="Review debt payments",
                reason="Debt-to-income ratio is above a conservative threshold.",
            )
        )

    if snapshot.savings_rate < 0.10 and snapshot.monthly_income > 0:
        action_items.append(
            ActionItem(
                priority="medium",
                title="Increase savings rate",
                reason="Savings rate is below 10% of monthly income.",
            )
        )

    if not action_items:
        action_items.append(
            ActionItem(
                priority="low",
                title="Maintain current plan",
                reason="No urgent issues were detected from the current snapshot.",
            )
        )

    return action_items


def create_open_cfo_briefing(month: str) -> OpenCFOBriefing:
    snapshot = create_financial_snapshot(month)
    confidence = calculate_financial_confidence_score()
    action_items = generate_action_items(snapshot, confidence)

    return OpenCFOBriefing(
        snapshot=snapshot,
        confidence=confidence,
        action_items=action_items,
    )