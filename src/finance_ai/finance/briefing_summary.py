from finance_ai.finance.open_cfo import OpenCFOBriefing, create_open_cfo_briefing
from finance_ai.finance.summary import format_currency, format_months, format_percent


def format_briefing(briefing: OpenCFOBriefing) -> str:
    snapshot = briefing.snapshot
    confidence = briefing.confidence

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
        "Recommended Action Items:",
    ]

    for item in briefing.action_items:
        lines.append(f"- [{item.priority}] {item.title}: {item.reason}")

    return "\n".join(lines)


def briefing_summary(month: str) -> str:
    briefing = create_open_cfo_briefing(month)
    return format_briefing(briefing)