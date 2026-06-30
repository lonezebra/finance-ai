from dataclasses import dataclass
from sqlalchemy import func

from finance_ai.db.database import SessionLocal
from finance_ai.db.models import Account, Asset, Debt, Transaction


@dataclass
class FinanceSnapshot:
    total_assets: float
    total_debt: float
    net_worth: float
    cash_balance: float
    monthly_income: float
    monthly_expenses: float
    monthly_cash_flow: float


def get_total_assets(session) -> float:
    asset_total = session.query(func.coalesce(func.sum(Asset.current_value), 0)).scalar()
    account_total = session.query(func.coalesce(func.sum(Account.current_balance), 0)).scalar()
    return float(asset_total + account_total)


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
    start = f"{month}-01"
    end = f"{month}-31"

    total = (
        session.query(func.coalesce(func.sum(Transaction.amount), 0))
        .filter(Transaction.transaction_date >= start)
        .filter(Transaction.transaction_date <= end)
        .filter(Transaction.amount > 0)
        .scalar()
    )
    return float(total)


def get_monthly_expenses(session, month: str) -> float:
    start = f"{month}-01"
    end = f"{month}-31"

    total = (
        session.query(func.coalesce(func.sum(Transaction.amount), 0))
        .filter(Transaction.transaction_date >= start)
        .filter(Transaction.transaction_date <= end)
        .filter(Transaction.amount < 0)
        .scalar()
    )
    return abs(float(total))


def get_finance_snapshot(month: str) -> FinanceSnapshot:
    with SessionLocal() as session:
        total_assets = get_total_assets(session)
        total_debt = get_total_debt(session)
        cash_balance = get_cash_balance(session)
        monthly_income = get_monthly_income(session, month)
        monthly_expenses = get_monthly_expenses(session, month)

        return FinanceSnapshot(
            total_assets=total_assets,
            total_debt=total_debt,
            net_worth=total_assets - total_debt,
            cash_balance=cash_balance,
            monthly_income=monthly_income,
            monthly_expenses=monthly_expenses,
            monthly_cash_flow=monthly_income - monthly_expenses,
        )