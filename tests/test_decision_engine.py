from datetime import date

from finance_ai.decision.engine import _goal_funding_decisions, generate_decisions
from finance_ai.decision.models import DebtSummary, GoalSummary
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


def make_stable_snapshot() -> FinancialSnapshot:
    return FinancialSnapshot(
        month="2026-06",
        total_assets=600000,
        total_debt=29500,
        net_worth=570500,
        cash_balance=50000,
        monthly_income=7000,
        monthly_expenses=3000,
        monthly_cash_flow=4000,
        savings_rate=0.57,
        debt_to_income_ratio=0.09,
        emergency_fund_months=16.67,
    )


def test_emergency_fund_decision_includes_dollar_gap_and_contribution():
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
    emergency_fund = decisions.decisions[0]

    # target 3 months of $4,000 expenses = $12,000, minus $1,000 cash = $11,000 gap,
    # closed over the 6-month suggested horizon = ~$1,833.33/month
    assert "$11,000.00" in emergency_fund.description
    assert "$1,833.33" in emergency_fund.description


def test_debt_payoff_ranks_higher_interest_rate_first():
    snapshot = make_stable_snapshot()
    debts = [
        DebtSummary(name="Truck Loan", balance=22000, interest_rate=6.49),
        DebtSummary(name="Credit Card", balance=7500, interest_rate=24.99),
    ]

    decisions = generate_decisions(snapshot, debts=debts)
    debt_titles = [d.title for d in decisions.decisions if d.title.startswith("Pay down")]

    assert debt_titles[0] == "Pay down Credit Card"
    assert debt_titles[1] == "Pay down Truck Loan"


def test_debt_payoff_skipped_when_cash_flow_not_positive():
    snapshot = FinancialSnapshot(
        month="2026-06",
        total_assets=1000,
        total_debt=7500,
        net_worth=-6500,
        cash_balance=1000,
        monthly_income=3000,
        monthly_expenses=3200,
        monthly_cash_flow=-200,
        savings_rate=0.0,
        debt_to_income_ratio=0.06,
        emergency_fund_months=0.31,
    )
    debts = [DebtSummary(name="Credit Card", balance=7500, interest_rate=24.99)]

    decisions = generate_decisions(snapshot, debts=debts)

    assert all(not d.title.startswith("Pay down") for d in decisions.decisions)


def test_debt_payoff_skips_debt_missing_interest_rate():
    snapshot = make_stable_snapshot()
    debts = [DebtSummary(name="Family Loan", balance=5000, interest_rate=None)]

    decisions = generate_decisions(snapshot, debts=debts)

    assert all(not d.title.startswith("Pay down") for d in decisions.decisions)


def test_goal_funding_feasible_when_cash_flow_supports_it():
    snapshot = make_stable_snapshot()
    goal = GoalSummary(
        name="Vacation Fund",
        target_amount=6000,
        current_amount=0,
        target_date=date(2027, 6, 24),
    )

    decisions = _goal_funding_decisions(snapshot, [goal], today=date(2026, 6, 24))

    assert decisions[0].title == "Fund goal: Vacation Fund"
    assert "$500.00" in decisions[0].description


def test_goal_funding_flagged_at_risk_when_infeasible():
    snapshot = make_stable_snapshot()
    goal = GoalSummary(
        name="Down Payment",
        target_amount=100000,
        current_amount=0,
        target_date=date(2027, 6, 24),
    )

    decisions = _goal_funding_decisions(snapshot, [goal], today=date(2026, 6, 24))

    assert decisions[0].title == "Fund goal: Down Payment (at risk)"


def test_goal_funding_skips_already_met_goal():
    snapshot = make_stable_snapshot()
    goal = GoalSummary(
        name="Emergency Fund",
        target_amount=10000,
        current_amount=12000,
        target_date=date(2027, 6, 24),
    )

    decisions = _goal_funding_decisions(snapshot, [goal], today=date(2026, 6, 24))

    assert decisions == []