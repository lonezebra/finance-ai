from finance_ai.finance.summary import format_currency, format_months, format_percent
from finance_ai.reports.models import ExecutiveReport


def format_executive_report_for_ai(report: ExecutiveReport) -> str:
    snapshot = report.snapshot

    lines = [
        f"Executive Report for {report.month}",
        "",
        "Financial Snapshot",
        f"- Net Worth: {format_currency(snapshot.net_worth)}",
        f"- Total Assets: {format_currency(snapshot.total_assets)}",
        f"- Total Debt: {format_currency(snapshot.total_debt)}",
        f"- Cash Balance: {format_currency(snapshot.cash_balance)}",
        f"- Monthly Income: {format_currency(snapshot.monthly_income)}",
        f"- Monthly Expenses: {format_currency(snapshot.monthly_expenses)}",
        f"- Monthly Cash Flow: {format_currency(snapshot.monthly_cash_flow)}",
        f"- Savings Rate: {format_percent(snapshot.savings_rate)}",
        f"- Debt-to-Income Ratio (take-home): {format_percent(snapshot.debt_to_income_ratio)}",
        f"- Emergency Fund: {format_months(snapshot.emergency_fund_months)}",
        "",
        (
            f"Data Confidence: {report.confidence.score}/100 ({report.confidence.label}) -- "
            "measures how complete and trustworthy the underlying data is, not financial health."
        ),
    ]

    for issue in report.confidence.issues:
        lines.append(f"- [{issue.severity}] {issue.message}")

    lines.append("")
    lines.append("Important Changes:")

    if report.important_changes:
        for change in report.important_changes:
            lines.append(
                f"- {change.metric}: {change.direction.value} "
                f"({change.previous:,.2f} -> {change.current:,.2f}, "
                f"{change.percent_change * 100:+.1f}%, {change.significance.value} significance)"
            )
    else:
        lines.append("- No significant changes since the previous snapshot.")

    lines.append("")
    lines.append("Strengths:")

    if report.strengths:
        for strength in report.strengths:
            lines.append(f"- {strength}")
    else:
        lines.append("- None identified.")

    lines.append("")
    lines.append("Concerns:")

    if report.concerns:
        for concern in report.concerns:
            lines.append(f"- {concern}")
    else:
        lines.append("- None identified.")

    lines.append("")
    lines.append(f"Recommended Focus: {report.recommended_focus or 'None'}")

    lines.append("")
    lines.append("Top Decisions:")

    if report.top_decisions:
        for decision in report.top_decisions:
            lines.append(
                f"- {decision.title} "
                f"(Priority: {decision.priority.value}, "
                f"Time Horizon: {decision.time_horizon.value}, "
                f"Score: {decision.score})"
            )
            lines.append(f"  Reasoning: {decision.reasoning}")
    else:
        lines.append("- No decisions surfaced.")

    return "\n".join(lines)
