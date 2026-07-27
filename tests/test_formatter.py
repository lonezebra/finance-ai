from finance_ai.decision.models import DecisionPriority, FinancialDecision, TimeHorizon
from finance_ai.finance.confidence import ConfidenceIssue, FinancialConfidenceScore
from finance_ai.finance.metrics import FinancialSnapshot
from finance_ai.history.interpreter import ChangeDirection, ChangeSignificance, InterpretedChange
from finance_ai.reports.formatter import format_executive_report_for_ai
from finance_ai.reports.models import ExecutiveReport


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
        savings_rate=0.57,
        debt_to_income_ratio=0.20,
        emergency_fund_months=16.67,
    )


def test_formatter_includes_snapshot_facts():
    report = ExecutiveReport(month="2026-06", snapshot=make_snapshot())

    output = format_executive_report_for_ai(report)

    assert "Executive Report for 2026-06" in output
    assert "Net Worth: $575,000.00" in output
    assert "Savings Rate: 57.0%" in output


def test_formatter_includes_default_confidence_when_not_specified():
    report = ExecutiveReport(month="2026-06", snapshot=make_snapshot())

    output = format_executive_report_for_ai(report)

    assert "Data Confidence: 100/100 (High)" in output


def test_formatter_includes_confidence_score_and_issues():
    confidence = FinancialConfidenceScore(
        score=65,
        issues=[
            ConfidenceIssue("medium", "No budgets have been created."),
            ConfidenceIssue("low", "No financial goals have been added."),
        ],
    )
    report = ExecutiveReport(month="2026-06", snapshot=make_snapshot(), confidence=confidence)

    output = format_executive_report_for_ai(report)

    assert "Data Confidence: 65/100 (Low)" in output
    assert "not financial health" in output
    assert "[medium] No budgets have been created." in output
    assert "[low] No financial goals have been added." in output


def test_formatter_lists_important_changes():
    change = InterpretedChange(
        metric="Net Worth",
        previous=570000,
        current=592000,
        change=22000,
        percent_change=0.0386,
        direction=ChangeDirection.IMPROVED,
        significance=ChangeSignificance.MEDIUM,
    )

    report = ExecutiveReport(
        month="2026-06",
        snapshot=make_snapshot(),
        important_changes=[change],
    )

    output = format_executive_report_for_ai(report)

    assert "Net Worth: improved" in output
    assert "medium significance" in output


def test_formatter_handles_empty_changes_strengths_and_concerns():
    report = ExecutiveReport(month="2026-06", snapshot=make_snapshot())

    output = format_executive_report_for_ai(report)

    assert "No significant changes since the previous snapshot." in output
    assert "None identified." in output
    assert "No decisions surfaced." in output


def test_formatter_lists_top_decisions_with_reasoning():
    decision = FinancialDecision(
        title="Optimize capital allocation",
        description="Evaluate whether surplus cash should be directed toward debt payoff, "
        "investing, or specific goals.",
        priority=DecisionPriority.MEDIUM,
        expected_impact_score=75,
        confidence_score=85,
        ease_multiplier=0.6,
        time_horizon=TimeHorizon.LONG_TERM,
        reasoning="Cash flow is positive, emergency reserves are strong, and debt is conservative.",
    )

    report = ExecutiveReport(
        month="2026-06",
        snapshot=make_snapshot(),
        top_decisions=[decision],
    )

    output = format_executive_report_for_ai(report)

    assert "Optimize capital allocation" in output
    assert "Reasoning: Cash flow is positive" in output
    assert "Priority: medium" in output
