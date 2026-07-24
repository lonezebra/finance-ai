from finance_ai.finance.metrics import FinancialSnapshot
from finance_ai.scenario.engine import apply_adjustments
from finance_ai.scenario.models import AdjustmentType, ScenarioAdjustment


def make_snapshot() -> FinancialSnapshot:
    return FinancialSnapshot(
        month="2026-06",
        total_assets=600000,
        total_debt=25000,
        net_worth=575000,
        cash_balance=50000,
        monthly_income=7000,
        monthly_expenses=3000,
        monthly_cash_flow=4000,
        savings_rate=4000 / 7000,
        debt_to_income_ratio=500 / 7000,
        emergency_fund_months=50000 / 3000,
    )


def test_income_change_updates_flow_metrics_but_not_balances():
    baseline = make_snapshot()
    adjustment = ScenarioAdjustment(
        type=AdjustmentType.INCOME_CHANGE, amount=1000, label="Raise"
    )

    projected, facts = apply_adjustments(baseline, [adjustment])

    assert projected.monthly_income == 8000
    assert projected.monthly_cash_flow == 5000
    assert projected.cash_balance == baseline.cash_balance
    assert projected.total_assets == baseline.total_assets
    assert "Raise" in facts[0]


def test_extra_debt_payment_reduces_debt_and_cash_but_not_net_worth():
    baseline = make_snapshot()
    adjustment = ScenarioAdjustment(
        type=AdjustmentType.EXTRA_DEBT_PAYMENT, amount=5000, label="Payoff credit card"
    )

    projected, _ = apply_adjustments(baseline, [adjustment])

    assert projected.total_debt == 20000
    assert projected.cash_balance == 45000
    assert projected.net_worth == baseline.net_worth
    assert projected.debt_to_income_ratio == baseline.debt_to_income_ratio


def test_one_time_windfall_increases_cash_assets_and_net_worth():
    baseline = make_snapshot()
    adjustment = ScenarioAdjustment(
        type=AdjustmentType.ONE_TIME_WINDFALL, amount=10000, label="Bonus"
    )

    projected, _ = apply_adjustments(baseline, [adjustment])

    assert projected.cash_balance == 60000
    assert projected.total_assets == 610000
    assert projected.net_worth == baseline.net_worth + 10000


def test_contribution_change_reduces_cash_without_changing_net_worth():
    baseline = make_snapshot()
    adjustment = ScenarioAdjustment(
        type=AdjustmentType.CONTRIBUTION_CHANGE, amount=2000, label="Increase 401k contribution"
    )

    projected, _ = apply_adjustments(baseline, [adjustment])

    assert projected.cash_balance == 48000
    assert projected.total_assets == baseline.total_assets
    assert projected.net_worth == baseline.net_worth


def test_stacked_adjustments_apply_in_sequence():
    baseline = make_snapshot()
    adjustments = [
        ScenarioAdjustment(type=AdjustmentType.INCOME_CHANGE, amount=500, label="Side income"),
        ScenarioAdjustment(
            type=AdjustmentType.EXTRA_DEBT_PAYMENT, amount=3000, label="Extra payment"
        ),
        ScenarioAdjustment(
            type=AdjustmentType.ONE_TIME_PURCHASE, amount=1000, label="New laptop"
        ),
    ]

    projected, facts = apply_adjustments(baseline, adjustments)

    assert projected.monthly_income == 7500
    assert projected.total_debt == 22000
    assert projected.cash_balance == 50000 - 3000 - 1000
    assert len(facts) == 3


def test_emergency_fund_months_recalculated_after_expense_change():
    baseline = make_snapshot()
    adjustment = ScenarioAdjustment(
        type=AdjustmentType.RECURRING_EXPENSE_CHANGE, amount=-1000, label="Cut subscriptions"
    )

    projected, _ = apply_adjustments(baseline, [adjustment])

    assert projected.monthly_expenses == 2000
    assert projected.emergency_fund_months == 25.0
