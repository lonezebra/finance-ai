import sqlite3

import pytest
from sqlalchemy import create_engine

from finance_ai.db import models  # noqa: F401 -- registers tables on Base.metadata
from finance_ai.db.backup import (
    BackupError,
    create_backup,
    list_backups,
    prune_backups,
    restore_backup,
)
from finance_ai.db.database import Base


def make_database(path, account_name: str = "Checking") -> None:
    engine = create_engine(f"sqlite:///{path}", future=True)
    Base.metadata.create_all(engine)

    with engine.begin() as connection:
        connection.exec_driver_sql(
            "INSERT INTO accounts (name, account_type, current_balance) "
            f"VALUES ('{account_name}', 'checking', 1000.0)"
        )

    engine.dispose()


def account_names(path) -> list[str]:
    conn = sqlite3.connect(path)
    try:
        return [row[0] for row in conn.execute("SELECT name FROM accounts ORDER BY name")]
    finally:
        conn.close()


@pytest.fixture
def db_path(tmp_path):
    path = tmp_path / "finance.db"
    make_database(path)
    return path


@pytest.fixture
def backup_dir(tmp_path):
    return tmp_path / "backups"


# --- create ------------------------------------------------------------------------------


def test_create_backup_produces_a_readable_copy(db_path, backup_dir):
    backup_path = create_backup(db_path=db_path, backup_dir=backup_dir)

    assert backup_path.exists()
    assert backup_path.parent == backup_dir
    assert account_names(backup_path) == ["Checking"]


def test_create_backup_does_not_modify_the_source(db_path, backup_dir):
    create_backup(db_path=db_path, backup_dir=backup_dir)

    assert account_names(db_path) == ["Checking"]


def test_create_backup_applies_an_optional_label(db_path, backup_dir):
    backup_path = create_backup(label="pre-migration", db_path=db_path, backup_dir=backup_dir)

    assert "pre-migration" in backup_path.name
    assert list_backups(backup_dir)[0].label == "pre-migration"


def test_description_translates_open_cfos_own_labels_into_plain_language(db_path, backup_dir):
    """The two labels Open CFO applies on its own ("pre-migration", "pre-restore") are
    filename slugs, not prose meant for a user to read -- .description is what the UI and
    CLI show instead."""

    create_backup(label="pre-migration", db_path=db_path, backup_dir=backup_dir)

    description = list_backups(backup_dir)[0].description
    assert description != "pre-migration"
    assert "automatic" in description


def test_description_passes_through_a_user_supplied_label_unchanged(db_path, backup_dir):
    create_backup(label="before big import", db_path=db_path, backup_dir=backup_dir)

    backup = list_backups(backup_dir)[0]
    assert backup.description == backup.label == "before-big-import"


def test_labels_are_slugified_into_safe_filenames(db_path, backup_dir):
    backup_path = create_backup(
        label="Before The Big Import!", db_path=db_path, backup_dir=backup_dir
    )

    assert "before-the-big-import" in backup_path.name
    assert " " not in backup_path.name


def test_backups_taken_in_the_same_second_do_not_overwrite_each_other(db_path, backup_dir):
    first = create_backup(db_path=db_path, backup_dir=backup_dir)
    second = create_backup(db_path=db_path, backup_dir=backup_dir)

    assert first != second
    assert first.exists() and second.exists()


def test_create_backup_fails_clearly_when_there_is_no_database(tmp_path, backup_dir):
    with pytest.raises(BackupError, match="no database to back up"):
        create_backup(db_path=tmp_path / "nonexistent.db", backup_dir=backup_dir)


def test_create_backup_creates_the_backup_directory_if_missing(db_path, tmp_path):
    target = tmp_path / "does" / "not" / "exist"

    backup_path = create_backup(db_path=db_path, backup_dir=target)

    assert backup_path.exists()


# --- list --------------------------------------------------------------------------------


def test_list_backups_is_empty_when_none_exist(backup_dir):
    assert list_backups(backup_dir) == []


def test_list_backups_returns_newest_first(db_path, backup_dir):
    create_backup(label="first", db_path=db_path, backup_dir=backup_dir)
    create_backup(label="second", db_path=db_path, backup_dir=backup_dir)
    create_backup(label="third", db_path=db_path, backup_dir=backup_dir)

    labels = [backup.label for backup in list_backups(backup_dir)]

    assert labels[0] == "third"
    assert labels[-1] == "first"


def test_list_backups_ignores_unrelated_files(db_path, backup_dir):
    create_backup(db_path=db_path, backup_dir=backup_dir)
    (backup_dir / "notes.txt").write_text("not a backup")
    (backup_dir / "finance-garbage.db").write_bytes(b"")

    backups = list_backups(backup_dir)

    assert len(backups) == 1


# --- restore -----------------------------------------------------------------------------


def test_restore_replaces_the_live_database(db_path, backup_dir):
    backup_path = create_backup(db_path=db_path, backup_dir=backup_dir)

    # Change the live database after the backup was taken.
    conn = sqlite3.connect(db_path)
    conn.execute(
        "INSERT INTO accounts (name, account_type, current_balance) "
        "VALUES ('Added Later', 'savings', 5.0)"
    )
    conn.commit()
    conn.close()
    assert account_names(db_path) == ["Added Later", "Checking"]

    restore_backup(backup_path, db_path=db_path, backup_dir=backup_dir)

    assert account_names(db_path) == ["Checking"]


def test_restore_saves_the_replaced_database_first(db_path, backup_dir):
    backup_path = create_backup(label="original", db_path=db_path, backup_dir=backup_dir)

    conn = sqlite3.connect(db_path)
    conn.execute(
        "INSERT INTO accounts (name, account_type, current_balance) "
        "VALUES ('Would Be Lost', 'savings', 5.0)"
    )
    conn.commit()
    conn.close()

    safety_backup = restore_backup(backup_path, db_path=db_path, backup_dir=backup_dir)

    # The state that was overwritten is still recoverable.
    assert "pre-restore" in safety_backup.name
    assert "Would Be Lost" in account_names(safety_backup)


def test_restore_rejects_a_file_that_is_not_a_database(db_path, backup_dir, tmp_path):
    junk = tmp_path / "junk.db"
    junk.write_text("this is not a sqlite database")

    with pytest.raises(BackupError):
        restore_backup(junk, db_path=db_path, backup_dir=backup_dir)

    # The live database is untouched.
    assert account_names(db_path) == ["Checking"]


def test_restore_rejects_a_database_without_the_apps_schema(db_path, backup_dir, tmp_path):
    stranger = tmp_path / "stranger.db"
    conn = sqlite3.connect(stranger)
    conn.execute("CREATE TABLE unrelated (id INTEGER)")
    conn.commit()
    conn.close()

    with pytest.raises(BackupError, match="doesn't look like an Open CFO database"):
        restore_backup(stranger, db_path=db_path, backup_dir=backup_dir)

    assert account_names(db_path) == ["Checking"]


def test_restore_fails_clearly_when_the_backup_is_missing(db_path, backup_dir, tmp_path):
    with pytest.raises(BackupError, match="doesn't exist"):
        restore_backup(tmp_path / "nope.db", db_path=db_path, backup_dir=backup_dir)


def test_restore_works_when_there_is_no_live_database_to_replace(tmp_path, backup_dir):
    source = tmp_path / "source.db"
    make_database(source, account_name="FromBackup")
    backup_path = create_backup(db_path=source, backup_dir=backup_dir)

    fresh_target = tmp_path / "fresh" / "finance.db"
    restore_backup(backup_path, db_path=fresh_target, backup_dir=backup_dir)

    assert account_names(fresh_target) == ["FromBackup"]


# --- prune -------------------------------------------------------------------------------


def test_prune_keeps_the_newest_and_removes_the_rest(db_path, backup_dir):
    for index in range(5):
        create_backup(label=f"b{index}", db_path=db_path, backup_dir=backup_dir)

    removed = prune_backups(keep=2, backup_dir=backup_dir)

    remaining = list_backups(backup_dir)
    assert len(remaining) == 2
    assert len(removed) == 3
    # The two survivors are the newest.
    assert {backup.label for backup in remaining} == {"b3", "b4"}


def test_prune_is_a_no_op_when_under_the_limit(db_path, backup_dir):
    create_backup(db_path=db_path, backup_dir=backup_dir)

    removed = prune_backups(keep=10, backup_dir=backup_dir)

    assert removed == []
    assert len(list_backups(backup_dir)) == 1


def test_prune_rejects_a_negative_keep(backup_dir):
    with pytest.raises(BackupError):
        prune_backups(keep=-1, backup_dir=backup_dir)
