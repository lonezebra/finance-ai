from finance_ai.finance.summary import (
    format_currency,
    format_months,
    format_optional_months,
    format_percent,
)
from finance_ai.history.interpreter import interpret_comparison
from finance_ai.scenario.models import ScenarioResult


def format_scenario_for_ai(result: ScenarioResult) -> str:
    snapshot = result.projected_snapshot
    changes = interpret_comparison(result.comparison)

    lines = [
        f"Scenario: {result.scenario.name}",
        "",
        "Adjustments Applied:",
    ]

    if result.scenario_facts:
        for fact in result.scenario_facts:
            lines.append(f"- {fact}")
    else:
        lines.append("- No adjustments applied.")

    lines.append("")
    lines.append("Projected Changes vs. Current Position:")

    if changes:
        for change in changes:
            lines.append(
                f"- {change.metric}: {change.direction.value} "
                f"({change.previous:,.2f} -> {change.current:,.2f}, "
                f"{change.percent_change * 100:+.1f}%, {change.significance.value} significance)"
            )
    else:
        lines.append("- No metrics change under this scenario.")

    lines.append("")
    lines.append(f"Projected Financial Position ({snapshot.month}):")
    lines.append(f"- Net Worth: {format_currency(snapshot.net_worth)}")
    lines.append(f"- Total Assets: {format_currency(snapshot.total_assets)}")
    lines.append(f"- Total Debt: {format_currency(snapshot.total_debt)}")
    lines.append(f"- Cash Balance: {format_currency(snapshot.cash_balance)}")
    lines.append(f"- Monthly Income: {format_currency(snapshot.monthly_income)}")
    lines.append(f"- Monthly Expenses: {format_currency(snapshot.monthly_expenses)}")
    lines.append(f"- Monthly Cash Flow: {format_currency(snapshot.monthly_cash_flow)}")
    lines.append(f"- Savings Rate: {format_percent(snapshot.savings_rate)}")
    lines.append(f"- Debt-to-Income Ratio (take-home): {format_percent(snapshot.debt_to_income_ratio)}")
    lines.append(
        f"- Emergency Fund, at current spending: {format_months(snapshot.emergency_fund_months)}"
    )
    lines.append(
        "- Emergency Fund, essentials only: "
        f"{format_optional_months(snapshot.essential_emergency_fund_months)}"
    )

    lines.append("")
    lines.append("Projected Top Decisions:")

    top_decisions = result.projected_decisions.decisions[:3]

    if top_decisions:
        for decision in top_decisions:
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
