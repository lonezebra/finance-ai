import customtkinter as ctk

from finance_ai.ui.presenters.chat_presenter import ChatMessage, ChatPresenter, ChatRole

PLACEHOLDER_TEXT = "Ask the Strategic Advisor about your finances."

ROLE_LABELS = {
    ChatRole.USER: "You",
    ChatRole.ASSISTANT: "Strategic Advisor",
}


class ChatView(ctk.CTkFrame):
    def __init__(self, parent, presenter: ChatPresenter):
        super().__init__(parent)

        self.presenter = presenter
        self._transcript_row = 0

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        title = ctk.CTkLabel(
            self,
            text="AI Advisor",
            font=ctk.CTkFont(size=28, weight="bold"),
        )
        title.grid(row=0, column=0, sticky="w", padx=20, pady=(20, 10))

        self.transcript = ctk.CTkScrollableFrame(self)
        self.transcript.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 10))
        self.transcript.grid_columnconfigure(0, weight=1)

        self.status_label = ctk.CTkLabel(self, text="", anchor="w", text_color="gray60")
        self.status_label.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 5))

        input_row = ctk.CTkFrame(self, fg_color="transparent")
        input_row.grid(row=3, column=0, sticky="ew", padx=20, pady=(0, 20))
        input_row.grid_columnconfigure(0, weight=1)

        self.input_box = ctk.CTkEntry(input_row, placeholder_text="Ask a question...")
        self.input_box.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self.input_box.bind("<Return>", lambda event: self.send())

        self.send_button = ctk.CTkButton(input_row, text="Send", width=80, command=self.send)
        self.send_button.grid(row=0, column=1)

        self.bind("<Destroy>", self._on_destroy)

        if not self.presenter.messages and not self.presenter.is_thinking:
            self._add_placeholder()

        self.presenter.attach(
            on_message=self._on_message,
            on_thinking_change=self._on_thinking_change,
        )

    def _add_placeholder(self):
        label = ctk.CTkLabel(
            self.transcript, text=PLACEHOLDER_TEXT, text_color="gray60", anchor="w"
        )
        label.grid(row=self._transcript_row, column=0, sticky="w", pady=6)
        self._transcript_row += 1

    def _on_destroy(self, event):
        if event.widget is self:
            self.presenter.detach()

    def send(self):
        text = self.input_box.get()
        if not text.strip():
            return

        self.input_box.delete(0, "end")
        self.presenter.send(text, self.winfo_toplevel())

    def _on_message(self, message: ChatMessage):
        bubble = ctk.CTkFrame(self.transcript, fg_color=("gray86", "gray17"))
        bubble.grid(row=self._transcript_row, column=0, sticky="ew", pady=6)
        bubble.grid_columnconfigure(0, weight=1)
        self._transcript_row += 1

        header = ctk.CTkLabel(
            bubble,
            text=ROLE_LABELS[message.role],
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="gray60",
            anchor="w",
        )
        header.grid(row=0, column=0, sticky="w", padx=12, pady=(8, 0))

        body = ctk.CTkLabel(
            bubble,
            text=message.content,
            anchor="w",
            justify="left",
            wraplength=560,
        )
        body.grid(row=1, column=0, sticky="w", padx=12, pady=(0, 8))

    def _on_thinking_change(self, thinking: bool):
        if thinking:
            self.status_label.configure(text="Strategic Advisor is thinking...")
            self.send_button.configure(state="disabled")
            self.input_box.configure(state="disabled")
        else:
            self.status_label.configure(text="")
            self.send_button.configure(state="normal")
            self.input_box.configure(state="normal")
