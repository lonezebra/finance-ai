import customtkinter as ctk

from finance_ai.ui.presenters.briefing_presenter import BriefingPresenter, BriefingRequestState
from finance_ai.ui.presenters.executive_report_presenter import ExecutiveReportPresenter
from finance_ai.ui.report_cards import (
    build_changes_card,
    build_confidence_card,
    build_decisions_card,
    build_snapshot_card,
    build_strengths_concerns_card,
)

PLACEHOLDER_TEXT = "Click \"Generate Briefing\" to get your AI-powered executive briefing."


class BriefingView(ctk.CTkFrame):
    def __init__(self, parent, presenter: BriefingPresenter):
        super().__init__(parent)

        self.presenter = presenter
        self.report_presenter = ExecutiveReportPresenter()

        self.grid_columnconfigure(0, weight=1)
        # Cards (row 1) and the AI narrative textbox (row 4) split the available vertical
        # space evenly. Previously only row 4 had weight, so the cards region was pinned to
        # its construction-time height (260px) regardless of window size -- it never grew.
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(4, weight=1)

        title = ctk.CTkLabel(
            self,
            text="Executive Briefing",
            font=ctk.CTkFont(size=28, weight="bold"),
        )
        title.grid(row=0, column=0, sticky="w", padx=20, pady=(20, 10))

        self._build_cards()

        self.status_label = ctk.CTkLabel(self, text="", anchor="w")
        self.status_label.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 5))

        self.progress_bar = ctk.CTkProgressBar(self)
        self.progress_bar.set(0)
        self.progress_bar.grid(row=3, column=0, sticky="ew", padx=20, pady=(0, 5))
        self.progress_bar.grid_remove()

        self.textbox = ctk.CTkTextbox(self, wrap="word")
        self.textbox.grid(row=4, column=0, sticky="nsew", padx=20, pady=10)

        self.generate_button = ctk.CTkButton(
            self,
            text="Generate Briefing",
            command=self.generate,
        )
        self.generate_button.grid(row=5, column=0, sticky="ew", padx=20, pady=(10, 20))

        self.bind("<Destroy>", self._on_destroy)

        # DONE/ERROR are fully rendered by attach()'s replay below (via _on_success/_on_error
        # -> _finish, which sets text, chrome, and button state together). Only RUNNING's
        # button/progress-bar chrome and IDLE's placeholder need setting up front, since
        # attach() has nothing to replay for those two cases (RUNNING only replays the
        # thinking-phase label/progress, not the chrome; IDLE has no request to replay at all).
        if self.presenter.state == BriefingRequestState.RUNNING:
            self.generate_button.configure(state="disabled", text="Generating...")
            self.progress_bar.grid()
        elif self.presenter.state == BriefingRequestState.IDLE:
            self.textbox.insert("1.0", PLACEHOLDER_TEXT)

        self.presenter.attach(
            on_thinking_update=self._on_thinking_update,
            on_success=self._on_success,
            on_error=self._on_error,
        )

    def _build_cards(self):
        report = self.report_presenter.get_report()

        cards_frame = ctk.CTkScrollableFrame(self)
        cards_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 10))
        cards_frame.grid_columnconfigure(0, weight=1)

        confidence_card = build_confidence_card(cards_frame, report.confidence)
        confidence_card.grid(row=0, column=0, sticky="ew", pady=(0, 10))

        snapshot_card = build_snapshot_card(cards_frame, report.snapshot)
        snapshot_card.grid(row=1, column=0, sticky="ew", pady=(0, 10))

        changes_card = build_changes_card(cards_frame, report.important_changes)
        changes_card.grid(row=2, column=0, sticky="ew", pady=(0, 10))

        strengths_card = build_strengths_concerns_card(
            cards_frame, report.strengths, report.concerns
        )
        strengths_card.grid(row=3, column=0, sticky="ew", pady=(0, 10))

        decisions_card = build_decisions_card(cards_frame, report.top_decisions)
        decisions_card.grid(row=4, column=0, sticky="ew", pady=(0, 10))

    def _on_destroy(self, event):
        if event.widget is self:
            self.presenter.detach()

    def generate(self):
        self.generate_button.configure(state="disabled", text="Generating...")
        self.textbox.delete("1.0", "end")
        self.progress_bar.set(0)
        self.progress_bar.grid()

        self.presenter.generate(self.winfo_toplevel())

    def _on_thinking_update(self, state):
        self.status_label.configure(text=state.phase.value)
        self.progress_bar.set(state.progress / 100)

    def _on_success(self, briefing_text: str):
        self._finish(briefing_text)

    def _on_error(self, message: str):
        self._finish(message)

    def _finish(self, text: str):
        self.status_label.configure(text="")
        self.progress_bar.grid_remove()
        self.textbox.delete("1.0", "end")
        self.textbox.insert("1.0", text)
        self.generate_button.configure(state="normal", text="Generate Briefing")
