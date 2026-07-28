from collections.abc import Callable
from contextlib import AbstractContextManager
from dataclasses import dataclass, field
from datetime import date

from sqlalchemy import func
from sqlalchemy.orm import Session

from finance_ai.db.database import SessionLocal
from finance_ai.db.models import Account, Asset, Budget, Category, Debt, Goal, Transaction

STALE_AFTER_DAYS = 30
VERY_STALE_AFTER_DAYS = 90

# How many overlapping names to name individually before summarizing the rest.
MAX_OVERLAPS_LISTED = 3


@dataclass(frozen=True)
class ConfidenceIssue:
    severity: str
    message: str


@dataclass(frozen=True)
class FinancialConfidenceScore:
    score: int
    issues: list[ConfidenceIssue] = field(default_factory=list)

    @property
    def label(self) -> str:
        if self.score >= 90:
            return "High"
        if self.score >= 70:
            return "Moderate"
        if self.score >= 50:
            return "Low"
        return "Very Low"


def _count(session, model) -> int:
    return int(session.query(func.count(model.id)).scalar() or 0)


@dataclass(frozen=True)
class NameOverlap:
    """One name that appears in both the Accounts and the Assets table."""

    name: str
    account_total: float
    asset_total: float

    @property
    def amount_at_stake(self) -> float:
        """What net worth is inflated by if these really are the same holding. The smaller
        of the two is the safe figure to quote: if a $10,000 savings account is also listed
        as a $10,000 asset, $10,000 is being counted twice. If the two disagree, only the
        overlapping portion is certainly duplicated."""

        return min(self.account_total, self.asset_total)


def find_account_asset_overlaps(session: Session) -> list[NameOverlap]:
    """Names appearing in both Accounts and Assets, matched case- and whitespace-insensitively.

    total_assets is sum(account balances) + sum(asset values), which is only correct because
    the two tables are meant to be disjoint: Accounts holds liquid balances (the template's
    examples are Checking and Savings) and Assets holds everything else (Home, Roth IRA).
    get_cash_balance() relies on the same split, filtering accounts to checking/savings/cash.

    Nothing in the schema enforces that, so a user who records one holding in both tables
    silently inflates net worth -- the headline number -- with no indication anything is off.

    This only reports. It deliberately does not adjust any figure: an exact name match is
    strong evidence but not proof (a "Vanguard" brokerage account and a "Vanguard" asset row
    could legitimately be different things), and silently changing someone's net worth on a
    guess is worse than the double-count, because the guess is invisible. Matching is exact
    rather than fuzzy for the same reason -- "Savings" vs "Savings Account" would generate
    false alarms that train the user to ignore the warning.
    """

    account_totals: dict[str, float] = {}
    account_display: dict[str, str] = {}
    for account in session.query(Account).all():
        key = (account.name or "").strip().casefold()
        if not key:
            continue
        # Account names aren't unique in the schema, so aggregate rather than overwrite.
        account_totals[key] = account_totals.get(key, 0.0) + float(account.current_balance or 0.0)
        account_display.setdefault(key, (account.name or "").strip())

    asset_totals: dict[str, float] = {}
    for asset in session.query(Asset).all():
        key = (asset.name or "").strip().casefold()
        if not key:
            continue
        asset_totals[key] = asset_totals.get(key, 0.0) + float(asset.current_value or 0.0)

    return [
        NameOverlap(
            name=account_display[key],
            account_total=account_totals[key],
            asset_total=asset_totals[key],
        )
        for key in sorted(account_totals.keys() & asset_totals.keys())
    ]


def _describe_overlaps(overlaps: list[NameOverlap]) -> str:
    from finance_ai.finance.summary import format_currency

    listed = overlaps[:MAX_OVERLAPS_LISTED]
    names = ", ".join(f'"{overlap.name}"' for overlap in listed)

    remainder = len(overlaps) - len(listed)
    if remainder > 0:
        names = f"{names} and {remainder} more"

    total = sum(overlap.amount_at_stake for overlap in overlaps)

    return (
        f"{names} {'appears' if len(overlaps) == 1 else 'appear'} in both Accounts and "
        f"Assets. Net worth adds the two tables together, so up to "
        f"{format_currency(total)} may be counted twice. Accounts is for liquid balances "
        "and Assets for everything else -- if these are the same holding, remove one."
    )


def calculate_financial_confidence_score(
    today: date | None = None,
    session_factory: Callable[[], AbstractContextManager[Session]] = SessionLocal,
) -> FinancialConfidenceScore:
    """Measures how complete and up to date the data behind Open CFO's numbers is -- not
    financial health. A full, well-categorized dataset scores high even if the user's
    finances themselves look concerning; a sparse or stale one scores low even if the
    numbers it does show look great.

    today defaults to the real current date; tests pass a fixed date so "how many days
    since the last transaction" doesn't depend on when the test happens to run.
    """

    today = today or date.today()
    issues: list[ConfidenceIssue] = []
    score = 100

    with session_factory() as session:
        account_count = _count(session, Account)
        transaction_count = _count(session, Transaction)
        category_count = _count(session, Category)
        debt_count = _count(session, Debt)
        asset_count = _count(session, Asset)
        budget_count = _count(session, Budget)
        goal_count = _count(session, Goal)

        if account_count == 0:
            score -= 20
            issues.append(ConfidenceIssue("high", "No accounts have been added."))

        if transaction_count == 0:
            score -= 20
            issues.append(ConfidenceIssue("high", "No transactions have been imported."))
        else:
            most_recent_date = session.query(func.max(Transaction.transaction_date)).scalar()

            if most_recent_date is not None:
                days_since_last_transaction = (today - most_recent_date).days

                if days_since_last_transaction > VERY_STALE_AFTER_DAYS:
                    score -= 20
                    issues.append(
                        ConfidenceIssue(
                            "high",
                            f"No transactions in {days_since_last_transaction} days -- this "
                            "data may no longer reflect your current financial position.",
                        )
                    )
                elif days_since_last_transaction > STALE_AFTER_DAYS:
                    score -= 10
                    issues.append(
                        ConfidenceIssue(
                            "medium",
                            f"No transactions in {days_since_last_transaction} days -- "
                            "consider importing more recent activity.",
                        )
                    )

        if category_count == 0:
            score -= 10
            issues.append(ConfidenceIssue("medium", "No categories have been added."))

        if budget_count == 0:
            score -= 10
            issues.append(ConfidenceIssue("medium", "No budgets have been created."))

        if debt_count == 0:
            score -= 5
            issues.append(ConfidenceIssue("low", "No debts have been added."))

        if asset_count == 0:
            score -= 5
            issues.append(ConfidenceIssue("low", "No assets have been added."))

        if goal_count == 0:
            score -= 5
            issues.append(ConfidenceIssue("low", "No financial goals have been added."))

        uncategorized = (
            session.query(func.count(Transaction.id))
            .filter(Transaction.category_id.is_(None))
            .scalar()
            or 0
        )

        if uncategorized > 0:
            score -= min(15, int(uncategorized))
            issues.append(
                ConfidenceIssue(
                    "medium",
                    f"{uncategorized} transactions are uncategorized.",
                )
            )

        debts_missing_rate = (
            session.query(func.count(Debt.id))
            .filter(Debt.interest_rate.is_(None))
            .scalar()
            or 0
        )

        if debts_missing_rate > 0:
            score -= min(10, int(debts_missing_rate) * 3)
            issues.append(
                ConfidenceIssue(
                    "medium",
                    f"{debts_missing_rate} debts are missing interest rates.",
                )
            )

        overlaps = find_account_asset_overlaps(session)

        if overlaps:
            # A single flat penalty regardless of how many names overlap: this is one class
            # of problem (the Accounts/Assets split isn't being followed), and the message
            # enumerates the specifics so the user can act. Weighted high because it
            # distorts net worth -- the most prominent number in the product -- rather than
            # merely leaving a gap.
            score -= 15
            issues.append(ConfidenceIssue("high", _describe_overlaps(overlaps)))

    return FinancialConfidenceScore(score=max(score, 0), issues=issues)
