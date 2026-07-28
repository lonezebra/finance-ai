"""Covers the essentials-only emergency fund figure: the calculation, the import column
that feeds it, and the deliberate use of None (rather than 0.0) for "not set up yet"."""

from datetime import date

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from finance_ai.db import models  # noqa: F401 -- registers tables on Base.metadata
from finance_ai.db.database import Base
from finance_ai.db.models import Account, Category, Transaction
from finance_ai.finance.metrics import get_monthly_essential_expenses
from finance_ai.finance.summary import format_optional_currency, format_optional_months
from finance_ai.imports.mapper import _optional_bool

MONTH = "2026-06"


@pytest.fixture
def session_factory():
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def _setup(session_factory, spending: list[tuple[str, bool | None, float]]) -> None:
    """spending is (category name, is_essential, amount spent) -- amounts given as positive
    numbers and stored as negative, matching the app's expense convention."""

    with session_factory() as session:
        account = Account(name="Checking", account_type="checking", current_balance=10000.0)
        session.add(account)
        session.flush()

        for name, is_essential, amount in spending:
            category = Category(name=name, category_type="expense", is_essential=is_essential)
            session.add(category)
            session.flush()
            session.add(
                Transaction(
                    transaction_date=date(2026, 6, 10),
                    merchant=name,
                    amount=-amount,
                    account_id=account.id,
                    category_id=category.id,
                )
            )

        session.commit()


# --- the calculation --------------------------------------------------------------------


def test_returns_none_when_nothing_is_marked_essential(session_factory):
    """None means "the user hasn't told us", which is different from "they spend nothing on
    essentials". Returning 0.0 here would display as no runway at all."""

    _setup(session_factory, [("Groceries", None, 300.0), ("Streaming", None, 50.0)])

    with session_factory() as session:
        assert get_monthly_essential_expenses(session, MONTH) is None


def test_sums_only_the_categories_marked_essential(session_factory):
    _setup(
        session_factory,
        [("Groceries", True, 300.0), ("Rent", True, 1200.0), ("Restaurants", False, 400.0)],
    )

    with session_factory() as session:
        assert get_monthly_essential_expenses(session, MONTH) == 1500.0


def test_unmarked_categories_are_excluded_not_assumed_essential(session_factory):
    """Only spending positively confirmed as essential counts, so the figure never
    overstates what the user would truly have to keep paying."""

    _setup(session_factory, [("Rent", True, 1000.0), ("Mystery", None, 500.0)])

    with session_factory() as session:
        assert get_monthly_essential_expenses(session, MONTH) == 1000.0


def test_only_counts_spending_in_the_requested_month(session_factory):
    _setup(session_factory, [("Rent", True, 1000.0)])

    with session_factory() as session:
        assert get_monthly_essential_expenses(session, MONTH) == 1000.0
        assert get_monthly_essential_expenses(session, "2026-07") == 0.0


def test_income_is_never_counted_as_essential_spending(session_factory):
    """Only negative amounts are spending. A category marked essential that somehow has
    income against it must not reduce the total."""

    with session_factory() as session:
        account = Account(name="Checking", account_type="checking", current_balance=1000.0)
        category = Category(name="Rent", category_type="expense", is_essential=True)
        session.add_all([account, category])
        session.flush()
        session.add(
            Transaction(
                transaction_date=date(2026, 6, 1),
                amount=-800.0,
                account_id=account.id,
                category_id=category.id,
            )
        )
        session.add(
            Transaction(
                transaction_date=date(2026, 6, 2),
                amount=2000.0,  # a refund or misfiled deposit
                account_id=account.id,
                category_id=category.id,
            )
        )
        session.commit()

    with session_factory() as session:
        assert get_monthly_essential_expenses(session, MONTH) == 800.0


# --- the snapshot ------------------------------------------------------------------------


def test_essentials_only_runway_is_longer_than_at_current_spending(session_factory):
    """The reason the feature exists: in an emergency you cut discretionary spending, so the
    essentials-only figure is the more realistic one."""

    from finance_ai.finance.metrics import _safe_divide

    _setup(session_factory, [("Rent", True, 1000.0), ("Restaurants", False, 1000.0)])

    with session_factory() as session:
        all_spending = 2000.0
        essential = get_monthly_essential_expenses(session, MONTH)
        cash = 10000.0

        assert _safe_divide(cash, essential) > _safe_divide(cash, all_spending)
        assert _safe_divide(cash, essential) == 10.0
        assert _safe_divide(cash, all_spending) == 5.0


# --- the import column -------------------------------------------------------------------


@pytest.mark.parametrize(
    ("cell", "expected"),
    [
        ("yes", True),
        ("Yes", True),
        (" YES ", True),
        ("y", True),
        ("true", True),
        (1, True),
        (True, True),
        ("no", False),
        ("No", False),
        ("n", False),
        ("false", False),
        (0, False),
        (False, False),
    ],
)
def test_essential_column_reads_common_ways_of_writing_yes_and_no(cell, expected):
    assert _optional_bool(cell) is expected


@pytest.mark.parametrize("cell", [None, "", "   ", "maybe", "sort of", "1.5"])
def test_unrecognised_or_blank_cells_become_not_stated_rather_than_no(cell):
    """A typo must not silently become a confident "no" -- that would quietly shrink the
    user's essential spending and overstate their runway."""

    assert _optional_bool(cell) is None


# --- plain-language display --------------------------------------------------------------


def test_unset_figures_are_described_in_words_not_as_zero():
    assert format_optional_months(None) == "not set up yet"
    assert format_optional_currency(None) == "not set up yet"


def test_present_figures_format_normally():
    assert format_optional_months(6.0) == "6.0 months"
    assert format_optional_currency(1500.0) == "$1,500.00"
