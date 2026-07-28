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
    find_account_asset_overlaps,
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
        # Marked essential so this fixture represents a genuinely complete dataset --
        # otherwise the "no spending marked essential" issue fires and the
        # scores-100-with-no-issues assertions stop meaning what they say.
        category = Category(name="Groceries", category_type="expense", is_essential=True)
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


# --- account/asset overlap detection ----------------------------------------------------


def find_account_asset_overlaps_via(session_factory):
    """find_account_asset_overlaps() takes a live session; the fixture hands out a factory."""

    with session_factory() as session:
        return find_account_asset_overlaps(session)


def _add_account(session_factory, name: str, balance: float) -> None:
    with session_factory() as session:
        session.add(Account(name=name, account_type="savings", current_balance=balance))
        session.commit()


def _add_asset(session_factory, name: str, value: float) -> None:
    with session_factory() as session:
        session.add(Asset(name=name, asset_type="other", current_value=value))
        session.commit()


def test_no_overlap_is_reported_for_the_intended_disjoint_layout(session_factory):
    """The template's own layout: liquid balances in Accounts, everything else in Assets."""

    _add_account(session_factory, "Checking", 2500.0)
    _add_account(session_factory, "Savings", 10000.0)
    _add_asset(session_factory, "Home", 600000.0)
    _add_asset(session_factory, "Roth IRA", 35000.0)

    overlaps = find_account_asset_overlaps_via(session_factory)

    assert overlaps == []


def test_same_name_in_both_tables_is_detected(session_factory):
    _add_account(session_factory, "Savings", 10000.0)
    _add_asset(session_factory, "Savings", 10000.0)

    overlaps = find_account_asset_overlaps_via(session_factory)

    assert len(overlaps) == 1
    assert overlaps[0].name == "Savings"
    assert overlaps[0].amount_at_stake == 10000.0


def test_matching_ignores_case_and_surrounding_whitespace(session_factory):
    _add_account(session_factory, "  savings ", 5000.0)
    _add_asset(session_factory, "SAVINGS", 5000.0)

    assert len(find_account_asset_overlaps_via(session_factory)) == 1


def test_amount_at_stake_uses_the_smaller_of_the_two_values(session_factory):
    """If the two rows disagree, only the overlapping portion is certainly duplicated."""

    _add_account(session_factory, "Brokerage", 8000.0)
    _add_asset(session_factory, "Brokerage", 12000.0)

    assert find_account_asset_overlaps_via(session_factory)[0].amount_at_stake == 8000.0


def test_duplicate_names_within_one_table_are_aggregated_not_dropped(session_factory):
    """Account names aren't unique in the schema, so two rows can share a name."""

    _add_account(session_factory, "Savings", 4000.0)
    _add_account(session_factory, "Savings", 6000.0)
    _add_asset(session_factory, "Savings", 10000.0)

    overlaps = find_account_asset_overlaps_via(session_factory)

    assert len(overlaps) == 1
    assert overlaps[0].account_total == 10000.0


def test_overlap_lowers_the_confidence_score_with_a_high_severity_issue(session_factory):
    _add_full_dataset(session_factory, transaction_dates=[TODAY])
    _add_asset(session_factory, "Checking", 1000.0)  # collides with the account of that name

    result = calculate_financial_confidence_score(today=TODAY, session_factory=session_factory)

    assert result.score == 85
    overlap_issues = [i for i in result.issues if "both Accounts and Assets" in i.message]
    assert len(overlap_issues) == 1
    assert overlap_issues[0].severity == "high"


def test_overlap_message_names_the_entry_and_the_amount(session_factory):
    _add_full_dataset(session_factory, transaction_dates=[TODAY])
    _add_asset(session_factory, "Checking", 1000.0)

    result = calculate_financial_confidence_score(today=TODAY, session_factory=session_factory)
    message = next(i.message for i in result.issues if "both Accounts and Assets" in i.message)

    assert '"Checking"' in message
    assert "$1,000.00" in message
    assert "remove one" in message


def test_many_overlaps_are_summarized_rather_than_listed_in_full(session_factory):
    for index in range(6):
        _add_account(session_factory, f"Dup{index}", 100.0)
        _add_asset(session_factory, f"Dup{index}", 100.0)

    result = calculate_financial_confidence_score(today=TODAY, session_factory=session_factory)
    message = next(i.message for i in result.issues if "both Accounts and Assets" in i.message)

    assert "and 3 more" in message
    assert "$600.00" in message  # 6 overlaps x 100 each


def test_overlap_penalty_is_flat_regardless_of_how_many_overlap(session_factory):
    """One class of problem, charged once -- the message carries the per-entry detail."""

    _add_full_dataset(session_factory, transaction_dates=[TODAY])
    _add_asset(session_factory, "Checking", 1000.0)
    one = calculate_financial_confidence_score(today=TODAY, session_factory=session_factory).score

    _add_asset(session_factory, "Savings", 500.0)
    _add_account(session_factory, "Savings", 500.0)
    two = calculate_financial_confidence_score(today=TODAY, session_factory=session_factory).score

    assert one == two


def test_detection_does_not_change_total_assets(session_factory):
    """Detection reports; it must never silently adjust the headline number."""

    from finance_ai.finance.metrics import get_total_assets

    _add_account(session_factory, "Savings", 10000.0)
    _add_asset(session_factory, "Savings", 10000.0)

    with session_factory() as session:
        assert get_total_assets(session) == 20000.0  # still double-counted, by design
