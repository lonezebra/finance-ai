from datetime import datetime

from finance_ai.decision.engine import generate_decisions
from finance_ai.finance.metrics import FinancialSnapshot
from finance_ai.history.comparison import compare_snapshots
from finance_ai.history.models import SnapshotRecord
from finance_ai.scenario.formatter import format_scenario_for_ai
from finance_ai.scenario.models import AdjustmentType, Scenario, ScenarioAdjustment, ScenarioResult


def make_snapshot(**overrides) -> FinancialSnapshot:
    defaults = {
        "month": "2026-06",
        "total_assets": 600000,
        "total_debt": 25000,
        "net_worth": 575000,
        "cash_balance": 50000,
        "monthly_income": 7000,
        "monthly_expenses": 3000,
        "monthly_cash_flow": 4000,
        "savings_rate": 4000 / 7000,
        "debt_to_income_ratio": 500 / 7000,
        "emergency_fund_months": 50000 / 3000,
    }
    defaults.update(overrides)
    return FinancialSnapshot(**defaults)


def make_result(**projected_overrides) -> ScenarioResult:
    baseline = make_snapshot()
    projected = make_snapshot(**projected_overrides)

    baseline_record = SnapshotRecord(id=None, created_at=datetime.now(), snapshot=baseline)
    projected_record = SnapshotRecord(id=None, created_at=datetime.now(), snapshot=projected)
    comparison = compare_snapshots(baseline_record, projected_record)

    scenario = Scenario(
        name="Test Scenario",
        adjustments=[
            ScenarioAdjustment(type=AdjustmentType.ONE_TIME_WINDFALL, amount=10000, label="Bonus")
        ],
    )

    return ScenarioResult(
        scenario=scenario,
        baseline_snapshot=baseline,
        projected_snapshot=projected,
        comparison=comparison,
        projected_decisions=generate_decisions(projected),
        scenario_facts=["Bonus: one-time windfall of $10,000.00"],
    )


def test_formatter_includes_scenario_name_and_facts():
    result = make_result(cash_balance=60000, total_assets=610000, net_worth=585000)

    output = format_scenario_for_ai(result)

    assert "Scenario: Test Scenario" in output
    assert "Bonus: one-time windfall of $10,000.00" in output


def test_formatter_lists_projected_changes():
    result = make_result(cash_balance=60000, total_assets=610000, net_worth=585000)

    output = format_scenario_for_ai(result)

    assert "Net Worth: improved" in output
    assert "575,000.00 -> 585,000.00" in output


def test_formatter_shows_projected_snapshot_values():
    result = make_result(cash_balance=60000, total_assets=610000, net_worth=585000)

    output = format_scenario_for_ai(result)

    assert "Net Worth: $585,000.00" in output
    assert "Cash Balance: $60,000.00" in output


def test_formatter_handles_no_changes():
    result = make_result()

    output = format_scenario_for_ai(result)

    assert "No metrics change under this scenario." in output


def test_formatter_lists_projected_decisions_with_reasoning():
    result = make_result(cash_balance=60000, total_assets=610000, net_worth=585000)

    output = format_scenario_for_ai(result)

    assert "Projected Top Decisions:" in output
    assert "Reasoning:" in output
