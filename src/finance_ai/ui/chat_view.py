import customtkinter as ctk

from finance_ai.ui.presenters.chat_presenter import ChatMessage, ChatPresenter, ChatRole

PLACEHOLDER_TEXT = "Ask the Strategic Advisor about your finances."

ROLE_LABELS = {
    ChatRole.USER: "You",
    ChatRole.ASSISTANT: "Strategic Advisor",
}

BUBBLE_COLORS = {
    ChatRole.USER: ("#CFE3FF", "#274873"),
    ChatRole.ASSISTANT: ("gray85", "gray25"),
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
        self.status_label.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 2))

        self.progress_bar = ctk.CTkProgressBar(self, mode="indeterminate")
        self.progress_bar.grid(row=3, column=0, sticky="ew", padx=20, pady=(0, 5))
        self.progress_bar.grid_remove()

        input_row = ctk.CTkFrame(self, fg_color="transparent")
        input_row.grid(row=4, column=0, sticky="ew", padx=20, pady=(0, 20))
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
        bubble = ctk.CTkFrame(
            self.transcript,
            fg_color=BUBBLE_COLORS[message.role],
            corner_radius=10,
        )
        bubble.grid(row=self._transcript_row, column=0, sticky="ew", pady=6)
        bubble.grid_columnconfigure(0, weight=1)
        self._transcript_row += 1

        header = ctk.CTkLabel(
            bubble,
            text=ROLE_LABELS[message.role],
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=("gray30", "gray70"),
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

        self._scroll_to_bottom()

    def _scroll_to_bottom(self):
        # CTkScrollableFrame has no public "scroll to bottom" API; _parent_canvas is the
        # plain tkinter.Canvas underneath it, confirmed present in the installed
        # customtkinter version. Guarded so a version mismatch degrades to "no
        # auto-scroll" instead of crashing message rendering.
        try:
            canvas = self.transcript._parent_canvas
            self.transcript.update_idletasks()
            canvas.configure(scrollregion=canvas.bbox("all"))
            canvas.yview_moveto(1.0)
        except AttributeError:
            pass

    def _on_thinking_change(self, thinking: bool):
        if thinking:
            self.status_label.configure(text="Strategic Advisor is thinking...")
            self.progress_bar.grid()
            self.progress_bar.start()
            self.send_button.configure(state="disabled")
            self.input_box.configure(state="disabled")
        else:
            self.status_label.configure(text="")
            self.progress_bar.stop()
            self.progress_bar.grid_remove()
            self.send_button.configure(state="normal")
            self.input_box.configure(state="normal")
