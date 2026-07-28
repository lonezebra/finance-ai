from finance_ai.finance.metrics import FinancialSnapshot, create_financial_snapshot


def format_currency(value: float) -> str:
    return f"${value:,.2f}"


def format_percent(value: float) -> str:
    return f"{value * 100:.1f}%"


def format_months(value: float) -> str:
    return f"{value:.1f} months"


NOT_SET_UP = "not set up yet"


def format_optional_months(value: float | None) -> str:
    """For figures that can be genuinely unknown rather than zero. Says so in plain words
    instead of showing "0.0 months", which would read as "you have no runway at all"."""

    return NOT_SET_UP if value is None else format_months(value)


def format_optional_currency(value: float | None) -> str:
    return NOT_SET_UP if value is None else format_currency(value)


def format_snapshot(snapshot: FinancialSnapshot) -> str:
    return f"""
Financial Snapshot for {snapshot.month}

Net Worth: {format_currency(snapshot.net_worth)}
Total Assets: {format_currency(snapshot.total_assets)}
Total Debt: {format_currency(snapshot.total_debt)}
Cash Balance: {format_currency(snapshot.cash_balance)}

Monthly Income: {format_currency(snapshot.monthly_income)}
Monthly Expenses: {format_currency(snapshot.monthly_expenses)}
Monthly Cash Flow: {format_currency(snapshot.monthly_cash_flow)}

Savings Rate: {format_percent(snapshot.savings_rate)}
Debt-to-Income Ratio (take-home): {format_percent(snapshot.debt_to_income_ratio)}
Emergency Fund Coverage: {format_months(snapshot.emergency_fund_months)}
""".strip()


def financial_summary(month: str) -> str:
    snapshot = create_financial_snapshot(month)
    return format_snapshot(snapshot)