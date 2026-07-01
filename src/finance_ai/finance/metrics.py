from dataclasses import dataclass
from datetime import date

from sqlalchemy import func

from finance_ai.db.database import SessionLocal
from finance_ai.db.models import Account, Asset, Debt, Transaction


@dataclass(frozen=True)
class FinancialSnapshot:
    month: str
    total_assets: float
    total_debt: float
    net_worth: float
    cash_balance: float
    monthly_income: float
    monthly_expenses: float
    monthly_cash_flow: float
    savings_rate: float
    debt_to_income_ratio: float
    emergency_fund_months: float


def _month_bounds(month: str) -> tuple[date, date]:
    year, month_number = [int(part) for part in month.split("-")]

    start = date(year, month_number, 1)

    if month_number == 12:
        end = date(year + 1, 1, 1)
    else:
        end = date(year, month_number + 1, 1)

    return start, end


def _safe_divide(numerator: float, denominator: float) -> float:
    if denominator == 0:
        return 0.0
    return numerator / denominator


def get_total_assets(session) -> float:
    account_total = session.query(func.coalesce(func.sum(Account.current_balance), 0)).scalar()
    asset_total = session.query(func.coalesce(func.sum(Asset.current_value), 0)).scalar()
    return float(account_total + asset_total)


def get_total_debt(session) -> float:
    total = session.query(func.coalesce(func.sum(Debt.balance), 0)).scalar()
    return float(total)


def get_cash_balance(session) -> float:
    total = (
        session.query(func.coalesce(func.sum(Account.current_balance), 0))
        .filter(Account.account_type.in_(["checking", "savings", "cash"]))
        .scalar()
    )
    return float(total)


def get_monthly_income(session, month: str) -> float:
    start, end = _month_bounds(month)

    total = (
        session.query(func.coalesce(func.sum(Transaction.amount), 0))
        .filter(Transaction.transaction_date >= start)
        .filter(Transaction.transaction_date < end)
        .filter(Transaction.amount > 0)
        .scalar()
    )

    return float(total)


def get_monthly_expenses(session, month: str) -> float:
    start, end = _month_bounds(month)

    total = (
        session.query(func.coalesce(func.sum(Transaction.amount), 0))
        .filter(Transaction.transaction_date >= start)
        .filter(Transaction.transaction_date < end)
        .filter(Transaction.amount < 0)
        .scalar()
    )

    return abs(float(total))


def get_monthly_debt_payments(session) -> float:
    total = session.query(func.coalesce(func.sum(Debt.minimum_payment), 0)).scalar()
    return float(total)


def create_financial_snapshot(month: str) -> FinancialSnapshot:
    with SessionLocal() as session:
        total_assets = get_total_assets(session)
        total_debt = get_total_debt(session)
        cash_balance = get_cash_balance(session)
        monthly_income = get_monthly_income(session, month)
        monthly_expenses = get_monthly_expenses(session, month)
        monthly_cash_flow = monthly_income - monthly_expenses
        monthly_debt_payments = get_monthly_debt_payments(session)

        savings_rate = _safe_divide(monthly_cash_flow, monthly_income)
        debt_to_income_ratio = _safe_divide(monthly_debt_payments, monthly_income)
        emergency_fund_months = _safe_divide(cash_balance, monthly_expenses)

        return FinancialSnapshot(
            month=month,
            total_assets=total_assets,
            total_debt=total_debt,
            net_worth=total_assets - total_debt,
            cash_balance=cash_balance,
            monthly_income=monthly_income,
            monthly_expenses=monthly_expenses,
            monthly_cash_flow=monthly_cash_flow,
            savings_rate=savings_rate,
            debt_to_income_ratio=debt_to_income_ratio,
            emergency_fund_months=emergency_fund_months,
        )