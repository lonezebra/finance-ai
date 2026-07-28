from datetime import date

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from finance_ai.db import models  # noqa: F401 -- registers tables on Base.metadata
from finance_ai.db.database import Base
from finance_ai.db.models import Account, Asset, Budget, Category, Debt, Transaction
from finance_ai.finance.dashboard import create_dashboard_data

TODAY = date(2026, 7, 28)


@pytest.fixture
def session_factory():
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


# --- month resolution -----------------------------------------------------------------


def test_defaults_to_the_month_of_the_most_recent_transaction(session_factory):
    with session_factory() as session:
        account = Account(name="Checking", account_type="checking", current_balance=1000.0)
        session.add(account)
        session.flush()
        session.add(
            Transaction(
                transaction_date=date(2026, 3, 5),
                merchant="Old",
                amount=-10.0,
                account_id=account.id,
            )
        )
        session.add(
            Transaction(
                transaction_date=date(2026, 5, 12),
                merchant="Newest",
                amount=-20.0,
                account_id=account.id,
            )
        )
        session.commit()

    data = create_dashboard_data(today=TODAY, session_factory=session_factory)

    assert data.month == "2026-05"


def test_falls_back_to_todays_month_with_no_transactions(session_factory):
    data = create_dashboard_data(today=TODAY, session_factory=session_factory)

    assert data.month == "2026-07"


def test_an_explicit_month_is_used_as_is(session_factory):
    data = create_dashboard_data(month="2026-01", today=TODAY, session_factory=session_factory)

    assert data.month == "2026-01"


# --- accounts / debts / assets ----------------------------------------------------------


def test_accounts_are_sorted_by_balance_descending(session_factory):
    with session_factory() as session:
        session.add_all(
            [
                Account(name="Savings", account_type="savings", current_balance=500.0),
                Account(name="Checking", account_type="checking", current_balance=5000.0),
            ]
        )
        session.commit()

    data = create_dashboard_data(today=TODAY, session_factory=session_factory)

    assert [account.name for account in data.accounts] == ["Checking", "Savings"]


def test_debts_are_sorted_by_balance_descending(session_factory):
    with session_factory() as session:
        session.add_all(
            [
                Debt(name="Car Loan", balance=8000.0),
                Debt(name="Credit Card", balance=15000.0),
            ]
        )
        session.commit()

    data = create_dashboard_data(today=TODAY, session_factory=session_factory)

    assert [debt.name for debt in data.debts] == ["Credit Card", "Car Loan"]


def test_assets_are_sorted_by_value_descending(session_factory):
    with session_factory() as session:
        session.add_all(
            [
                Asset(name="Car", asset_type="vehicle", current_value=12000.0),
                Asset(name="Home", asset_type="real_estate", current_value=400000.0),
            ]
        )
        session.commit()

    data = create_dashboard_data(today=TODAY, session_factory=session_factory)

    assert [asset.name for asset in data.assets] == ["Home", "Car"]


# --- recent transactions -----------------------------------------------------------------


def test_recent_transactions_are_newest_first_and_limited(session_factory):
    with session_factory() as session:
        account = Account(name="Checking", account_type="checking", current_balance=1000.0)
        session.add(account)
        session.flush()

        for day in range(1, 13):
            session.add(
                Transaction(
                    transaction_date=date(2026, 5, day),
                    merchant=f"Store {day}",
                    amount=-10.0,
                    account_id=account.id,
                )
            )
        session.commit()

    data = create_dashboard_data(today=TODAY, session_factory=session_factory)

    assert len(data.recent_transactions) == 10
    assert data.recent_transactions[0].description == "Store 12"
    assert data.recent_transactions[-1].description == "Store 3"


def test_recent_transaction_falls_back_from_merchant_to_description_to_placeholder(
    session_factory,
):
    with session_factory() as session:
        account = Account(name="Checking", account_type="checking", current_balance=1000.0)
        session.add(account)
        session.flush()
        session.add(
            Transaction(
                transaction_date=date(2026, 5, 1),
                merchant=None,
                description="Wire transfer",
                amount=-100.0,
                account_id=account.id,
            )
        )
        session.add(
            Transaction(
                transaction_date=date(2026, 5, 2),
                merchant=None,
                description=None,
                amount=-5.0,
                account_id=account.id,
            )
        )
        session.commit()

    data = create_dashboard_data(today=TODAY, session_factory=session_factory)

    descriptions = {t.description for t in data.recent_transactions}
    assert "Wire transfer" in descriptions
    assert "(no description)" in descriptions


def test_recent_transaction_carries_its_category_name(session_factory):
    with session_factory() as session:
        account = Account(name="Checking", account_type="checking", current_balance=1000.0)
        category = Category(name="Groceries", category_type="expense")
        session.add_all([account, category])
        session.flush()
        session.add(
            Transaction(
                transaction_date=date(2026, 5, 1),
                merchant="Store",
                amount=-40.0,
                account_id=account.id,
                category_id=category.id,
            )
        )
        session.commit()

    data = create_dashboard_data(today=TODAY, session_factory=session_factory)

    assert data.recent_transactions[0].category_name == "Groceries"


# --- budget status -------------------------------------------------------------------


def test_budget_status_is_empty_with_no_budgets_for_the_month(session_factory):
    data = create_dashboard_data(month="2026-05", today=TODAY, session_factory=session_factory)

    assert data.budget_lines == []


def test_a_budgeted_category_with_no_spending_shows_zero_actual(session_factory):
    with session_factory() as session:
        session.add(Budget(month="2026-05", category_name="Dining", budgeted_amount=200.0))
        session.commit()

    data = create_dashboard_data(month="2026-05", today=TODAY, session_factory=session_factory)

    assert len(data.budget_lines) == 1
    line = data.budget_lines[0]
    assert line.actual_amount == 0.0
    assert line.variance == 200.0
    assert not line.is_over_budget


def test_overspent_categories_are_flagged_and_sorted_first(session_factory):
    with session_factory() as session:
        account = Account(name="Checking", account_type="checking", current_balance=1000.0)
        dining = Category(name="Dining", category_type="expense")
        groceries = Category(name="Groceries", category_type="expense")
        session.add_all([account, dining, groceries])
        session.flush()

        session.add_all(
            [
                Budget(month="2026-05", category_name="Dining", budgeted_amount=100.0),
                Budget(month="2026-05", category_name="Groceries", budgeted_amount=300.0),
            ]
        )
        session.add(
            Transaction(
                transaction_date=date(2026, 5, 10),
                merchant="Restaurant",
                amount=-150.0,
                account_id=account.id,
                category_id=dining.id,
            )
        )
        session.add(
            Transaction(
                transaction_date=date(2026, 5, 11),
                merchant="Market",
                amount=-100.0,
                account_id=account.id,
                category_id=groceries.id,
            )
        )
        session.commit()

    data = create_dashboard_data(month="2026-05", today=TODAY, session_factory=session_factory)

    assert data.budget_lines[0].category_name == "Dining"
    assert data.budget_lines[0].is_over_budget
    assert data.budget_lines[0].actual_amount == 150.0
    assert data.budget_lines[1].category_name == "Groceries"
    assert not data.budget_lines[1].is_over_budget


def test_unbudgeted_categories_are_not_included(session_factory):
    with session_factory() as session:
        account = Account(name="Checking", account_type="checking", current_balance=1000.0)
        category = Category(name="Entertainment", category_type="expense")
        session.add_all([account, category])
        session.flush()
        session.add(
            Transaction(
                transaction_date=date(2026, 5, 1),
                merchant="Cinema",
                amount=-30.0,
                account_id=account.id,
                category_id=category.id,
            )
        )
        session.commit()

    data = create_dashboard_data(month="2026-05", today=TODAY, session_factory=session_factory)

    assert data.budget_lines == []
