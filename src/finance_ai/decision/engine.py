from datetime import date

from finance_ai.db.database import SessionLocal
from finance_ai.db.models import Debt, Goal
from finance_ai.decision.models import (
    DebtSummary,
    DecisionPriority,
    DecisionSet,
    FinancialDecision,
    GoalSummary,
    TimeHorizon,
)
from finance_ai.finance.summary import format_currency, format_months
from finance_ai.finance.thresholds import DTI_CONSERVATIVE, DTI_ELEVATED

EMERGENCY_FUND_TARGET_MONTHS = 3
# Horizon over which we suggest closing an emergency-fund gap. Chosen as a pace that's
# aggressive but achievable for most households, not derived from user data.
EMERGENCY_FUND_CONTRIBUTION_HORIZON_MONTHS = 6

# Interest rates are stored as whole-number percentages (e.g. 24.99), not fractions.
# Debts at or above this rate are treated as "high interest" (roughly typical credit-card
# territory) for priority purposes.
HIGH_INTEREST_RATE_THRESHOLD = 15.0
# Reference ceiling used to scale a debt's payoff impact score to 0-100. 30% approximates the
# top of typical consumer credit card APRs.
DEBT_PAYOFF_RATE_CEILING = 30.0


def get_debt_summaries(session) -> list[DebtSummary]:
    return [
        DebtSummary(
            name=debt.name,
            balance=debt.balance,
            interest_rate=debt.interest_rate,
            minimum_payment=debt.minimum_payment,
        )
        for debt in session.query(Debt).all()
    ]


def get_goal_summaries(session) -> list[GoalSummary]:
    return [
        GoalSummary(
            name=goal.name,
            target_amount=goal.target_amount,
            current_amount=goal.current_amount,
            target_date=goal.target_date,
        )
        for goal in session.query(Goal).all()
    ]


def generate_decisions_from_db(snapshot) -> DecisionSet:
    with SessionLocal() as session:
        debts = get_debt_summaries(session)
        goals = get_goal_summaries(session)

    return generate_decisions(snapshot, debts=debts, goals=goals)


def generate_decisions(
    snapshot,
    debts: list[DebtSummary] | None = None,
    goals: list[GoalSummary] | None = None,
) -> DecisionSet:
    debts = debts or []
    goals = goals or []
    decisions: list[FinancialDecision] = []

    if snapshot.emergency_fund_months < EMERGENCY_FUND_TARGET_MONTHS:
        decisions.append(_emergency_fund_decision(snapshot))

    if snapshot.debt_to_income_ratio > DTI_ELEVATED:
        decisions.append(
            FinancialDecision(
                title="Reduce debt burden",
                description="Focus on lowering debt payments or balances to improve financial flexibility.",
                priority=DecisionPriority.HIGH,
                expected_impact_score=85,
                confidence_score=90,
                ease_multiplier=0.7,
                time_horizon=TimeHorizon.SHORT_TERM,
                reasoning=(
                    f"Debt payments are above {DTI_ELEVATED:.0%} of take-home income."
                ),
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
                ease_multiplier=0.7,
                time_horizon=TimeHorizon.IMMEDIATE,
                reasoning="Monthly cash flow is negative.",
            )
        )

    if (
        snapshot.monthly_cash_flow > 0
        and snapshot.emergency_fund_months >= 6
        and snapshot.debt_to_income_ratio <= DTI_CONSERVATIVE
    ):
        decisions.append(_capital_allocation_decision(snapshot))

    decisions.extend(_debt_payoff_decisions(snapshot, debts))
    decisions.extend(_goal_funding_decisions(snapshot, goals))

    if not decisions:
        decisions.append(
            FinancialDecision(
                title="Maintain current plan",
                description="Continue monitoring your financial position and keep your current plan in place.",
                priority=DecisionPriority.LOW,
                expected_impact_score=30,
                confidence_score=80,
                ease_multiplier=1.0,
                time_horizon=TimeHorizon.SHORT_TERM,
                reasoning="No urgent decision surfaced from the current financial snapshot.",
            )
        )

    return DecisionSet(
        decisions=sorted(decisions, key=lambda decision: decision.score, reverse=True)
    )


def _emergency_fund_decision(snapshot) -> FinancialDecision:
    gap = max(
        EMERGENCY_FUND_TARGET_MONTHS * snapshot.monthly_expenses - snapshot.cash_balance,
        0,
    )
    suggested_monthly = gap / EMERGENCY_FUND_CONTRIBUTION_HORIZON_MONTHS

    return FinancialDecision(
        title="Build emergency fund",
        description=(
            f"Prioritize cash reserves until you have at least {EMERGENCY_FUND_TARGET_MONTHS} "
            f"months of expenses covered. Contributing {format_currency(suggested_monthly)}/month "
            f"would close the {format_currency(gap)} gap in about "
            f"{EMERGENCY_FUND_CONTRIBUTION_HORIZON_MONTHS} months."
        ),
        priority=DecisionPriority.CRITICAL,
        expected_impact_score=95,
        confidence_score=95,
        ease_multiplier=0.8,
        time_horizon=TimeHorizon.SHORT_TERM,
        reasoning=(
            f"Emergency fund coverage is {format_months(snapshot.emergency_fund_months)}, below "
            f"the {EMERGENCY_FUND_TARGET_MONTHS}-month target."
        ),
    )


def _capital_allocation_decision(snapshot) -> FinancialDecision:
    return FinancialDecision(
        title="Optimize capital allocation",
        description=(
            f"You have {format_currency(snapshot.monthly_cash_flow)}/month in surplus cash flow "
            "beyond your emergency fund and debt targets. Consider directing it toward "
            "investments, additional debt payoff, or specific goals based on your priorities."
        ),
        priority=DecisionPriority.MEDIUM,
        expected_impact_score=75,
        confidence_score=85,
        ease_multiplier=0.6,
        time_horizon=TimeHorizon.LONG_TERM,
        reasoning="Cash flow is positive, emergency reserves are strong, and debt levels are conservative.",
    )


def _debt_payoff_decisions(snapshot, debts: list[DebtSummary]) -> list[FinancialDecision]:
    if snapshot.monthly_cash_flow <= 0:
        return []

    decisions = []

    for debt in debts:
        if debt.interest_rate is None or debt.balance <= 0:
            continue

        annual_cost = debt.balance * (debt.interest_rate / 100)
        impact = min(100, round(debt.interest_rate / DEBT_PAYOFF_RATE_CEILING * 100))
        high_interest = debt.interest_rate >= HIGH_INTEREST_RATE_THRESHOLD

        decisions.append(
            FinancialDecision(
                title=f"Pay down {debt.name}",
                description=(
                    f"Direct extra payments toward {debt.name} ahead of lower-interest debts. "
                    f"At {debt.interest_rate:.2f}% APR on a {format_currency(debt.balance)} "
                    f"balance, it costs about {format_currency(annual_cost)} per year in interest."
                ),
                priority=DecisionPriority.HIGH if high_interest else DecisionPriority.MEDIUM,
                expected_impact_score=impact,
                confidence_score=95,
                ease_multiplier=0.7,
                time_horizon=TimeHorizon.SHORT_TERM,
                reasoning=(
                    f"{debt.name} carries a {debt.interest_rate:.2f}% interest rate, the basis "
                    "for prioritizing it under an avalanche (highest-rate-first) payoff strategy."
                ),
            )
        )

    return decisions


def _goal_funding_decisions(
    snapshot,
    goals: list[GoalSummary],
    today: date | None = None,
) -> list[FinancialDecision]:
    today = today or date.today()
    decisions = []

    for goal in goals:
        if goal.target_amount is None or goal.target_date is None:
            continue

        current_amount = goal.current_amount or 0.0
        remaining = goal.target_amount - current_amount

        if remaining <= 0:
            continue

        months_remaining = max(
            (goal.target_date.year - today.year) * 12 + (goal.target_date.month - today.month),
            1,
        )
        required_monthly = remaining / months_remaining
        available = max(snapshot.monthly_cash_flow, 0)
        feasible = required_monthly <= available
        time_horizon = TimeHorizon.SHORT_TERM if months_remaining <= 6 else TimeHorizon.LONG_TERM

        if feasible:
            decisions.append(
                FinancialDecision(
                    title=f"Fund goal: {goal.name}",
                    description=(
                        f"Contribute {format_currency(required_monthly)}/month toward {goal.name} "
                        f"to reach {format_currency(goal.target_amount)} by "
                        f"{goal.target_date.isoformat()}."
                    ),
                    priority=DecisionPriority.MEDIUM,
                    expected_impact_score=60,
                    confidence_score=85,
                    ease_multiplier=1.0,
                    time_horizon=time_horizon,
                    reasoning=(
                        f"{format_currency(remaining)} remains for {goal.name} with "
                        f"{months_remaining} months until the target date, and current cash flow "
                        "can support the required contribution."
                    ),
                )
            )
        else:
            decisions.append(
                FinancialDecision(
                    title=f"Fund goal: {goal.name} (at risk)",
                    description=(
                        f"{goal.name} needs {format_currency(required_monthly)}/month to reach "
                        f"{format_currency(goal.target_amount)} by {goal.target_date.isoformat()}, "
                        f"more than the {format_currency(available)}/month currently available."
                    ),
                    priority=DecisionPriority.MEDIUM,
                    expected_impact_score=80,
                    confidence_score=85,
                    ease_multiplier=0.5,
                    time_horizon=time_horizon,
                    reasoning=(
                        "Required contribution exceeds available monthly cash flow, so this goal "
                        "is off track unless the target amount, target date, or cash flow changes."
                    ),
                )
            )

    return decisions
