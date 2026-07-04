import customtkinter as ctk

from finance_ai.ui.briefing_view import BriefingView


class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Open CFO")
        self.geometry("1200x800")
        self.minsize(900, 600)

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

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
        view = BriefingView(self.content)
        view.grid(row=0, column=0, sticky="nsew")

    def _show_placeholder(self, name: str):
        if name == "Executive Briefing":
            self._show_briefing()
            return

        self._clear_content()
        label = ctk.CTkLabel(
            self.content,
            text=f"{name}\n\nComing soon.",
            font=ctk.CTkFont(size=24, weight="bold"),
        )
        label.grid(row=0, column=0, sticky="nsew")