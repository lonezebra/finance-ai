import customtkinter as ctk

from finance_ai.ui.presenters.briefing_presenter import BriefingPresenter


class BriefingView(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)

        self.presenter = BriefingPresenter()

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        title = ctk.CTkLabel(
            self,
            text="Executive Briefing",
            font=ctk.CTkFont(size=28, weight="bold"),
        )
        title.grid(row=0, column=0, sticky="w", padx=20, pady=(20, 10))

        self.textbox = ctk.CTkTextbox(self, wrap="word")
        self.textbox.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)

        self.refresh_button = ctk.CTkButton(
            self,
            text="Refresh Briefing",
            command=self.refresh,
        )
        self.refresh_button.grid(row=2, column=0, sticky="ew", padx=20, pady=(10, 20))

        self.refresh()

    def refresh(self):
        briefing = self.presenter.get_briefing_text()
        self.textbox.delete("1.0", "end")
        self.textbox.insert("1.0", briefing)