from tkinter import filedialog

import customtkinter as ctk

from finance_ai.ui.presenters.import_presenter import ImportPresenter, ImportPreview

IDEMPOTENCY_WARNING = (
    "Importing will add these records to your database. If you've already imported this "
    "file (or one with overlapping data), re-importing will create duplicates -- there's no "
    "duplicate detection yet."
)


class ImportView(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)

        self.presenter = ImportPresenter()
        self._preview: ImportPreview | None = None

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        title = ctk.CTkLabel(
            self,
            text="Import Data",
            font=ctk.CTkFont(size=28, weight="bold"),
        )
        title.grid(row=0, column=0, sticky="w", padx=20, pady=(20, 10))

        self.choose_button = ctk.CTkButton(
            self,
            text="Choose File...",
            command=self.choose_file,
        )
        self.choose_button.grid(row=1, column=0, sticky="w", padx=20, pady=(0, 10))

        self.preview_box = ctk.CTkTextbox(self, wrap="word")
        self.preview_box.grid(row=2, column=0, sticky="nsew", padx=20, pady=10)
        self._render_text(
            "Choose an Excel workbook to preview its contents before importing."
        )

        self.confirm_button = ctk.CTkButton(
            self,
            text="Confirm Import",
            command=self.confirm_import,
            state="disabled",
        )
        self.confirm_button.grid(row=3, column=0, sticky="ew", padx=20, pady=(10, 20))

    def choose_file(self):
        path = filedialog.askopenfilename(
            title="Choose an Excel workbook to import",
            filetypes=[("Excel files", "*.xlsx")],
        )

        if not path:
            return

        try:
            preview = self.presenter.load_preview(path)
        except Exception as exc:  # noqa: BLE001 - shown to the user, not swallowed
            self._preview = None
            self._render_text(f"Could not read this file:\n\n{exc}")
            self.confirm_button.configure(state="disabled")
            return

        self._preview = preview
        self._render_preview(preview)

    def _render_preview(self, preview: ImportPreview):
        report = preview.validation_report
        lines = [
            f"File: {preview.source_file}",
            "",
            f"Valid: {'Yes' if report.is_valid else 'No'}",
            f"Errors: {len(report.errors)}",
            f"Warnings: {len(report.warnings)}",
            "",
        ]

        if report.issues:
            lines.append("Issues:")
            for issue in report.issues:
                lines.append(f"- [{issue.severity}] {issue.sheet_name}: {issue.message}")
            lines.append("")

        if preview.dataset is not None:
            lines.append("This import will add:")
            for label, count in preview.counts.items():
                if count:
                    lines.append(f"- {count} {label.lower()}")
            lines.append("")
            lines.append(IDEMPOTENCY_WARNING)

        self._render_text("\n".join(lines))
        self.confirm_button.configure(
            state="normal" if preview.dataset is not None else "disabled"
        )

    def confirm_import(self):
        if self._preview is None:
            return

        self.confirm_button.configure(state="disabled")

        try:
            imported_counts = self.presenter.confirm_import(self._preview)
        except Exception as exc:  # noqa: BLE001 - shown to the user, not swallowed
            self._render_text(
                f"Import failed:\n\n{exc}\n\n"
                "If this looks like a duplicate-key error, you may have already imported "
                "this file."
            )
            return

        lines = ["Import complete.", ""]
        for label, count in imported_counts.items():
            if count:
                lines.append(f"- {count} {label}")

        self._render_text("\n".join(lines))
        self._preview = None

    def _render_text(self, text: str):
        self.preview_box.configure(state="normal")
        self.preview_box.delete("1.0", "end")
        self.preview_box.insert("1.0", text)
        self.preview_box.configure(state="disabled")
