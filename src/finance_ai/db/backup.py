import logging
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from finance_ai.config import BACKUP_DIR, DB_PATH

logger = logging.getLogger(__name__)

BACKUP_PREFIX = "finance"
BACKUP_SUFFIX = ".db"
TIMESTAMP_FORMAT = "%Y%m%d-%H%M%S"


class BackupError(RuntimeError):
    """Raised when a backup or restore can't be completed. Carries a message intended to be
    shown to a non-technical user, per the error-handling requirement in CLAUDE.md Rule 8."""


@dataclass(frozen=True)
class BackupInfo:
    path: Path
    created_at: datetime
    size_bytes: int

    @property
    def label(self) -> str:
        """The optional trailing tag in the filename (e.g. "pre-migration"), or "" if none."""

        stem = self.path.stem
        parts = stem.split("-", 3)  # finance, YYYYMMDD, HHMMSS, [label]
        return parts[3] if len(parts) > 3 else ""


def _slugify(label: str) -> str:
    cleaned = "".join(char if char.isalnum() else "-" for char in label.strip().lower())
    return "-".join(part for part in cleaned.split("-") if part)


def create_backup(
    label: str | None = None,
    db_path: Path | str | None = None,
    backup_dir: Path | str | None = None,
) -> Path:
    """Copy the database to a timestamped file in backup_dir and return its path.

    Uses sqlite3's native backup API rather than a plain file copy. A file copy of a live
    SQLite database can capture a torn state if a write is in flight or a WAL/journal is
    present; Connection.backup() takes a consistent snapshot even while the source is open,
    which matters here because this runs from inside the app.

    The finished backup is opened and integrity-checked before being returned -- a backup
    that can't be restored is worse than no backup, because it looks like protection.
    """

    source_path = Path(db_path) if db_path is not None else DB_PATH
    target_dir = Path(backup_dir) if backup_dir is not None else BACKUP_DIR

    if not source_path.exists():
        raise BackupError(
            f"There's no database to back up yet at {source_path}. "
            "Run the app or `make init-db` first."
        )

    target_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime(TIMESTAMP_FORMAT)
    name = f"{BACKUP_PREFIX}-{timestamp}"
    if label:
        slug = _slugify(label)
        if slug:
            name = f"{name}-{slug}"

    target_path = target_dir / f"{name}{BACKUP_SUFFIX}"

    # Two backups inside the same second would otherwise collide silently.
    counter = 2
    while target_path.exists():
        target_path = target_dir / f"{name}-{counter}{BACKUP_SUFFIX}"
        counter += 1

    try:
        with sqlite3.connect(source_path) as source, sqlite3.connect(target_path) as destination:
            source.backup(destination)
    except sqlite3.Error as exc:
        target_path.unlink(missing_ok=True)
        raise BackupError(f"Could not back up the database: {exc}") from exc

    _verify_backup(target_path)

    logger.info("Created database backup at %s", target_path)
    return target_path


def _verify_backup(path: Path) -> None:
    try:
        with sqlite3.connect(path) as connection:
            result = connection.execute("PRAGMA integrity_check").fetchone()
    except sqlite3.Error as exc:
        path.unlink(missing_ok=True)
        raise BackupError(f"The backup was written but could not be read back: {exc}") from exc

    if not result or result[0] != "ok":
        path.unlink(missing_ok=True)
        raise BackupError(
            "The backup failed its integrity check and has been discarded. "
            "The original database was not modified."
        )


def list_backups(backup_dir: Path | str | None = None) -> list[BackupInfo]:
    """Available backups, newest first. Ordered by the timestamp in the filename via the
    name itself (the format sorts lexicographically), not by mtime -- copying or restoring
    a backup can change mtime, but the recorded creation time shouldn't move."""

    target_dir = Path(backup_dir) if backup_dir is not None else BACKUP_DIR

    if not target_dir.exists():
        return []

    backups = []

    for path in target_dir.glob(f"{BACKUP_PREFIX}-*{BACKUP_SUFFIX}"):
        created_at = _parse_timestamp(path)
        if created_at is None:
            continue  # not one of ours; leave unrecognized files alone
        backups.append(
            BackupInfo(path=path, created_at=created_at, size_bytes=path.stat().st_size)
        )

    return sorted(backups, key=lambda backup: (backup.created_at, backup.path.name), reverse=True)


def _parse_timestamp(path: Path) -> datetime | None:
    parts = path.stem.split("-")
    if len(parts) < 3:
        return None

    try:
        return datetime.strptime(f"{parts[1]}-{parts[2]}", TIMESTAMP_FORMAT)
    except ValueError:
        return None


def restore_backup(
    backup_path: Path | str,
    db_path: Path | str | None = None,
    backup_dir: Path | str | None = None,
) -> Path:
    """Replace the live database with a backup. Returns the path of the safety backup taken
    of the database that was replaced.

    Restoring is destructive, so the database being overwritten is itself backed up first
    (labelled "pre-restore"). If the restore goes wrong, or the user picks the wrong file,
    the previous state is still recoverable rather than gone.
    """

    source = Path(backup_path)
    target_path = Path(db_path) if db_path is not None else DB_PATH

    if not source.exists():
        raise BackupError(f"That backup file doesn't exist: {source}")

    _verify_backup_readable(source)

    safety_backup: Path | None = None
    if target_path.exists():
        safety_backup = create_backup(
            label="pre-restore", db_path=target_path, backup_dir=backup_dir
        )

    target_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with sqlite3.connect(source) as source_connection, sqlite3.connect(
            target_path
        ) as destination:
            source_connection.backup(destination)
    except sqlite3.Error as exc:
        raise BackupError(
            f"Could not restore from {source.name}: {exc}. "
            + (
                f"Your previous database was saved to {safety_backup} and is unchanged."
                if safety_backup
                else "No changes were made."
            )
        ) from exc

    logger.info("Restored database from %s (previous state saved to %s)", source, safety_backup)
    return safety_backup if safety_backup else target_path


def _verify_backup_readable(path: Path) -> None:
    """Refuse to restore from a file that isn't a readable SQLite database with this app's
    schema -- better to fail before overwriting anything than halfway through."""

    try:
        with sqlite3.connect(path) as connection:
            tables = {
                row[0]
                for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")
            }
    except sqlite3.Error as exc:
        raise BackupError(f"{path.name} isn't a readable database file: {exc}") from exc

    if "accounts" not in tables:
        raise BackupError(
            f"{path.name} doesn't look like an Open CFO database "
            "(no accounts table). Nothing was changed."
        )


def prune_backups(
    keep: int,
    backup_dir: Path | str | None = None,
) -> list[Path]:
    """Delete all but the `keep` newest backups. Returns the paths removed.

    Deliberately NOT called automatically from create_backup(). Backups are the user's
    safety net and deleting them is irreversible, so it stays an explicit action rather
    than a silent side effect of taking a new one. Growth is slow in practice -- automatic
    backups only happen before a migration or a restore -- and the files are small.
    """

    if keep < 0:
        raise BackupError("Number of backups to keep can't be negative.")

    backups = list_backups(backup_dir)
    doomed = backups[keep:]

    for backup in doomed:
        backup.path.unlink(missing_ok=True)
        logger.info("Pruned old backup %s", backup.path)

    return [backup.path for backup in doomed]
