import os
from pathlib import Path


def configure_qt() -> None:
    project_root = Path(__file__).resolve().parents[3]
    plugin_root = (
        project_root
        / ".venv"
        / "lib"
        / "python3.12"
        / "site-packages"
        / "PySide6"
        / "Qt"
        / "plugins"
    )
    platforms_path = plugin_root / "platforms"

    os.environ["QT_PLUGIN_PATH"] = str(plugin_root)
    os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = str(platforms_path)