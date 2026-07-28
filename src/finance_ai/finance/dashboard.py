"""Data for the Dashboard page: current balances, recent activity, and budget status.

Deliberately separate from the Executive Report Engine (reports/engine.py). The Executive
Briefing page already covers "what changed" and "what should I do next" -- an AI-narrated
report meant to be generated deliberately. The Dashboard is the fast, always-current landing
page: a plain read of the books, with no AI involved and no LM Studio dependency, so it's safe
to rebuild on every visit.
"""

from dataclasses import dataclass
from datetime import date

from sqlalchemy import func

from finance_ai.db.database import SessionLocal
from finance_ai.db.models import Account, Asset, Budget, Category, Debt, Transaction
from finance_ai.finance.metrics import FinancialSnapshot, create_financial_snapshot, month_bounds

RECENT_TRANSACTIONS_LIMIT = 10


@dataclass(frozen=True)
class AccountSummary:
    name: str
    account_type: str
    institution: str | None
    balance: float


@dataclass(frozen=True)
class DebtSummary:
    name: str
    lender: str | None
    balance: float
    interest_rate: float | None
    minimum_payment: float | None
    due_day: int | None


@dataclass(frozen=True)
class AssetSummary:
    name: str
    asset_type: str
    value: float


@dataclass(frozen=True)
class RecentTransaction:
    transaction_date: date
    description: str
    category_name: str | None
    amount: float


@dataclass(frozen=True)
class BudgetStatusLine:
    category_name: str
    budgeted_amount: float
    actual_amount: float

    @property
    def variance(self) -> float:
        """Positive means under budget, negative means over."""

        return self.budgeted_amount - self.actual_amount

    @property
    def is_over_budget(self) -> bool:
        return self.actual_amount > self.budgeted_amount


@dataclass(frozen=True)
class DashboardData:
    month: str
    snapshot: FinancialSnapshot
    accounts: list[AccountSummary]
    debts: list[DebtSummary]
    assets: list[AssetSummary]
    recent_transactions: list[RecentTransaction]
    budget_lines: list[BudgetStatusLine]


def _resolve_month(session, month: str | None, today: date) -> str:
    """The month to show, when the caller doesn't pin one.

    Uses the month of the most recent transaction rather than today's calendar month --
    a dashboard for a file last imported three months ago should show that month's figures,
    not a blank current month that makes the app look broken. Falls back to today's month
    only when there's no transaction data to go by at all.
    """

    if month is not None:
        return month

    most_recent = session.query(func.max(Transaction.transaction_date)).scalar()
    if most_recent is not None:
        return f"{most_recent.year:04d}-{most_recent.month:02d}"

    return f"{today.year:04d}-{today.month:02d}"


def get_accounts(session) -> list[AccountSummary]:
    accounts = [
        AccountSummary(
            name=account.name,
            account_type=account.account_type,
            institution=account.institution,
            balance=float(account.current_balance or 0.0),
        )
        for account in session.query(Account).all()
    ]
    return sorted(accounts, key=lambda account: account.balance, reverse=True)


def get_debts(session) -> list[DebtSummary]:
    debts = [
        DebtSummary(
            name=debt.name,
            lender=debt.lender,
            balance=float(debt.balance or 0.0),
            interest_rate=debt.interest_rate,
            minimum_payment=debt.minimum_payment,
            due_day=debt.due_day,
        )
        for debt in session.query(Debt).all()
    ]
    return sorted(debts, key=lambda debt: debt.balance, reverse=True)


def get_assets(session) -> list[AssetSummary]:
    assets = [
        AssetSummary(
            name=asset.name,
            asset_type=asset.asset_type,
            value=float(asset.current_value or 0.0),
        )
        for asset in session.query(Asset).all()
    ]
    return sorted(assets, key=lambda asset: asset.value, reverse=True)


def get_recent_transactions(session, limit: int = RECENT_TRANSACTIONS_LIMIT) -> list[RecentTransaction]:
    rows = (
        session.query(Transaction, Category.name)
        .outerjoin(Category, Transaction.category_id == Category.id)
        .order_by(Transaction.transaction_date.desc(), Transaction.id.desc())
        .limit(limit)
        .all()
    )

    return [
        RecentTransaction(
            transaction_date=transaction.transaction_date,
            description=transaction.merchant or transaction.description or "(no description)",
            category_name=category_name,
            amount=transaction.amount,
        )
        for transaction, category_name in rows
    ]


def get_budget_status(session, month: str) -> list[BudgetStatusLine]:
    """Budgeted vs. actual spending per category for month, most overspent first.

    Only covers categories that have a budget row for this month -- there's nothing to
    compare an unbudgeted category against. A budgeted category with no matching spending
    still appears, at 0 actual, so "you haven't spent anything here yet" is visible rather
    than silently dropped.
    """

    budgets = session.query(Budget).filter(Budget.month == month).all()
    if not budgets:
        return []

    start, end = month_bounds(month)

    actuals = dict(
        session.query(Category.name, func.coalesce(func.sum(Transaction.amount), 0))
        .join(Transaction, Transaction.category_id == Category.id)
        .filter(Transaction.transaction_date >= start)
        .filter(Transaction.transaction_date < end)
        .filter(Transaction.amount < 0)
        .group_by(Category.name)
        .all()
    )

    lines = [
        BudgetStatusLine(
            category_name=budget.category_name,
            budgeted_amount=float(budget.budgeted_amount or 0.0),
            actual_amount=abs(float(actuals.get(budget.category_name, 0.0))),
        )
        for budget in budgets
    ]

    return sorted(lines, key=lambda line: line.variance)


def create_dashboard_data(
    month: str | None = None,
    today: date | None = None,
    session_factory=SessionLocal,
) -> DashboardData:
    today = today or date.today()

    with session_factory() as session:
        resolved_month = _resolve_month(session, month, today)

        return DashboardData(
            month=resolved_month,
            snapshot=create_financial_snapshot(resolved_month, session=session),
            accounts=get_accounts(session),
            debts=get_debts(session),
            assets=get_assets(session),
            recent_transactions=get_recent_transactions(session),
            budget_lines=get_budget_status(session, resolved_month),
        )
