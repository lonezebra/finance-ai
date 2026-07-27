from datetime import datetime

from finance_ai.decision.engine import generate_decisions_from_db
from finance_ai.finance.confidence import calculate_financial_confidence_score
from finance_ai.finance.metrics import create_financial_snapshot
from finance_ai.history.comparison import compare_snapshots
from finance_ai.history.engine import get_latest_snapshot, get_previous_snapshot, save_snapshot
from finance_ai.history.interpreter import ChangeSignificance, interpret_comparison
from finance_ai.history.models import SnapshotRecord
from finance_ai.reports.models import ExecutiveReport


def create_executive_report(month: str, persist: bool = True) -> ExecutiveReport:
    """Builds an ExecutiveReport for month.

    persist=True (the default, used by "Generate Briefing") saves a new snapshot to
    financial_snapshot_records and compares it against the one before it -- an explicit
    check-in worth recording in history.

    persist=False computes the snapshot fresh without writing anything, and compares it
    against whatever was last saved. This is for read paths that render on every page visit
    (e.g. the briefing's summary cards) -- those must not multiply duplicate snapshot rows
    just from being viewed.
    """
    if persist:
        current_record = save_snapshot(month)
        previous_record = get_previous_snapshot()
    else:
        current_record = SnapshotRecord(
            id=None,
            created_at=datetime.now(),
            snapshot=create_financial_snapshot(month),
        )
        previous_record = get_latest_snapshot()

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
    decision_set = generate_decisions_from_db(snapshot)

    return ExecutiveReport(
        month=month,
        snapshot=snapshot,
        important_changes=important_changes,
        strengths=_identify_strengths(snapshot),
        concerns=_identify_concerns(snapshot),
        recommended_focus=_recommended_focus(snapshot),
        top_decisions=decision_set.decisions[:3],
        confidence=calculate_financial_confidence_score(),
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