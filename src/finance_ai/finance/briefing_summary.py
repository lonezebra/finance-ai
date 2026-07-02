from finance_ai.finance.open_cfo import OpenCFOBriefing, create_open_cfo_briefing
from finance_ai.finance.summary import format_currency, format_months, format_percent


def format_briefing(briefing: OpenCFOBriefing) -> str:
    snapshot = briefing.snapshot
    confidence = briefing.confidence
    health = briefing.health

    lines = [
        f"Open CFO Briefing for {snapshot.month}",
        "",
        briefing.headline,
        "",
        "Financial Snapshot",
        f"- Net Worth: {format_currency(snapshot.net_worth)}",
        f"- Cash Balance: {format_currency(snapshot.cash_balance)}",
        f"- Total Debt: {format_currency(snapshot.total_debt)}",
        f"- Monthly Cash Flow: {format_currency(snapshot.monthly_cash_flow)}",
        f"- Savings Rate: {format_percent(snapshot.savings_rate)}",
        f"- Debt-to-Income Ratio: {format_percent(snapshot.debt_to_income_ratio)}",
        f"- Emergency Fund: {format_months(snapshot.emergency_fund_months)}",
        "",
        f"Financial Confidence: {confidence.score}/100 ({confidence.label})",
        "",
        f"Financial Health: {health.score}/100 ({health.label})",
        "",
        "Current Risks:",
    ]

    if health.issues:
        for issue in health.issues:
            lines.append(f"- [{issue.severity}] {issue.message}")
    else:
        lines.append("- No significant financial risks detected.")

    lines.append("")
    lines.append("Top Opportunities:")

    if briefing.top_opportunities:
        for opportunity in briefing.top_opportunities[:3]:
            lines.append(
                f"- {opportunity.title} "
                f"(Score: {opportunity.opportunity_score}, "
                f"Impact: {opportunity.impact_score}, "
                f"Confidence: {opportunity.confidence_score}/100, "
                f"Difficulty: {opportunity.difficulty.value})"
            )
            lines.append(f"  Reason: {opportunity.reason}")
    else:
        lines.append("- No opportunities identified.")

    return "\n".join(lines)


def briefing_summary(month: str) -> str:
    briefing = create_open_cfo_briefing(month)
    return format_briefing(briefing)