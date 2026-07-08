from finance_ai.decision.engine import generate_decisions
from finance_ai.finance.metrics import FinancialSnapshot


def test_decision_engine_recommends_emergency_fund_when_low():
    snapshot = FinancialSnapshot(
        month="2026-06",
        total_assets=1000,
        total_debt=0,
        net_worth=1000,
        cash_balance=1000,
        monthly_income=5000,
        monthly_expenses=4000,
        monthly_cash_flow=1000,
        savings_rate=0.20,
        debt_to_income_ratio=0.0,
        emergency_fund_months=0.25,
    )

    decisions = generate_decisions(snapshot)

    assert decisions.decisions[0].title == "Build emergency fund"


def test_decision_engine_recommends_capital_allocation_when_stable():
    snapshot = FinancialSnapshot(
        month="2026-06",
        total_assets=600000,
        total_debt=25000,
        net_worth=575000,
        cash_balance=50000,
        monthly_income=7000,
        monthly_expenses=3000,
        monthly_cash_flow=4000,
        savings_rate=0.57,
        debt_to_income_ratio=0.20,
        emergency_fund_months=16.67,
    )

    decisions = generate_decisions(snapshot)

    assert decisions.decisions[0].title == "Optimize capital allocation"