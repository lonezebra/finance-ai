import os
from PySide6.QtCore import QLibraryInfo


def configure_qt() -> None:
    plugin_path = QLibraryInfo.path(QLibraryInfo.PluginsPath)

    if plugin_path:
        os.environ.setdefault("QT_QPA_PLATFORM_PLUGIN_PATH", plugin_path)