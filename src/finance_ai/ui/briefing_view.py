from PySide6.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QPushButton, QLabel

from finance_ai.ui.presenters.briefing_presenter import BriefingPresenter


class BriefingView(QWidget):
    def __init__(self):
        super().__init__()

        self.presenter = BriefingPresenter()

        self.title = QLabel("Executive Briefing")
        self.text = QTextEdit()
        self.text.setReadOnly(True)

        self.refresh_button = QPushButton("Refresh Briefing")
        self.refresh_button.clicked.connect(self.refresh)

        layout = QVBoxLayout()
        layout.addWidget(self.title)
        layout.addWidget(self.text)
        layout.addWidget(self.refresh_button)

        self.setLayout(layout)

        self.refresh()

    def refresh(self):
        briefing = self.presenter.get_briefing_text()
        self.text.setPlainText(briefing)