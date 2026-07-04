from PySide6.QtWidgets import QListWidget


class Navigation(QListWidget):
    def __init__(self):
        super().__init__()

        pages = [
            "Executive Briefing",
            "Dashboard",
            "Accounts",
            "Transactions",
            "Debt",
            "Assets",
            "Budget",
            "Goals",
            "Reports",
            "AI Advisor",
            "Settings",
        ]

        self.addItems(pages)
        self.setCurrentRow(0)