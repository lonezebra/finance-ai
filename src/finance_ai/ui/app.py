from finance_ai.core.bootstrap import bootstrap_app
from finance_ai.ui.main_window import MainWindow


def run_app():
    bootstrap_app()
    app = MainWindow()
    app.mainloop()


if __name__ == "__main__":
    run_app()