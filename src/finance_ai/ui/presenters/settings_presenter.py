import tkinter
from dataclasses import dataclass
from pathlib import Path

from finance_ai.db.backup import (
    BackupError,
    BackupInfo,
    create_backup,
    list_backups,
    restore_backup,
)


@dataclass(frozen=True)
class StatusMessage:
    text: str
    is_error: bool = False


# Shown after a successful restore. The database itself is fully live immediately -- verified
# that even a session held open across a restore reads the restored data, because SQLite's
# backup API rewrites the destination file's pages in place. What *doesn't* refresh is any
# text a presenter has already cached, so the message says exactly which parts to expect
# stale rather than a vague "you may need to restart".
RESTORE_FOLLOW_UP = (
    "Your data has been replaced. The figures on other pages reload when you visit them "
    "again. An AI briefing or scenario explanation generated before the restore still "
    "describes the old data until you generate it again."
)


class SettingsPresenter:
    """Backup and restore for the Settings page.

    All four backup functions are injectable so this can be tested without touching the
    real database or the user's backups directory -- the same pattern as
    import_dataset()'s session_factory and migrate.py's db_path.
    """

    def __init__(
        self,
        create_backup_fn=create_backup,
        list_backups_fn=list_backups,
        restore_backup_fn=restore_backup,
    ):
        self._create_backup = create_backup_fn
        self._list_backups = list_backups_fn
        self._restore_backup = restore_backup_fn

        self.backups: list[BackupInfo] = []
        self.status: StatusMessage | None = None
        self._on_change = None

    def attach(self, on_change) -> None:
        self._on_change = on_change
        self.refresh()

    def detach(self) -> None:
        self._on_change = None

    def refresh(self) -> None:
        """Reload the backup list. Never raises -- a listing failure becomes a status
        message, because the Settings page failing to open is worse than it opening with a
        note that the backups folder couldn't be read."""

        try:
            self.backups = self._list_backups()
        except BackupError as exc:
            self.backups = []
            self.status = StatusMessage(str(exc), is_error=True)
        except OSError as exc:
            self.backups = []
            self.status = StatusMessage(f"Could not read the backups folder: {exc}", is_error=True)

        self._notify()

    def create_backup(self, label: str | None = None) -> None:
        label = (label or "").strip() or None

        try:
            path = self._create_backup(label=label)
        except BackupError as exc:
            self.status = StatusMessage(str(exc), is_error=True)
            self._notify()
            return

        self.status = StatusMessage(f"Backup saved as {path.name}")
        self.refresh()

    def restore(self, backup_path: Path | str) -> None:
        """Replace the live database with a backup. The view is responsible for confirming
        with the user first -- keeping the dialog out of here means this stays testable."""

        try:
            safety_backup = self._restore_backup(backup_path)
        except BackupError as exc:
            self.status = StatusMessage(str(exc), is_error=True)
            self._notify()
            return

        self.status = StatusMessage(
            f"Restored from {Path(backup_path).name}. Your previous data was saved as "
            f"{Path(safety_backup).name} in case you want it back. {RESTORE_FOLLOW_UP}"
        )
        self.refresh()

    def _notify(self) -> None:
        if not self._on_change:
            return

        try:
            self._on_change()
        except tkinter.TclError:
            # Same race as the other presenters: <Destroy> and an already-scheduled callback
            # aren't strictly ordered, so this can fire against a torn-down widget.
            self._on_change = None
