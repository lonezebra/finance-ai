import sqlite3

from sqlalchemy import create_engine

from finance_ai.db import models  # noqa: F401 -- registers tables on Base.metadata
from finance_ai.db.database import Base
from finance_ai.db.migrate import current_revision, ensure_schema_up_to_date, head_revision


def make_pre_migration_database(path) -> None:
    """Simulates an existing install from before migrations existed: all app tables
    present (created the old way, via Base.metadata.create_all()), no alembic_version
    table, real data in it."""

    engine = create_engine(f"sqlite:///{path}", future=True)
    Base.metadata.create_all(engine)

    with engine.begin() as connection:
        connection.exec_driver_sql(
            "INSERT INTO accounts (name, account_type, current_balance) "
            "VALUES ('Checking', 'checking', 1000.0)"
        )

    engine.dispose()


def table_names(path) -> set[str]:
    conn = sqlite3.connect(path)
    try:
        return {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    finally:
        conn.close()


def test_fresh_database_creates_all_tables_and_reaches_head(tmp_path):
    db_path = tmp_path / "fresh.db"

    ensure_schema_up_to_date(db_path)

    assert current_revision(db_path) == head_revision()
    tables = table_names(db_path)
    assert "accounts" in tables
    assert "transactions" in tables
    assert "alembic_version" in tables


def test_pre_migration_database_is_stamped_without_losing_data(tmp_path):
    db_path = tmp_path / "existing.db"
    make_pre_migration_database(db_path)

    assert current_revision(db_path) is None  # not migration-tracked yet

    ensure_schema_up_to_date(db_path)

    assert current_revision(db_path) == head_revision()

    conn = sqlite3.connect(db_path)
    try:
        count = conn.execute("SELECT COUNT(*) FROM accounts").fetchone()[0]
        name = conn.execute("SELECT name FROM accounts").fetchone()[0]
    finally:
        conn.close()

    assert count == 1
    assert name == "Checking"


def test_already_migrated_database_is_idempotent(tmp_path):
    db_path = tmp_path / "migrated.db"

    ensure_schema_up_to_date(db_path)
    first_revision = current_revision(db_path)

    ensure_schema_up_to_date(db_path)  # must not raise or change anything
    second_revision = current_revision(db_path)

    assert first_revision == second_revision == head_revision()


def test_current_revision_is_none_for_a_database_that_does_not_exist_yet(tmp_path):
    db_path = tmp_path / "does_not_exist.db"

    assert current_revision(db_path) is None
