from tkinter import messagebox

import customtkinter as ctk

from finance_ai.ui.presenters.settings_presenter import SettingsPresenter

ERROR_COLOR = "#d9534f"
OK_COLOR = "#2fa572"

INTRO = (
    "Open CFO keeps your financial data in a single file on this computer. A backup is a "
    "copy of that file, so you can go back to it if something goes wrong."
)


def format_size(size_bytes: int) -> str:
    if size_bytes < 1024:
        return f"{size_bytes} B"
    if size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.0f} KB"
    return f"{size_bytes / (1024 * 1024):.1f} MB"


class SettingsView(ctk.CTkFrame):
    def __init__(self, parent, presenter: SettingsPresenter):
        super().__init__(parent)

        self.presenter = presenter

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(4, weight=1)

        title = ctk.CTkLabel(self, text="Settings", font=ctk.CTkFont(size=28, weight="bold"))
        title.grid(row=0, column=0, sticky="w", padx=20, pady=(20, 10))

        self._build_backup_controls(row=1)
        self._build_status(row=2)
        self._build_backup_list(row=4)

        self.bind("<Destroy>", self._on_destroy)
        self.presenter.attach(on_change=self._render)

    def _build_backup_controls(self, row: int):
        section = ctk.CTkFrame(self)
        section.grid(row=row, column=0, sticky="ew", padx=20, pady=(0, 10))
        section.grid_columnconfigure(0, weight=1)

        heading = ctk.CTkLabel(
            section, text="Back up your data", font=ctk.CTkFont(size=16, weight="bold"), anchor="w"
        )
        heading.grid(row=0, column=0, sticky="w", padx=14, pady=(14, 2))

        ctk.CTkLabel(
            section,
            text=INTRO,
            text_color="gray60",
            anchor="w",
            justify="left",
            wraplength=620,
        ).grid(row=1, column=0, sticky="w", padx=14, pady=(0, 10))

        controls = ctk.CTkFrame(section, fg_color="transparent")
        controls.grid(row=2, column=0, sticky="ew", padx=14, pady=(0, 14))
        controls.grid_columnconfigure(0, weight=1)

        self.label_entry = ctk.CTkEntry(
            controls, placeholder_text='Optional note, e.g. "before big import"'
        )
        self.label_entry.grid(row=0, column=0, sticky="ew", padx=(0, 10))

        self.backup_button = ctk.CTkButton(
            controls, text="Back up now", width=130, command=self._create_backup
        )
        self.backup_button.grid(row=0, column=1)

    def _build_status(self, row: int):
        self.status_label = ctk.CTkLabel(
            self, text="", anchor="w", justify="left", wraplength=640
        )
        self.status_label.grid(row=row, column=0, sticky="ew", padx=20, pady=(0, 8))

    def _build_backup_list(self, row: int):
        section = ctk.CTkFrame(self)
        section.grid(row=row, column=0, sticky="nsew", padx=20, pady=(0, 20))
        section.grid_columnconfigure(0, weight=1)
        section.grid_rowconfigure(2, weight=1)

        ctk.CTkLabel(
            section,
            text="Saved backups",
            font=ctk.CTkFont(size=16, weight="bold"),
            anchor="w",
        ).grid(row=0, column=0, sticky="w", padx=14, pady=(14, 2))

        ctk.CTkLabel(
            section,
            text=(
                "Restoring replaces everything currently in Open CFO with the contents of "
                "that backup. Your current data is saved first, so you can undo it."
            ),
            text_color="gray60",
            anchor="w",
            justify="left",
            wraplength=620,
        ).grid(row=1, column=0, sticky="w", padx=14, pady=(0, 10))

        self.backup_list = ctk.CTkScrollableFrame(section, fg_color="transparent")
        self.backup_list.grid(row=2, column=0, sticky="nsew", padx=14, pady=(0, 14))
        self.backup_list.grid_columnconfigure(0, weight=1)

    def _on_destroy(self, event):
        if event.widget is self:
            self.presenter.detach()

    def _create_backup(self):
        self.presenter.create_backup(self.label_entry.get())
        self.label_entry.delete(0, "end")

    def _confirm_and_restore(self, backup):
        """The confirmation lives here rather than in the presenter so the presenter stays
        testable without a display. Spells out what will happen, in plain words, because this
        is the one destructive action in the app."""

        when = f"{backup.created_at:%d %b %Y at %H:%M}"
        confirmed = messagebox.askyesno(
            title="Restore this backup?",
            message=(
                f"This will replace everything currently in Open CFO with the backup taken "
                f"on {when}.\n\n"
                "Your current data will be saved as a backup first, so you can undo this.\n\n"
                "Continue?"
            ),
            icon="warning",
            default="no",
        )

        if confirmed:
            self.presenter.restore(backup.path)

    def _render(self):
        self._render_status()
        self._render_backup_list()

    def _render_status(self):
        status = self.presenter.status

        if status is None:
            self.status_label.configure(text="")
            return

        self.status_label.configure(
            text=status.text, text_color=ERROR_COLOR if status.is_error else OK_COLOR
        )

    def _render_backup_list(self):
        for child in self.backup_list.winfo_children():
            child.destroy()

        if not self.presenter.backups:
            ctk.CTkLabel(
                self.backup_list,
                text='No backups yet. Click "Back up now" to make one.',
                text_color="gray60",
                anchor="w",
            ).grid(row=0, column=0, sticky="w", pady=4)
            return

        for index, backup in enumerate(self.presenter.backups):
            row_frame = ctk.CTkFrame(self.backup_list, fg_color="transparent")
            row_frame.grid(row=index, column=0, sticky="ew", pady=3)
            row_frame.grid_columnconfigure(0, weight=1)

            note = f"  ({backup.description})" if backup.description else ""
            text = f"{backup.created_at:%d %b %Y  %H:%M}   {format_size(backup.size_bytes)}{note}"
            ctk.CTkLabel(row_frame, text=text, anchor="w").grid(row=0, column=0, sticky="w")

            ctk.CTkButton(
                row_frame,
                text="Restore",
                width=90,
                fg_color=("gray70", "gray30"),
                hover_color=ERROR_COLOR,
                command=lambda b=backup: self._confirm_and_restore(b),
            ).grid(row=0, column=1, padx=(10, 0))
