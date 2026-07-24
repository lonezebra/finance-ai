import customtkinter as ctk

from finance_ai.ai.background import BackgroundTask
from finance_ai.ai.errors import describe_ai_error
from finance_ai.ai.thinking import EXECUTIVE_BRIEFING_THINKING_STEPS, ThinkingAnimator
from finance_ai.ui.presenters.briefing_presenter import BriefingPresenter

PLACEHOLDER_TEXT = "Click \"Generate Briefing\" to get your AI-powered executive briefing."


class BriefingView(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)

        self.presenter = BriefingPresenter()
        self.animator = ThinkingAnimator(
            EXECUTIVE_BRIEFING_THINKING_STEPS,
            on_update=self._on_thinking_update,
        )
        self._task: BackgroundTask | None = None

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        title = ctk.CTkLabel(
            self,
            text="Executive Briefing",
            font=ctk.CTkFont(size=28, weight="bold"),
        )
        title.grid(row=0, column=0, sticky="w", padx=20, pady=(20, 10))

        self.status_label = ctk.CTkLabel(self, text="", anchor="w")
        self.status_label.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 5))

        self.progress_bar = ctk.CTkProgressBar(self)
        self.progress_bar.set(0)
        self.progress_bar.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 5))
        self.progress_bar.grid_remove()

        self.textbox = ctk.CTkTextbox(self, wrap="word")
        self.textbox.grid(row=3, column=0, sticky="nsew", padx=20, pady=10)
        self.textbox.insert("1.0", PLACEHOLDER_TEXT)

        self.generate_button = ctk.CTkButton(
            self,
            text="Generate Briefing",
            command=self.generate,
        )
        self.generate_button.grid(row=4, column=0, sticky="ew", padx=20, pady=(10, 20))

    def generate(self):
        self.generate_button.configure(state="disabled", text="Generating...")
        self.textbox.delete("1.0", "end")
        self.progress_bar.set(0)
        self.progress_bar.grid()

        self.animator.start(self)

        self._task = BackgroundTask(
            target=self.presenter.get_briefing_text,
            on_success=self._on_success,
            on_error=self._on_error,
        )
        self._task.start()
        self._task.poll(self)

    def _on_thinking_update(self, state):
        self.status_label.configure(text=state.phase.value)
        self.progress_bar.set(state.progress / 100)

    def _on_success(self, briefing_text: str):
        self.animator.stop()
        self._finish(briefing_text)

    def _on_error(self, exc: Exception):
        self.animator.stop()
        self._finish(describe_ai_error(exc))

    def _finish(self, text: str):
        self.status_label.configure(text="")
        self.progress_bar.grid_remove()
        self.textbox.delete("1.0", "end")
        self.textbox.insert("1.0", text)
        self.generate_button.configure(state="normal", text="Generate Briefing")
