from datetime import datetime

from finance_ai.finance.metrics import FinancialSnapshot
from finance_ai.history.comparison import compare_snapshots
from finance_ai.history.interpreter import (
    ChangeDirection,
    ChangeSignificance,
    interpret_comparison,
)
from finance_ai.history.models import SnapshotRecord


def make_snapshot_record(
    *,
    record_id: int,
    month: str,
    total_assets: float,
    total_debt: float,
    net_worth: float,
    cash_balance: float,
    monthly_income: float,
    monthly_expenses: float,
    monthly_cash_flow: float,
    savings_rate: float,
    debt_to_income_ratio: float,
    emergency_fund_months: float,
) -> SnapshotRecord:
    return SnapshotRecord(
        id=record_id,
        created_at=datetime.now(),
        snapshot=FinancialSnapshot(
            month=month,
            total_assets=total_assets,
            total_debt=total_debt,
            net_worth=net_worth,
            cash_balance=cash_balance,
            monthly_income=monthly_income,
            monthly_expenses=monthly_expenses,
            monthly_cash_flow=monthly_cash_flow,
            savings_rate=savings_rate,
            debt_to_income_ratio=debt_to_income_ratio,
            emergency_fund_months=emergency_fund_months,
        ),
    )


def test_compare_snapshots_detects_changed_metrics():
    previous = make_snapshot_record(
        record_id=1,
        month="2026-06",
        total_assets=600000,
        total_debt=30000,
        net_worth=570000,
        cash_balance=10000,
        monthly_income=5000,
        monthly_expenses=3000,
        monthly_cash_flow=2000,
        savings_rate=0.40,
        debt_to_income_ratio=0.20,
        emergency_fund_months=3.33,
    )

    current = make_snapshot_record(
        record_id=2,
        month="2026-07",
        total_assets=620000,
        total_debt=28000,
        net_worth=592000,
        cash_balance=12000,
        monthly_income=5000,
        monthly_expenses=2800,
        monthly_cash_flow=2200,
        savings_rate=0.44,
        debt_to_income_ratio=0.18,
        emergency_fund_months=4.28,
    )

    comparison = compare_snapshots(previous, current)

    metrics = [diff.metric for diff in comparison.differences]

    assert "Net Worth" in metrics
    assert "Total Debt" in metrics
    assert "Monthly Income" not in metrics


def test_interpreter_marks_debt_decrease_as_improved():
    previous = make_snapshot_record(
        record_id=1,
        month="2026-06",
        total_assets=600000,
        total_debt=30000,
        net_worth=570000,
        cash_balance=10000,
        monthly_income=5000,
        monthly_expenses=3000,
        monthly_cash_flow=2000,
        savings_rate=0.40,
        debt_to_income_ratio=0.20,
        emergency_fund_months=3.33,
    )

    current = make_snapshot_record(
        record_id=2,
        month="2026-07",
        total_assets=620000,
        total_debt=28000,
        net_worth=592000,
        cash_balance=12000,
        monthly_income=5000,
        monthly_expenses=2800,
        monthly_cash_flow=2200,
        savings_rate=0.44,
        debt_to_income_ratio=0.18,
        emergency_fund_months=4.28,
    )

    comparison = compare_snapshots(previous, current)
    interpreted = interpret_comparison(comparison)

    debt_change = next(change for change in interpreted if change.metric == "Total Debt")

    assert debt_change.direction == ChangeDirection.IMPROVED
    assert debt_change.significance == ChangeSignificance.MEDIUM


def test_interpreter_marks_cash_balance_large_increase_as_high_significance():
    previous = make_snapshot_record(
        record_id=1,
        month="2026-06",
        total_assets=600000,
        total_debt=30000,
        net_worth=570000,
        cash_balance=10000,
        monthly_income=5000,
        monthly_expenses=3000,
        monthly_cash_flow=2000,
        savings_rate=0.40,
        debt_to_income_ratio=0.20,
        emergency_fund_months=3.33,
    )

    current = make_snapshot_record(
        record_id=2,
        month="2026-07",
        total_assets=620000,
        total_debt=28000,
        net_worth=592000,
        cash_balance=12000,
        monthly_income=5000,
        monthly_expenses=2800,
        monthly_cash_flow=2200,
        savings_rate=0.44,
        debt_to_income_ratio=0.18,
        emergency_fund_months=4.28,
    )

    comparison = compare_snapshots(previous, current)
    interpreted = interpret_comparison(comparison)

    cash_change = next(change for change in interpreted if change.metric == "Cash Balance")

    assert cash_change.direction == ChangeDirection.IMPROVED
    assert cash_change.significance == ChangeSignificance.HIGH