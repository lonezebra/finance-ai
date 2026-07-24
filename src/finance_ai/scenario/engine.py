from datetime import datetime

from finance_ai.decision.engine import generate_decisions
from finance_ai.finance.metrics import FinancialSnapshot, create_financial_snapshot
from finance_ai.finance.summary import format_currency
from finance_ai.history.comparison import compare_snapshots
from finance_ai.history.models import SnapshotRecord
from finance_ai.scenario.models import AdjustmentType, Scenario, ScenarioAdjustment, ScenarioResult

# Income/expense adjustments change this month's flow rates (income, expenses, and the ratios
# derived from them) but are not compounded into point-in-time balances (cash, assets, debt) —
# that would require modeling accumulation over multiple months, which v1 does not attempt.
# Debt payment, purchase, windfall, and contribution adjustments are the opposite: they move
# money between balances immediately and leave this month's income/expenses untouched.


def _safe_divide(numerator: float, denominator: float) -> float:
    if denominator == 0:
        return 0.0
    return numerator / denominator


def apply_adjustments(
    baseline: FinancialSnapshot,
    adjustments: list[ScenarioAdjustment],
) -> tuple[FinancialSnapshot, list[str]]:
    total_assets = baseline.total_assets
    total_debt = baseline.total_debt
    cash_balance = baseline.cash_balance
    monthly_income = baseline.monthly_income
    monthly_expenses = baseline.monthly_expenses
    facts: list[str] = []

    for adjustment in adjustments:
        if adjustment.type == AdjustmentType.INCOME_CHANGE:
            monthly_income += adjustment.amount
            facts.append(
                f"{adjustment.label}: monthly income change of {format_currency(adjustment.amount)}"
            )

        elif adjustment.type == AdjustmentType.RECURRING_EXPENSE_CHANGE:
            monthly_expenses += adjustment.amount
            facts.append(
                f"{adjustment.label}: monthly expense change of {format_currency(adjustment.amount)}"
            )

        elif adjustment.type == AdjustmentType.EXTRA_DEBT_PAYMENT:
            cash_balance -= adjustment.amount
            total_assets -= adjustment.amount
            total_debt -= adjustment.amount
            facts.append(
                f"{adjustment.label}: extra debt payment of {format_currency(adjustment.amount)}"
            )

        elif adjustment.type == AdjustmentType.CONTRIBUTION_CHANGE:
            cash_balance -= adjustment.amount
            facts.append(
                f"{adjustment.label}: savings/investment contribution of "
                f"{format_currency(adjustment.amount)}"
            )

        elif adjustment.type == AdjustmentType.ONE_TIME_PURCHASE:
            cash_balance -= adjustment.amount
            total_assets -= adjustment.amount
            facts.append(
                f"{adjustment.label}: one-time purchase of {format_currency(adjustment.amount)}"
            )

        elif adjustment.type == AdjustmentType.ONE_TIME_WINDFALL:
            cash_balance += adjustment.amount
            total_assets += adjustment.amount
            facts.append(
                f"{adjustment.label}: one-time windfall of {format_currency(adjustment.amount)}"
            )

    monthly_cash_flow = monthly_income - monthly_expenses
    savings_rate = _safe_divide(monthly_cash_flow, monthly_income)

    monthly_debt_payments = baseline.debt_to_income_ratio * baseline.monthly_income
    debt_to_income_ratio = _safe_divide(monthly_debt_payments, monthly_income)

    emergency_fund_months = _safe_divide(cash_balance, monthly_expenses)

    projected = FinancialSnapshot(
        month=baseline.month,
        total_assets=total_assets,
        total_debt=total_debt,
        net_worth=total_assets - total_debt,
        cash_balance=cash_balance,
        monthly_income=monthly_income,
        monthly_expenses=monthly_expenses,
        monthly_cash_flow=monthly_cash_flow,
        savings_rate=savings_rate,
        debt_to_income_ratio=debt_to_income_ratio,
        emergency_fund_months=emergency_fund_months,
    )

    return projected, facts


def run_scenario(month: str, scenario: Scenario) -> ScenarioResult:
    baseline = create_financial_snapshot(month)
    projected, facts = apply_adjustments(baseline, scenario.adjustments)

    baseline_record = SnapshotRecord(id=None, created_at=datetime.now(), snapshot=baseline)
    projected_record = SnapshotRecord(id=None, created_at=datetime.now(), snapshot=projected)
    comparison = compare_snapshots(baseline_record, projected_record)

    projected_decisions = generate_decisions(projected)

    return ScenarioResult(
        scenario=scenario,
        baseline_snapshot=baseline,
        projected_snapshot=projected,
        comparison=comparison,
        projected_decisions=projected_decisions,
        scenario_facts=facts,
    )
