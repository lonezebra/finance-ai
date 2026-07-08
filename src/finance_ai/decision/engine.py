from finance_ai.decision.models import (
    DecisionPriority,
    DecisionSet,
    FinancialDecision,
    TimeHorizon,
)


def generate_decisions(snapshot) -> DecisionSet:
    decisions: list[FinancialDecision] = []

    if snapshot.emergency_fund_months < 3:
        decisions.append(
            FinancialDecision(
                title="Build emergency fund",
                description="Prioritize cash reserves until you have at least 3 months of expenses covered.",
                priority=DecisionPriority.CRITICAL,
                expected_impact_score=95,
                confidence_score=95,
                difficulty_score=0.8,
                time_horizon=TimeHorizon.SHORT_TERM,
                reasoning="Emergency fund coverage is below 3 months of expenses.",
            )
        )

    if snapshot.debt_to_income_ratio > 0.36:
        decisions.append(
            FinancialDecision(
                title="Reduce debt burden",
                description="Focus on lowering debt payments or balances to improve financial flexibility.",
                priority=DecisionPriority.HIGH,
                expected_impact_score=85,
                confidence_score=90,
                difficulty_score=0.7,
                time_horizon=TimeHorizon.SHORT_TERM,
                reasoning="Debt-to-income ratio is above the preferred threshold.",
            )
        )

    if snapshot.monthly_cash_flow < 0:
        decisions.append(
            FinancialDecision(
                title="Stabilize cash flow",
                description="Reduce expenses or increase income to return monthly cash flow to positive territory.",
                priority=DecisionPriority.CRITICAL,
                expected_impact_score=100,
                confidence_score=95,
                difficulty_score=0.7,
                time_horizon=TimeHorizon.IMMEDIATE,
                reasoning="Monthly cash flow is negative.",
            )
        )

    if (
        snapshot.monthly_cash_flow > 0
        and snapshot.emergency_fund_months >= 6
        and snapshot.debt_to_income_ratio <= 0.25
    ):
        decisions.append(
            FinancialDecision(
                title="Optimize capital allocation",
                description="Evaluate whether surplus cash should be directed toward debt payoff, investing, or specific goals.",
                priority=DecisionPriority.MEDIUM,
                expected_impact_score=75,
                confidence_score=85,
                difficulty_score=0.6,
                time_horizon=TimeHorizon.LONG_TERM,
                reasoning="Cash flow is positive, emergency reserves are strong, and debt levels are conservative.",
            )
        )

    if not decisions:
        decisions.append(
            FinancialDecision(
                title="Maintain current plan",
                description="Continue monitoring your financial position and keep your current plan in place.",
                priority=DecisionPriority.LOW,
                expected_impact_score=30,
                confidence_score=80,
                difficulty_score=1.0,
                time_horizon=TimeHorizon.SHORT_TERM,
                reasoning="No urgent decision surfaced from the current financial snapshot.",
            )
        )

    return DecisionSet(
        decisions=sorted(decisions, key=lambda decision: decision.score, reverse=True)
    )