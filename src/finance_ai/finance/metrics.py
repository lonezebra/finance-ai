from dataclasses import dataclass
from datetime import date

from sqlalchemy import func

from finance_ai.db.database import SessionLocal
from finance_ai.db.models import Account, Asset, Category, Debt, Transaction


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

    # "Essentials only" versions of the two expense figures above. None -- not 0.0 --
    # when the user hasn't marked any category as essential, because the honest answer
    # is "we don't know yet", and 0.0 would display as "no runway" or "no essential
    # spending", both of which are wrong and alarming. Consumers must handle None.
    essential_monthly_expenses: float | None = None
    essential_emergency_fund_months: float | None = None


def latest_transaction_month(session) -> str | None:
    """The `YYYY-MM` month of the most recent transaction, or None when there are none."""

    most_recent = session.query(func.max(Transaction.transaction_date)).scalar()
    if most_recent is None:
        return None
    return f"{most_recent.year:04d}-{most_recent.month:02d}"


def default_report_month(
    today: date | None = None,
    session_factory=SessionLocal,
) -> str:
    """The month to report on when the user hasn't picked one.

    Uses the month of the most recent transaction rather than today's calendar month:
    monthly income/expenses are computed from transactions inside one month, so a page that
    defaulted to the current calendar month would show $0 income for anyone whose latest
    import is even a few weeks old -- their money didn't disappear, the page was just
    looking at an empty month. Falls back to today's month only when there are no
    transactions at all (nothing to report on either way, but the label should at least be
    current).

    `today` is injectable for tests, same as calculate_financial_confidence_score().
    """

    today = today or date.today()

    with session_factory() as session:
        return latest_transaction_month(session) or f"{today.year:04d}-{today.month:02d}"


def month_bounds(month: str) -> tuple[date, date]:
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
    """Adding the two tables together is only correct because they're meant to be disjoint:
    Accounts holds liquid balances (Checking, Savings) and Assets holds everything else
    (Home, Roth IRA). get_cash_balance() relies on the same split.

    Nothing in the schema enforces it, so recording one holding in both tables inflates this
    figure. That's detected and reported as a Confidence Score issue
    (confidence.py::find_account_asset_overlaps) rather than corrected here -- an exact name
    match is strong evidence but not proof, and silently adjusting net worth on a guess would
    be worse than the double-count.
    """

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
    start, end = month_bounds(month)

    total = (
        session.query(func.coalesce(func.sum(Transaction.amount), 0))
        .filter(Transaction.transaction_date >= start)
        .filter(Transaction.transaction_date < end)
        .filter(Transaction.amount > 0)
        .scalar()
    )

    return float(total)


def get_monthly_expenses(session, month: str) -> float:
    start, end = month_bounds(month)

    total = (
        session.query(func.coalesce(func.sum(Transaction.amount), 0))
        .filter(Transaction.transaction_date >= start)
        .filter(Transaction.transaction_date < end)
        .filter(Transaction.amount < 0)
        .scalar()
    )

    return abs(float(total))


def get_monthly_essential_expenses(session, month: str) -> float | None:
    """Spending for the month in categories the user marked essential.

    Returns None when no category has been marked essential at all -- that's "not set up
    yet", which is different from "you spend nothing on essentials". Callers show it as
    unavailable rather than as zero.

    Categories explicitly marked non-essential are excluded, and so are ones left blank:
    only spending the user has positively confirmed as essential counts, so the figure
    never overstates what they'd truly have to keep paying.
    """

    any_marked = (
        session.query(func.count(Category.id)).filter(Category.is_essential.is_(True)).scalar() or 0
    )

    if not any_marked:
        return None

    start, end = month_bounds(month)

    total = (
        session.query(func.coalesce(func.sum(Transaction.amount), 0))
        .join(Category, Transaction.category_id == Category.id)
        .filter(Transaction.transaction_date >= start)
        .filter(Transaction.transaction_date < end)
        .filter(Transaction.amount < 0)
        .filter(Category.is_essential.is_(True))
        .scalar()
    )

    return abs(float(total))


def get_monthly_debt_payments(session) -> float:
    total = session.query(func.coalesce(func.sum(Debt.minimum_payment), 0)).scalar()
    return float(total)


def create_financial_snapshot(month: str, session=None) -> FinancialSnapshot:
    """Build the snapshot for month.

    Pass an open `session` to compute this as part of a larger read that already has one
    open (e.g. the Dashboard, which shares a single session across several queries and needs
    to inject a fake one in tests). Omit it to open and close a real one here, same as
    before -- every existing caller keeps working unchanged.
    """

    if session is not None:
        return _build_snapshot(session, month)

    with SessionLocal() as session:
        return _build_snapshot(session, month)


def _build_snapshot(session, month: str) -> FinancialSnapshot:
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

    essential_monthly_expenses = get_monthly_essential_expenses(session, month)
    essential_emergency_fund_months = (
        _safe_divide(cash_balance, essential_monthly_expenses)
        if essential_monthly_expenses is not None
        else None
    )

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
        essential_monthly_expenses=essential_monthly_expenses,
        essential_emergency_fund_months=essential_emergency_fund_months,
    )