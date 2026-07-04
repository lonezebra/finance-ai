import sys

from PySide6.QtWidgets import QApplication

from finance_ai.core.bootstrap import bootstrap_app
from finance_ai.ui.main_window import MainWindow


def run_app():
    bootstrap_app()

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    run_app()