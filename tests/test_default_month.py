"""Covers the follow-the-data month resolution behind every report page.

Regression context: every desktop page used to hardcode the demo data's month ("2026-06")
as its default. The first real-world import -- transactions dated any other month -- showed
$0 income and $0 expenses everywhere, because each page summed transactions inside a month
the user's data wasn't in.
"""

from datetime import date

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from finance_ai.db import models  # noqa: F401 -- registers tables on Base.metadata
from finance_ai.db.database import Base
from finance_ai.db.models import Account, Category, Transaction
from finance_ai.finance.metrics import (
    create_financial_snapshot,
    default_report_month,
    latest_transaction_month,
)

TODAY = date(2026, 7, 28)


@pytest.fixture
def session_factory():
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def add_transaction(session_factory, transaction_date: date, amount: float) -> None:
    with session_factory() as session:
        account = session.query(Account).first()
        if account is None:
            account = Account(name="Checking", account_type="checking", current_balance=1000.0)
            session.add(account)
            session.flush()
        session.add(
            Transaction(
                transaction_date=transaction_date,
                merchant="Anyone",
                amount=amount,
                account_id=account.id,
            )
        )
        session.commit()


def test_uses_the_month_of_the_most_recent_transaction(session_factory):
    add_transaction(session_factory, date(2026, 3, 5), -10.0)
    add_transaction(session_factory, date(2026, 5, 12), -20.0)

    assert default_report_month(today=TODAY, session_factory=session_factory) == "2026-05"


def test_falls_back_to_todays_month_with_no_transactions(session_factory):
    assert default_report_month(today=TODAY, session_factory=session_factory) == "2026-07"


def test_latest_transaction_month_is_none_with_no_transactions(session_factory):
    with session_factory() as session:
        assert latest_transaction_month(session) is None


def test_income_dated_outside_the_demo_month_is_found():
    """The original bug, end to end: a paycheck dated July used to read as $0 income
    because pages asked about the hardcoded June. Resolving the month from the data and
    then building the snapshot for it must find the paycheck."""

    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

    with factory() as session:
        account = Account(name="Checking", account_type="checking", current_balance=5000.0)
        salary = Category(name="Salary", category_type="income")
        session.add_all([account, salary])
        session.flush()
        session.add(
            Transaction(
                transaction_date=date(2026, 7, 15),
                merchant="Employer",
                amount=4200.0,
                account_id=account.id,
                category_id=salary.id,
            )
        )
        session.commit()

        month = default_report_month(today=TODAY, session_factory=factory)
        assert month == "2026-07"

        snapshot = create_financial_snapshot(month, session=session)
        assert snapshot.monthly_income == 4200.0
