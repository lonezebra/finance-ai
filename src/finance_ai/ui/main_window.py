from PySide6.QtWidgets import QHBoxLayout, QMainWindow, QWidget

from finance_ai.ui.briefing_view import BriefingView
from finance_ai.ui.navigation import Navigation


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Open CFO")
        self.resize(1200, 800)

        self.navigation = Navigation()
        self.briefing_view = BriefingView()

        root = QWidget()
        layout = QHBoxLayout()
        layout.addWidget(self.navigation, 1)
        layout.addWidget(self.briefing_view, 4)
        root.setLayout(layout)

        self.setCentralWidget(root)