import customtkinter as ctk

from finance_ai.ui.presenters.dashboard_presenter import DashboardPresenter
from finance_ai.ui.report_cards import (
    build_accounts_card,
    build_assets_card,
    build_budget_status_card,
    build_debts_card,
    build_recent_transactions_card,
    build_snapshot_card,
)

ERROR_COLOR = "#d9534f"


class DashboardView(ctk.CTkFrame):
    """The fast, no-AI landing page: current balances, recent activity, and budget status.

    Unlike BriefingView, there's no generate step and no background thread -- every card is
    a synchronous SQLite read, so it's rebuilt fresh each time this view is constructed
    (MainWindow._clear_content() tears the whole page down on every navigation, which is
    exactly the refresh this page wants).
    """

    def __init__(self, parent, presenter: DashboardPresenter):
        super().__init__(parent)

        self.presenter = presenter

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        title = ctk.CTkLabel(self, text="Dashboard", font=ctk.CTkFont(size=28, weight="bold"))
        title.grid(row=0, column=0, sticky="w", padx=20, pady=(20, 10))

        self.status_label = ctk.CTkLabel(self, text="", anchor="w", text_color=ERROR_COLOR)
        self.status_label.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 5))
        self.status_label.grid_remove()

        self.cards_frame = ctk.CTkScrollableFrame(self)
        self.cards_frame.grid(row=2, column=0, sticky="nsew", padx=20, pady=(0, 20))
        self.cards_frame.grid_columnconfigure(0, weight=1)

        self.bind("<Destroy>", self._on_destroy)
        self.presenter.attach(on_change=self._render)

    def _on_destroy(self, event):
        if event.widget is self:
            self.presenter.detach()

    def _render(self):
        for child in self.cards_frame.winfo_children():
            child.destroy()

        if self.presenter.status is not None:
            self.status_label.configure(text=self.presenter.status.text)
            self.status_label.grid()
        else:
            self.status_label.grid_remove()

        data = self.presenter.data
        if data is None:
            return

        cards = [
            build_snapshot_card(self.cards_frame, data.snapshot),
            build_accounts_card(self.cards_frame, data.accounts),
            build_debts_card(self.cards_frame, data.debts),
            build_assets_card(self.cards_frame, data.assets),
            build_budget_status_card(self.cards_frame, data.budget_lines),
            build_recent_transactions_card(self.cards_frame, data.recent_transactions),
        ]

        for index, card in enumerate(cards):
            card.grid(row=index, column=0, sticky="ew", pady=(0, 10))
