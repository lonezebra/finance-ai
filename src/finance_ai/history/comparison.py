from finance_ai.history.models import SnapshotComparison, SnapshotDifference, SnapshotRecord


METRICS_TO_COMPARE = {
    "total_assets": "Total Assets",
    "total_debt": "Total Debt",
    "net_worth": "Net Worth",
    "cash_balance": "Cash Balance",
    "monthly_income": "Monthly Income",
    "monthly_expenses": "Monthly Expenses",
    "monthly_cash_flow": "Monthly Cash Flow",
    "savings_rate": "Savings Rate",
    "debt_to_income_ratio": "Debt-to-Income Ratio",
    "emergency_fund_months": "Emergency Fund Months",
}


def compare_snapshots(
    previous: SnapshotRecord,
    current: SnapshotRecord,
) -> SnapshotComparison:
    differences: list[SnapshotDifference] = []

    for field_name, display_name in METRICS_TO_COMPARE.items():
        previous_value = float(getattr(previous.snapshot, field_name))
        current_value = float(getattr(current.snapshot, field_name))

        change = current_value - previous_value
        percent_change = _percent_change(previous_value, change)

        if change == 0:
            continue

        differences.append(
            SnapshotDifference(
                metric=display_name,
                previous=previous_value,
                current=current_value,
                change=change,
                percent_change=percent_change,
            )
        )

    return SnapshotComparison(
        previous=previous,
        current=current,
        differences=differences,
    )


def _percent_change(previous: float, change: float) -> float:
    if previous == 0:
        return 0.0

    return change / previous