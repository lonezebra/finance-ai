from finance_ai.history.comparison import compare_snapshots
from finance_ai.history.engine import get_previous_snapshot, save_snapshot
from finance_ai.history.interpreter import ChangeSignificance, interpret_comparison
from finance_ai.reports.models import ExecutiveReport


def create_executive_report(month: str) -> ExecutiveReport:
    current_record = save_snapshot(month)
    previous_record = get_previous_snapshot()

    important_changes = []

    if previous_record:
        comparison = compare_snapshots(previous_record, current_record)
        interpreted = interpret_comparison(comparison)
        important_changes = [
            change
            for change in interpreted
            if change.significance in {ChangeSignificance.MEDIUM, ChangeSignificance.HIGH}
        ]

    snapshot = current_record.snapshot

    return ExecutiveReport(
        month=month,
        snapshot=snapshot,
        important_changes=important_changes,
        strengths=_identify_strengths(snapshot),
        concerns=_identify_concerns(snapshot),
        recommended_focus=_recommended_focus(snapshot),
    )


def _identify_strengths(snapshot):
    strengths = []

    if snapshot.monthly_cash_flow > 0:
        strengths.append("Positive monthly cash flow.")

    if snapshot.emergency_fund_months >= 6:
        strengths.append("Emergency fund exceeds 6 months of expenses.")

    if snapshot.debt_to_income_ratio <= 0.25:
        strengths.append("Debt-to-income ratio is conservative.")

    if snapshot.net_worth > 0:
        strengths.append("Net worth is positive.")

    return strengths


def _identify_concerns(snapshot):
    concerns = []

    if snapshot.monthly_cash_flow < 0:
        concerns.append("Monthly cash flow is negative.")

    if snapshot.emergency_fund_months < 3:
        concerns.append("Emergency fund is below 3 months of expenses.")

    if snapshot.debt_to_income_ratio > 0.36:
        concerns.append("Debt-to-income ratio is elevated.")

    return concerns


def _recommended_focus(snapshot):
    if snapshot.monthly_cash_flow < 0:
        return "Stabilize monthly cash flow."

    if snapshot.emergency_fund_months < 3:
        return "Build emergency fund."

    if snapshot.debt_to_income_ratio > 0.36:
        return "Reduce debt burden."

    return "Optimize capital allocation."