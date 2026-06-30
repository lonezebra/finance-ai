from finance_ai.finance.metrics import get_finance_snapshot


def format_currency(value: float) -> str:
    return f"${value:,.2f}"


def financial_summary(month: str) -> str:
    snapshot = get_finance_snapshot(month)

    return f"""
Financial Summary for {month}

Assets: {format_currency(snapshot.total_assets)}
Debt: {format_currency(snapshot.total_debt)}
Net Worth: {format_currency(snapshot.net_worth)}
Cash Balance: {format_currency(snapshot.cash_balance)}

Monthly Income: {format_currency(snapshot.monthly_income)}
Monthly Expenses: {format_currency(snapshot.monthly_expenses)}
Monthly Cash Flow: {format_currency(snapshot.monthly_cash_flow)}
""".strip()