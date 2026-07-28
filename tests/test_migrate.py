import sqlite3

from alembic.config import Config
from sqlalchemy import create_engine

from alembic import command
from finance_ai.config import PROJECT_ROOT
from finance_ai.db import models  # noqa: F401 -- registers tables on Base.metadata
from finance_ai.db.backup import list_backups
from finance_ai.db.migrate import (
    BASELINE_REVISION,
    current_revision,
    ensure_schema_up_to_date,
    head_revision,
)


def make_pre_migration_database(path) -> None:
    """Simulates an existing install from before migrations existed: the app's tables at the
    *baseline* schema, no alembic_version table, real data in it.

    Built by running the baseline migration and then dropping alembic_version, rather than
    by Base.metadata.create_all(). create_all() reflects whatever the models say *today*,
    which was identical to the baseline while only one migration existed but diverges the
    moment a second one lands -- at which point the helper would be handing the code a
    database newer than the revision it gets stamped at, and the upgrade would fail trying
    to add columns that already exist. Running the migration keeps "pre-migration" honest
    however many migrations accumulate later.
    """

    cfg = Config(str(PROJECT_ROOT / "alembic.ini"))
    cfg.set_main_option("sqlalchemy.url", f"sqlite:///{path}")
    command.upgrade(cfg, BASELINE_REVISION)

    engine = create_engine(f"sqlite:///{path}", future=True)

    with engine.begin() as connection:
        # Drop the version table so the database looks untracked, the way one created
        # before Alembic was introduced would.
        connection.exec_driver_sql("DROP TABLE alembic_version")
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

    ensure_schema_up_to_date(db_path, backup_dir=tmp_path / 'backups')

    assert current_revision(db_path) == head_revision()
    tables = table_names(db_path)
    assert "accounts" in tables
    assert "transactions" in tables
    assert "alembic_version" in tables


def test_pre_migration_database_is_stamped_without_losing_data(tmp_path):
    db_path = tmp_path / "existing.db"
    make_pre_migration_database(db_path)

    assert current_revision(db_path) is None  # not migration-tracked yet

    ensure_schema_up_to_date(db_path, backup_dir=tmp_path / 'backups')

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

    ensure_schema_up_to_date(db_path, backup_dir=tmp_path / 'backups')
    first_revision = current_revision(db_path)

    ensure_schema_up_to_date(db_path, backup_dir=tmp_path / 'backups')  # must not raise or change anything
    second_revision = current_revision(db_path)

    assert first_revision == second_revision == head_revision()


def test_pending_migrations_trigger_an_automatic_backup_first(tmp_path):
    """A pre-migration database has pending work to do, so the schema change should be
    preceded by a backup of the data as it stood before."""

    db_path = tmp_path / "existing.db"
    backup_dir = tmp_path / "backups"
    make_pre_migration_database(db_path)

    ensure_schema_up_to_date(db_path, backup_dir=backup_dir)

    backups = list_backups(backup_dir)
    assert len(backups) == 1
    assert backups[0].label == "pre-migration"
    # The backup holds the data as it was before the migration ran.
    conn = sqlite3.connect(backups[0].path)
    try:
        assert conn.execute("SELECT COUNT(*) FROM accounts").fetchone()[0] == 1
    finally:
        conn.close()


def test_no_backup_is_taken_when_the_schema_is_already_current(tmp_path):
    """ensure_schema_up_to_date() runs on every startup, so an unconditional backup would
    mean a new file per launch. Nothing pending means nothing to protect against."""

    db_path = tmp_path / "migrated.db"
    backup_dir = tmp_path / "backups"

    ensure_schema_up_to_date(db_path, backup_dir=backup_dir)
    backups_after_first = len(list_backups(backup_dir))

    ensure_schema_up_to_date(db_path, backup_dir=backup_dir)
    ensure_schema_up_to_date(db_path, backup_dir=backup_dir)

    assert len(list_backups(backup_dir)) == backups_after_first


def test_backup_before_upgrade_can_be_disabled(tmp_path):
    db_path = tmp_path / "existing.db"
    backup_dir = tmp_path / "backups"
    make_pre_migration_database(db_path)

    ensure_schema_up_to_date(db_path, backup_before_upgrade=False, backup_dir=backup_dir)

    assert list_backups(backup_dir) == []
    assert current_revision(db_path) == head_revision()


def test_current_revision_is_none_for_a_database_that_does_not_exist_yet(tmp_path):
    db_path = tmp_path / "does_not_exist.db"

    assert current_revision(db_path) is None
