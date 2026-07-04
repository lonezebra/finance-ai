import os
from pathlib import Path

from PySide6.QtCore import QLibraryInfo


def configure_qt() -> None:
    plugin_root = Path(QLibraryInfo.path(QLibraryInfo.PluginsPath))
    platforms_path = plugin_root / "platforms"

    if platforms_path.exists():
        os.environ.setdefault("QT_QPA_PLATFORM_PLUGIN_PATH", str(platforms_path))