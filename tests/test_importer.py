from datetime import date

import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from finance_ai.db import models  # noqa: F401 -- registers tables on Base.metadata
from finance_ai.db.database import Base
from finance_ai.db.models import Account, Budget, Category, Debt, Goal, ImportBatch, Transaction
from finance_ai.imports.importer import import_dataset
from finance_ai.imports.mapper import (
    AccountImport,
    AssetImport,
    BudgetImport,
    CategoryImport,
    DebtImport,
    GoalImport,
    ImportDataset,
    TransactionImport,
)


@pytest.fixture
def session_factory():
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def make_dataset(
    *,
    accounts=(),
    categories=(),
    transactions=(),
    debts=(),
    assets=(),
    budgets=(),
    goals=(),
) -> ImportDataset:
    return ImportDataset(
        accounts=list(accounts),
        categories=list(categories),
        transactions=list(transactions),
        debts=list(debts),
        assets=list(assets),
        budgets=list(budgets),
        goals=list(goals),
    )


def test_first_import_creates_everything(session_factory):
    dataset = make_dataset(
        accounts=[AccountImport("Checking", "checking", "Bank", 1000.0, None)],
        categories=[CategoryImport("Salary", "income")],
        transactions=[
            TransactionImport(date(2026, 6, 1), "Employer", "Paycheck", 2000.0, "Checking", "Salary", None)
        ],
        debts=[DebtImport("Credit Card", "Bank", 500.0, 20.0, 25.0, 5, None)],
        assets=[AssetImport("Car", "vehicle", 8000.0, None)],
        budgets=[BudgetImport("2026-06", "Salary", 0.0)],
        goals=[GoalImport("Emergency Fund", 10000.0, 2000.0, date(2027, 1, 1), None)],
    )

    result = import_dataset(dataset, source_file="demo.xlsx", session_factory=session_factory)

    assert result.accounts.created == 1
    assert result.categories.created == 1
    assert result.transactions.created == 1
    assert result.debts.created == 1
    assert result.assets.created == 1
    assert result.budgets.created == 1
    assert result.goals.created == 1

    with session_factory() as session:
        assert session.query(Account).count() == 1
        assert session.query(ImportBatch).count() == 1


def test_reimporting_identical_workbook_updates_instead_of_duplicating(session_factory):
    dataset = make_dataset(
        accounts=[AccountImport("Checking", "checking", "Bank", 1000.0, None)],
        categories=[CategoryImport("Salary", "income")],
        transactions=[
            TransactionImport(date(2026, 6, 1), "Employer", "Paycheck", 2000.0, "Checking", "Salary", None)
        ],
        debts=[DebtImport("Credit Card", "Bank", 500.0, 20.0, 25.0, 5, None)],
        assets=[AssetImport("Car", "vehicle", 8000.0, None)],
        budgets=[BudgetImport("2026-06", "Salary", 0.0)],
        goals=[GoalImport("Emergency Fund", 10000.0, 2000.0, date(2027, 1, 1), None)],
    )

    import_dataset(dataset, source_file="demo.xlsx", session_factory=session_factory)
    result = import_dataset(dataset, source_file="demo.xlsx", session_factory=session_factory)

    assert result.accounts.created == 0
    assert result.accounts.updated == 1
    assert result.categories.created == 0
    assert result.categories.updated == 1
    assert result.debts.created == 0
    assert result.debts.updated == 1
    assert result.assets.created == 0
    assert result.assets.updated == 1
    assert result.budgets.created == 0
    assert result.budgets.updated == 1
    assert result.goals.created == 0
    assert result.goals.updated == 1

    # The transaction is an exact repeat -- skipped, not duplicated.
    assert result.transactions.created == 0
    assert result.transactions.skipped_duplicate == 1

    with session_factory() as session:
        assert session.query(Account).count() == 1
        assert session.query(Category).count() == 1
        assert session.query(Debt).count() == 1
        assert session.query(Transaction).count() == 1
        assert session.query(Budget).count() == 1
        assert session.query(Goal).count() == 1
        assert session.query(ImportBatch).count() == 2


def test_reimport_with_updated_balance_refreshes_existing_account(session_factory):
    first = make_dataset(accounts=[AccountImport("Checking", "checking", "Bank", 1000.0, None)])
    import_dataset(first, source_file="demo.xlsx", session_factory=session_factory)

    second = make_dataset(accounts=[AccountImport("Checking", "checking", "Bank", 1500.0, "Updated")])
    result = import_dataset(second, source_file="demo.xlsx", session_factory=session_factory)

    assert result.accounts.created == 0
    assert result.accounts.updated == 1

    with session_factory() as session:
        accounts = session.query(Account).all()
        assert len(accounts) == 1
        assert accounts[0].current_balance == 1500.0
        assert accounts[0].notes == "Updated"


def test_reimport_with_new_transaction_adds_it_alongside_existing(session_factory):
    account = [AccountImport("Checking", "checking", "Bank", 1000.0, None)]
    category = [CategoryImport("Salary", "income")]

    first = make_dataset(
        accounts=account,
        categories=category,
        transactions=[
            TransactionImport(date(2026, 6, 1), "Employer", "Paycheck", 2000.0, "Checking", "Salary", None)
        ],
    )
    import_dataset(first, source_file="demo.xlsx", session_factory=session_factory)

    second = make_dataset(
        accounts=account,
        categories=category,
        transactions=[
            TransactionImport(date(2026, 6, 1), "Employer", "Paycheck", 2000.0, "Checking", "Salary", None),
            TransactionImport(date(2026, 6, 15), "Employer", "Bonus", 500.0, "Checking", "Salary", None),
        ],
    )
    result = import_dataset(second, source_file="demo.xlsx", session_factory=session_factory)

    assert result.transactions.created == 1
    assert result.transactions.skipped_duplicate == 1

    with session_factory() as session:
        assert session.query(Transaction).count() == 2


def test_duplicate_rows_within_a_single_workbook_do_not_double_import(session_factory):
    dataset = make_dataset(
        accounts=[
            AccountImport("Checking", "checking", "Bank", 1000.0, None),
            AccountImport("Checking", "checking", "Bank", 1000.0, None),
        ],
        budgets=[
            BudgetImport("2026-06", "Groceries", 400.0),
            BudgetImport("2026-06", "Groceries", 450.0),
        ],
    )

    result = import_dataset(dataset, source_file="demo.xlsx", session_factory=session_factory)

    assert result.accounts.created == 1
    assert result.accounts.updated == 1
    assert result.budgets.created == 1
    assert result.budgets.updated == 1

    with session_factory() as session:
        assert session.query(Account).count() == 1
        assert session.query(Budget).count() == 1
        assert session.query(Budget).first().budgeted_amount == 450.0


def test_failed_import_rolls_back_and_does_not_record_a_batch(session_factory):
    # amount is NOT NULL at the DB level; None reliably triggers an IntegrityError at
    # commit time regardless of SQLite's otherwise-loose column typing.
    dataset = make_dataset(
        transactions=[
            TransactionImport(date(2026, 6, 1), "Employer", "Paycheck", None, "Checking", "Salary", None)
        ]
    )

    with pytest.raises(IntegrityError):
        import_dataset(dataset, source_file="demo.xlsx", session_factory=session_factory)

    with session_factory() as session:
        assert session.query(ImportBatch).count() == 0
        assert session.query(Transaction).count() == 0


def test_reimport_without_the_essential_column_does_not_wipe_existing_markings(session_factory):
    """A workbook created before the Essential column existed reports is_essential=None
    ("not stated"). Treating that as "no" would silently clear markings the user had already
    made, just because they re-imported an older file."""

    marked = make_dataset(categories=[CategoryImport("Groceries", "expense", is_essential=True)])
    import_dataset(marked, source_file="new.xlsx", session_factory=session_factory)

    with session_factory() as session:
        assert session.query(Category).one().is_essential is True

    # An older workbook: same category, no Essential column, so is_essential is None.
    older = make_dataset(categories=[CategoryImport("Groceries", "expense")])
    import_dataset(older, source_file="old.xlsx", session_factory=session_factory)

    with session_factory() as session:
        assert session.query(Category).one().is_essential is True  # preserved, not cleared


def test_reimport_can_explicitly_change_a_marking(session_factory):
    """An explicit "no" must still take effect -- only None is treated as "leave alone"."""

    marked = make_dataset(categories=[CategoryImport("Restaurants", "expense", is_essential=True)])
    import_dataset(marked, source_file="a.xlsx", session_factory=session_factory)

    unmarked = make_dataset(
        categories=[CategoryImport("Restaurants", "expense", is_essential=False)]
    )
    import_dataset(unmarked, source_file="b.xlsx", session_factory=session_factory)

    with session_factory() as session:
        assert session.query(Category).one().is_essential is False
