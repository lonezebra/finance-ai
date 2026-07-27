import customtkinter as ctk

from finance_ai.ui.briefing_view import BriefingView
from finance_ai.ui.chat_view import ChatView
from finance_ai.ui.import_view import ImportView
from finance_ai.ui.presenters.briefing_presenter import BriefingPresenter
from finance_ai.ui.presenters.chat_presenter import ChatPresenter
from finance_ai.ui.presenters.scenario_presenter import ScenarioPresenter
from finance_ai.ui.scenario_view import ScenarioView


class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Open CFO")
        self.geometry("1200x800")
        self.minsize(900, 600)

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # Owned here, not by BriefingView, so an in-flight (or completed) briefing request
        # survives navigating away and back -- _clear_content() destroys the whole page on
        # every navigation, but this presenter's lifetime spans the app's lifetime.
        self.briefing_presenter = BriefingPresenter()

        # Same reasoning as briefing_presenter: owned here so the conversation (and any
        # in-flight reply) survives navigating away and back.
        self.chat_presenter = ChatPresenter()

        # Same reasoning again: the adjustments being built, the last projection, and any
        # in-flight AI explanation survive navigating away and back.
        self.scenario_presenter = ScenarioPresenter()

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.sidebar = ctk.CTkFrame(self, width=220)
        self.sidebar.grid(row=0, column=0, sticky="nsew", padx=(12, 6), pady=12)
        self.sidebar.grid_propagate(False)

        self.content = ctk.CTkFrame(self)
        self.content.grid(row=0, column=1, sticky="nsew", padx=(6, 12), pady=12)
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(0, weight=1)

        self._build_sidebar()
        self._show_briefing()

    def _build_sidebar(self):
        title = ctk.CTkLabel(
            self.sidebar,
            text="Open CFO",
            font=ctk.CTkFont(size=22, weight="bold"),
        )
        title.pack(anchor="w", padx=16, pady=(16, 20))

        pages = [
            "Executive Briefing",
            "Scenario Planning",
            "Import Data",
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

        for page in pages:
            button = ctk.CTkButton(
                self.sidebar,
                text=page,
                anchor="w",
                command=lambda name=page: self._show_placeholder(name),
            )
            button.pack(fill="x", padx=12, pady=4)

    def _clear_content(self):
        for child in self.content.winfo_children():
            child.destroy()

    def _show_briefing(self):
        self._clear_content()
        view = BriefingView(self.content, presenter=self.briefing_presenter)
        view.grid(row=0, column=0, sticky="nsew")

    def _show_import(self):
        self._clear_content()
        view = ImportView(self.content)
        view.grid(row=0, column=0, sticky="nsew")

    def _show_chat(self):
        self._clear_content()
        view = ChatView(self.content, presenter=self.chat_presenter)
        view.grid(row=0, column=0, sticky="nsew")

    def _show_scenario(self):
        self._clear_content()
        view = ScenarioView(self.content, presenter=self.scenario_presenter)
        view.grid(row=0, column=0, sticky="nsew")

    def _show_placeholder(self, name: str):
        if name == "Executive Briefing":
            self._show_briefing()
            return

        if name == "Import Data":
            self._show_import()
            return

        if name == "AI Advisor":
            self._show_chat()
            return

        if name == "Scenario Planning":
            self._show_scenario()
            return

        self._clear_content()
        label = ctk.CTkLabel(
            self.content,
            text=f"{name}\n\nComing soon.",
            font=ctk.CTkFont(size=24, weight="bold"),
        )
        label.grid(row=0, column=0, sticky="nsew")