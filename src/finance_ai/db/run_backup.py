"""CLI entry points for database backup and restore, behind the make targets.

Kept separate from backup.py so that module stays a pure library the desktop UI can call
without dragging argument parsing or printing along with it.
"""

import argparse
import sys

from finance_ai.db.backup import (
    BackupError,
    create_backup,
    list_backups,
    prune_backups,
    restore_backup,
)
from finance_ai.logging_config import configure_logging


def _format_size(size_bytes: int) -> str:
    if size_bytes < 1024:
        return f"{size_bytes} B"
    if size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    return f"{size_bytes / (1024 * 1024):.1f} MB"


def cmd_create(args) -> int:
    path = create_backup(label=args.label)
    print(f"Backup created: {path}")
    return 0


def cmd_list(args) -> int:
    backups = list_backups()

    if not backups:
        print("No backups yet. Run `make backup` to create one.")
        return 0

    print(f"{len(backups)} backup(s), newest first:\n")
    for backup in backups:
        label = f"  [{backup.label}]" if backup.label else ""
        print(
            f"  {backup.created_at:%Y-%m-%d %H:%M:%S}  "
            f"{_format_size(backup.size_bytes):>9}  {backup.path.name}{label}"
        )
    return 0


def cmd_restore(args) -> int:
    if not args.file:
        print(
            "Specify which backup to restore, e.g.\n"
            '  make restore file=backups/finance-20260727-215300.db\n\n'
            "Run `make list-backups` to see what's available.",
            file=sys.stderr,
        )
        return 1

    safety_backup = restore_backup(args.file)
    print(f"Restored database from {args.file}")
    print(f"Your previous database was saved to {safety_backup}")
    return 0


def cmd_prune(args) -> int:
    removed = prune_backups(keep=args.keep)

    if not removed:
        print(f"Nothing to prune -- {args.keep} or fewer backups exist.")
        return 0

    print(f"Removed {len(removed)} old backup(s), keeping the {args.keep} newest:")
    for path in removed:
        print(f"  {path.name}")
    return 0


def main(argv: list[str] | None = None) -> int:
    configure_logging()

    parser = argparse.ArgumentParser(prog="finance_ai.db.run_backup")
    subparsers = parser.add_subparsers(dest="command", required=True)

    create_parser = subparsers.add_parser("create", help="Create a new backup")
    create_parser.add_argument("--label", default=None, help="Optional tag for the filename")
    create_parser.set_defaults(func=cmd_create)

    list_parser = subparsers.add_parser("list", help="List existing backups")
    list_parser.set_defaults(func=cmd_list)

    restore_parser = subparsers.add_parser("restore", help="Restore from a backup")
    restore_parser.add_argument("--file", default=None, help="Path to the backup to restore")
    restore_parser.set_defaults(func=cmd_restore)

    prune_parser = subparsers.add_parser("prune", help="Delete all but the newest N backups")
    prune_parser.add_argument("--keep", type=int, default=10, help="How many to keep")
    prune_parser.set_defaults(func=cmd_prune)

    args = parser.parse_args(argv)

    try:
        return args.func(args)
    except BackupError as exc:
        # BackupError messages are written for a non-technical reader, so show the message
        # rather than a traceback (CLAUDE.md Rule 8).
        print(f"\n{exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
