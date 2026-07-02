from finance_ai.finance.confidence import FinancialConfidenceScore
from finance_ai.finance.health import FinancialHealthScore
from finance_ai.finance.metrics import FinancialSnapshot
from finance_ai.finance.opportunities import OpportunityCategory, generate_opportunities


def test_low_confidence_prioritizes_data_quality():
    snapshot = FinancialSnapshot(
        month="2026-06",
        total_assets=0,
        total_debt=0,
        net_worth=0,
        cash_balance=0,
        monthly_income=0,
        monthly_expenses=0,
        monthly_cash_flow=0,
        savings_rate=0,
        debt_to_income_ratio=0,
        emergency_fund_months=0,
    )

    confidence = FinancialConfidenceScore(score=25)
    health = FinancialHealthScore(score=50)

    opportunities = generate_opportunities(snapshot, health, confidence)

    assert opportunities[0].category == OpportunityCategory.DATA_QUALITY
    assert opportunities[0].title == "Improve financial data quality"


def test_opportunities_are_sorted_by_score():
    snapshot = FinancialSnapshot(
        month="2026-06",
        total_assets=10000,
        total_debt=5000,
        net_worth=5000,
        cash_balance=500,
        monthly_income=5000,
        monthly_expenses=4500,
        monthly_cash_flow=500,
        savings_rate=0.10,
        debt_to_income_ratio=0.40,
        emergency_fund_months=0.11,
    )

    confidence = FinancialConfidenceScore(score=80)
    health = FinancialHealthScore(score=65)

    opportunities = generate_opportunities(snapshot, health, confidence)
    scores = [opportunity.opportunity_score for opportunity in opportunities]

    assert scores == sorted(scores, reverse=True)