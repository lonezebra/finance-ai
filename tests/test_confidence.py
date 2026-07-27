from datetime import date, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from finance_ai.db import models  # noqa: F401 -- registers tables on Base.metadata
from finance_ai.db.database import Base
from finance_ai.db.models import Account, Asset, Budget, Category, Debt, Goal, Transaction
from finance_ai.finance.confidence import (
    STALE_AFTER_DAYS,
    VERY_STALE_AFTER_DAYS,
    calculate_financial_confidence_score,
)

TODAY = date(2026, 6, 15)


@pytest.fixture
def session_factory():
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def _add_full_dataset(session_factory, *, transaction_dates):
    with session_factory() as session:
        account = Account(name="Checking", account_type="checking", current_balance=1000.0)
        category = Category(name="Groceries", category_type="expense")
        session.add_all([account, category])
        session.flush()

        for transaction_date in transaction_dates:
            session.add(
                Transaction(
                    transaction_date=transaction_date,
                    merchant="Store",
                    amount=-50.0,
                    account_id=account.id,
                    category_id=category.id,
                )
            )

        session.add(Debt(name="Credit Card", balance=500.0, interest_rate=20.0))
        session.add(Asset(name="Car", asset_type="vehicle", current_value=8000.0))
        session.add(Budget(month="2026-06", category_name="Groceries", budgeted_amount=400.0))
        session.add(Goal(name="Emergency Fund", target_amount=10000.0))
        session.commit()


def test_empty_database_scores_low_with_all_expected_issues(session_factory):
    result = calculate_financial_confidence_score(today=TODAY, session_factory=session_factory)

    assert result.score < 50
    messages = [issue.message for issue in result.issues]
    assert "No accounts have been added." in messages
    assert "No transactions have been imported." in messages
    assert "No categories have been added." in messages
    # No transactions at all -- the "no transactions" issue covers it; no separate
    # freshness complaint should pile on top of that.
    assert not any("days" in message for message in messages)


def test_complete_and_fresh_dataset_scores_high_with_no_issues(session_factory):
    _add_full_dataset(session_factory, transaction_dates=[TODAY])

    result = calculate_financial_confidence_score(today=TODAY, session_factory=session_factory)

    assert result.score == 100
    assert result.issues == []
    assert result.label == "High"


def test_transactions_exactly_at_the_stale_threshold_are_not_penalized(session_factory):
    _add_full_dataset(
        session_factory, transaction_dates=[TODAY - timedelta(days=STALE_AFTER_DAYS)]
    )

    result = calculate_financial_confidence_score(today=TODAY, session_factory=session_factory)

    assert result.score == 100
    assert result.issues == []


def test_moderately_stale_transactions_apply_medium_penalty(session_factory):
    stale_days = STALE_AFTER_DAYS + 15
    _add_full_dataset(session_factory, transaction_dates=[TODAY - timedelta(days=stale_days)])

    result = calculate_financial_confidence_score(today=TODAY, session_factory=session_factory)

    assert result.score == 90
    assert any(f"{stale_days} days" in issue.message for issue in result.issues)
    assert any(issue.severity == "medium" for issue in result.issues)


def test_very_stale_transactions_apply_high_penalty(session_factory):
    stale_days = VERY_STALE_AFTER_DAYS + 30
    _add_full_dataset(session_factory, transaction_dates=[TODAY - timedelta(days=stale_days)])

    result = calculate_financial_confidence_score(today=TODAY, session_factory=session_factory)

    assert result.score == 80
    assert any(f"{stale_days} days" in issue.message for issue in result.issues)
    assert any(issue.severity == "high" for issue in result.issues)


def test_freshness_is_based_on_the_most_recent_transaction_not_the_oldest(session_factory):
    _add_full_dataset(
        session_factory,
        transaction_dates=[
            TODAY - timedelta(days=VERY_STALE_AFTER_DAYS + 200),  # very old
            TODAY,  # but there's also a fresh one
        ],
    )

    result = calculate_financial_confidence_score(today=TODAY, session_factory=session_factory)

    assert result.score == 100
    assert result.issues == []
