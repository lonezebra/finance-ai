from finance_ai.config import BACKUP_DIR, DATA_DIR, EXPORT_DIR, IMPORT_DIR, LOG_DIR, REPORT_DIR
from finance_ai.db.migrate import ensure_schema_up_to_date
from finance_ai.logging_config import configure_logging


def ensure_directories() -> None:
    for directory in [
        DATA_DIR,
        IMPORT_DIR,
        EXPORT_DIR,
        BACKUP_DIR,
        LOG_DIR,
        REPORT_DIR,
    ]:
        directory.mkdir(parents=True, exist_ok=True)


def bootstrap_app() -> None:
    ensure_directories()
    configure_logging()
    ensure_schema_up_to_date()