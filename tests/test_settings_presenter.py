import tkinter
from datetime import datetime
from pathlib import Path

from finance_ai.db.backup import BackupError, BackupInfo
from finance_ai.ui.presenters.settings_presenter import SettingsPresenter


def make_backup(name: str = "finance-20260728-010000.db", size: int = 61440) -> BackupInfo:
    return BackupInfo(
        path=Path("backups") / name,
        created_at=datetime(2026, 7, 28, 1, 0, 0),
        size_bytes=size,
    )


def make_presenter(**overrides) -> SettingsPresenter:
    defaults = {
        "create_backup_fn": lambda label=None: Path("backups/finance-new.db"),
        "list_backups_fn": lambda: [make_backup()],
        "restore_backup_fn": lambda path: Path("backups/finance-pre-restore.db"),
    }
    defaults.update(overrides)
    return SettingsPresenter(**defaults)


# --- listing ------------------------------------------------------------------------------


def test_attaching_loads_the_backup_list_immediately():
    presenter = make_presenter()
    calls = []

    presenter.attach(on_change=lambda: calls.append(len(presenter.backups)))

    assert presenter.backups == [make_backup()]
    assert calls == [1]


def test_a_listing_failure_becomes_a_status_message_not_a_crash():
    """The Settings page failing to open is worse than it opening with a note that the
    backups folder couldn't be read."""

    def boom():
        raise OSError("permission denied")

    presenter = make_presenter(list_backups_fn=boom)
    presenter.attach(on_change=lambda: None)

    assert presenter.backups == []
    assert presenter.status is not None
    assert presenter.status.is_error
    assert "permission denied" in presenter.status.text


# --- creating -----------------------------------------------------------------------------


def test_creating_a_backup_reports_the_filename_and_refreshes_the_list():
    listings = [[], [make_backup()]]
    presenter = make_presenter(list_backups_fn=lambda: listings.pop(0))
    presenter.attach(on_change=lambda: None)

    assert presenter.backups == []

    presenter.create_backup()

    assert "finance-new.db" in presenter.status.text
    assert not presenter.status.is_error
    assert len(presenter.backups) == 1  # list was reloaded after the write


def test_a_blank_label_is_passed_as_none_rather_than_an_empty_string():
    captured = {}

    def create(label=None):
        captured["label"] = label
        return Path("backups/finance-new.db")

    presenter = make_presenter(create_backup_fn=create)
    presenter.attach(on_change=lambda: None)

    presenter.create_backup("   ")

    assert captured["label"] is None


def test_a_label_is_trimmed_before_use():
    captured = {}

    def create(label=None):
        captured["label"] = label
        return Path("backups/finance-new.db")

    presenter = make_presenter(create_backup_fn=create)
    presenter.attach(on_change=lambda: None)

    presenter.create_backup("  before import  ")

    assert captured["label"] == "before import"


def test_a_failed_backup_surfaces_the_friendly_message():
    def boom(label=None):
        raise BackupError("There's no database to back up yet.")

    presenter = make_presenter(create_backup_fn=boom)
    presenter.attach(on_change=lambda: None)

    presenter.create_backup()

    assert presenter.status.is_error
    assert "no database to back up" in presenter.status.text


# --- restoring ----------------------------------------------------------------------------


def test_restore_names_the_safety_backup_so_the_user_knows_it_is_undoable():
    presenter = make_presenter()
    presenter.attach(on_change=lambda: None)

    presenter.restore(Path("backups/finance-20260728-010000.db"))

    assert not presenter.status.is_error
    assert "finance-20260728-010000.db" in presenter.status.text
    assert "finance-pre-restore.db" in presenter.status.text


def test_restore_explains_which_parts_of_the_app_will_still_look_stale():
    """The database is live immediately, but a previously generated AI narrative isn't --
    saying so precisely beats a vague "you might need to restart"."""

    presenter = make_presenter()
    presenter.attach(on_change=lambda: None)

    presenter.restore(Path("backups/finance-20260728-010000.db"))

    assert "reload when you visit them again" in presenter.status.text
    assert "generate it again" in presenter.status.text


def test_a_failed_restore_surfaces_the_friendly_message():
    def boom(path):
        raise BackupError("That file doesn't look like an Open CFO database.")

    presenter = make_presenter(restore_backup_fn=boom)
    presenter.attach(on_change=lambda: None)

    presenter.restore(Path("backups/junk.db"))

    assert presenter.status.is_error
    assert "doesn't look like an Open CFO database" in presenter.status.text


def test_restore_reloads_the_backup_list_afterwards():
    """A restore creates a pre-restore safety backup, so the list has changed."""

    listings = [[make_backup()], [make_backup(), make_backup("finance-pre-restore.db")]]
    presenter = make_presenter(list_backups_fn=lambda: listings.pop(0))
    presenter.attach(on_change=lambda: None)

    presenter.restore(Path("backups/finance-20260728-010000.db"))

    assert len(presenter.backups) == 2


# --- lifecycle ----------------------------------------------------------------------------


def test_detaching_stops_notifications():
    presenter = make_presenter()
    calls = []
    presenter.attach(on_change=lambda: calls.append(1))
    presenter.detach()

    presenter.create_backup()

    assert len(calls) == 1  # only the attach() call


def test_dead_widget_callback_self_heals_instead_of_raising():
    presenter = make_presenter()
    call_count = {"n": 0}

    def flaky():
        call_count["n"] += 1
        if call_count["n"] > 1:
            raise tkinter.TclError('invalid command name ".!label"')

    presenter.attach(on_change=flaky)

    presenter.create_backup()  # must not raise

    assert presenter._on_change is None
