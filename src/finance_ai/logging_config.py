import logging
from logging.handlers import RotatingFileHandler

from finance_ai.config import LOG_DIR

_configured = False


def configure_logging(level: int = logging.INFO) -> None:
    """Wires the "finance_ai" logger (parent of every finance_ai.* module logger) to a
    rotating file under LOG_DIR. Idempotent -- safe to call from both the desktop app's
    and the CLI's entrypoints without double-adding handlers."""

    global _configured
    if _configured:
        return

    LOG_DIR.mkdir(parents=True, exist_ok=True)

    handler = RotatingFileHandler(
        LOG_DIR / "finance_ai.log", maxBytes=1_000_000, backupCount=3
    )
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))

    logger = logging.getLogger("finance_ai")
    logger.setLevel(level)
    logger.addHandler(handler)

    _configured = True
