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

def test_every_compared_metric_is_classified_by_direction():
    """comparison.py maps snapshot fields to display labels, and interpreter.py decides
    better-when-increasing vs better-when-decreasing by matching those same label *strings*.
    A metric present in one and not the other silently falls through _direction()'s
    ChangeDirection.NEUTRAL fallback -- so a real regression (e.g. debt increasing but no
    longer reported as worsened) would produce no error, just wrong output.

    This guards the coupling: renaming a label or adding a metric must touch both sides.
    """

    from finance_ai.history.comparison import METRICS_TO_COMPARE
    from finance_ai.history.interpreter import IMPROVES_WHEN_DECREASED, IMPROVES_WHEN_INCREASED

    labels = set(METRICS_TO_COMPARE.values())
    classified = IMPROVES_WHEN_INCREASED | IMPROVES_WHEN_DECREASED

    assert labels - classified == set(), (
        "these compared metrics are not classified in interpreter.py and would be "
        f"silently reported as neutral: {sorted(labels - classified)}"
    )
    # And nothing is classified that isn't actually compared, which would be dead config.
    assert classified - labels == set(), (
        f"these classified labels no longer match any compared metric: {sorted(classified - labels)}"
    )


def test_a_metric_cannot_be_classified_in_both_directions():
    from finance_ai.history.interpreter import IMPROVES_WHEN_DECREASED, IMPROVES_WHEN_INCREASED

    assert IMPROVES_WHEN_INCREASED & IMPROVES_WHEN_DECREASED == set()
