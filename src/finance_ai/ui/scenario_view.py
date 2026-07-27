import customtkinter as ctk

from finance_ai.history.interpreter import interpret_comparison
from finance_ai.scenario.models import AdjustmentType
from finance_ai.ui.presenters.scenario_presenter import NarrativeState, ScenarioPresenter
from finance_ai.ui.report_cards import (
    build_ai_narrative_card,
    build_changes_card,
    build_decisions_card,
    build_scenario_facts_card,
    build_snapshot_card,
)

ADJUSTMENT_TYPE_LABELS = {
    AdjustmentType.INCOME_CHANGE: "Income Change (monthly)",
    AdjustmentType.RECURRING_EXPENSE_CHANGE: "Recurring Expense Change (monthly)",
    AdjustmentType.EXTRA_DEBT_PAYMENT: "Extra Debt Payment (one-time)",
    AdjustmentType.CONTRIBUTION_CHANGE: "Savings/Investment Contribution (one-time)",
    AdjustmentType.ONE_TIME_PURCHASE: "One-Time Purchase",
    AdjustmentType.ONE_TIME_WINDFALL: "One-Time Windfall",
}

ADJUSTMENT_TYPE_HINTS = {
    AdjustmentType.INCOME_CHANGE: "Positive for a raise, negative for a cut.",
    AdjustmentType.RECURRING_EXPENSE_CHANGE: "Positive for more spending, negative for less.",
    AdjustmentType.EXTRA_DEBT_PAYMENT: "Enter the payment amount as a positive number.",
    AdjustmentType.CONTRIBUTION_CHANGE: "Enter the contribution amount as a positive number.",
    AdjustmentType.ONE_TIME_PURCHASE: "Enter the purchase amount as a positive number.",
    AdjustmentType.ONE_TIME_WINDFALL: "Enter the windfall amount as a positive number.",
}

LABEL_TO_TYPE = {label: adjustment_type for adjustment_type, label in ADJUSTMENT_TYPE_LABELS.items()}


class ScenarioView(ctk.CTkFrame):
    def __init__(self, parent, presenter: ScenarioPresenter):
        super().__init__(parent)

        self.presenter = presenter

        self.grid_columnconfigure(0, weight=1)
        # Results (row 4) and the AI narrative (row 5) split the available vertical space
        # evenly, same reasoning as BriefingView's cards/textbox split -- the narrative has
        # its own always-visible section rather than being appended at the end of the
        # scrollable results cards, where it wasn't obvious it needed scrolling to find.
        self.grid_rowconfigure(4, weight=1)
        self.grid_rowconfigure(5, weight=1)

        title = ctk.CTkLabel(
            self, text="Scenario Planning", font=ctk.CTkFont(size=28, weight="bold")
        )
        title.grid(row=0, column=0, sticky="w", padx=20, pady=(20, 10))

        self._build_form(row=1)
        self._build_ai_controls(row=2)
        self._build_results_frame(row=4)
        self._build_narrative_frame(row=5)

        self.bind("<Destroy>", self._on_destroy)
        self._update_hint()

        self.presenter.attach(on_change=self._render)

    def _build_form(self, row: int):
        builder = ctk.CTkFrame(self)
        builder.grid(row=row, column=0, sticky="ew", padx=20, pady=(0, 10))
        builder.grid_columnconfigure(0, weight=1)

        form_row = ctk.CTkFrame(builder, fg_color="transparent")
        form_row.grid(row=0, column=0, sticky="ew", padx=14, pady=(14, 4))
        form_row.grid_columnconfigure(1, weight=1)
        form_row.grid_columnconfigure(2, weight=1)

        self.type_menu = ctk.CTkOptionMenu(
            form_row,
            values=list(ADJUSTMENT_TYPE_LABELS.values()),
            command=self._on_type_change,
        )
        self.type_menu.grid(row=0, column=0, sticky="w", padx=(0, 10))

        self.amount_entry = ctk.CTkEntry(form_row, placeholder_text="Amount")
        self.amount_entry.grid(row=0, column=1, sticky="ew", padx=(0, 10))

        self.label_entry = ctk.CTkEntry(form_row, placeholder_text='Label (e.g. "Raise")')
        self.label_entry.grid(row=0, column=2, sticky="ew", padx=(0, 10))

        self.add_button = ctk.CTkButton(
            form_row, text="Add", width=70, command=self._add_adjustment
        )
        self.add_button.grid(row=0, column=3)

        self.hint_label = ctk.CTkLabel(builder, text="", text_color="gray60", anchor="w")
        self.hint_label.grid(row=1, column=0, sticky="w", padx=14, pady=(0, 4))

        self.error_label = ctk.CTkLabel(builder, text="", text_color="#d9534f", anchor="w")
        self.error_label.grid(row=2, column=0, sticky="w", padx=14, pady=(0, 4))

        self.adjustments_list = ctk.CTkFrame(builder, fg_color="transparent")
        self.adjustments_list.grid(row=3, column=0, sticky="ew", padx=14, pady=(0, 10))
        self.adjustments_list.grid_columnconfigure(0, weight=1)

        self.run_button = ctk.CTkButton(
            builder, text="Run Scenario", command=self._run_scenario, state="disabled"
        )
        self.run_button.grid(row=4, column=0, sticky="w", padx=14, pady=(0, 14))

    def _build_ai_controls(self, row: int):
        ai_row = ctk.CTkFrame(self, fg_color="transparent")
        ai_row.grid(row=row, column=0, sticky="ew", padx=20, pady=(0, 5))
        ai_row.grid_columnconfigure(0, weight=1)

        self.ai_status_label = ctk.CTkLabel(ai_row, text="", anchor="w", text_color="gray60")
        self.ai_status_label.grid(row=0, column=0, sticky="w")

        self.explain_button = ctk.CTkButton(
            ai_row, text="Explain with AI", command=self._explain_with_ai, state="disabled"
        )
        self.explain_button.grid(row=0, column=1, padx=(10, 0))

        self.ai_progress_bar = ctk.CTkProgressBar(self, mode="indeterminate")
        self.ai_progress_bar.grid(row=row + 1, column=0, sticky="ew", padx=20, pady=(0, 5))
        self.ai_progress_bar.grid_remove()

    def _build_results_frame(self, row: int):
        self.results_frame = ctk.CTkScrollableFrame(self)
        self.results_frame.grid(row=row, column=0, sticky="nsew", padx=20, pady=(0, 10))
        self.results_frame.grid_columnconfigure(0, weight=1)

    def _build_narrative_frame(self, row: int):
        self.narrative_frame = ctk.CTkScrollableFrame(self)
        self.narrative_frame.grid(row=row, column=0, sticky="nsew", padx=20, pady=(0, 20))
        self.narrative_frame.grid_columnconfigure(0, weight=1)

    def _on_destroy(self, event):
        if event.widget is self:
            self.presenter.detach()

    def _on_type_change(self, _value):
        self._update_hint()

    def _update_hint(self):
        selected = LABEL_TO_TYPE.get(self.type_menu.get())
        self.hint_label.configure(text=ADJUSTMENT_TYPE_HINTS.get(selected, ""))

    def _add_adjustment(self):
        self.error_label.configure(text="")
        adjustment_type = LABEL_TO_TYPE.get(self.type_menu.get())
        label = self.label_entry.get().strip()

        try:
            amount = float(self.amount_entry.get())
        except ValueError:
            self.error_label.configure(text="Amount must be a number.")
            return

        if not label:
            self.error_label.configure(text="Give this adjustment a short label.")
            return

        self.presenter.add_adjustment(adjustment_type, amount, label)
        self.amount_entry.delete(0, "end")
        self.label_entry.delete(0, "end")

    def _run_scenario(self):
        self.presenter.run_scenario()

    def _explain_with_ai(self):
        self.presenter.explain_with_ai(self.winfo_toplevel())

    def _render(self):
        self._render_adjustments_list()
        self._render_ai_controls()
        self._render_results()
        self._render_narrative()

    def _render_adjustments_list(self):
        for child in self.adjustments_list.winfo_children():
            child.destroy()

        if not self.presenter.adjustments:
            ctk.CTkLabel(
                self.adjustments_list,
                text="No adjustments added yet.",
                text_color="gray60",
                anchor="w",
            ).grid(row=0, column=0, sticky="w")
            self.run_button.configure(state="disabled")
            return

        self.run_button.configure(state="normal")

        for index, adjustment in enumerate(self.presenter.adjustments):
            row_frame = ctk.CTkFrame(self.adjustments_list, fg_color="transparent")
            row_frame.grid(row=index, column=0, sticky="ew", pady=2)
            row_frame.grid_columnconfigure(0, weight=1)

            type_label = ADJUSTMENT_TYPE_LABELS.get(adjustment.type, adjustment.type.value)
            text = f"{adjustment.label} -- {type_label}: {adjustment.amount:,.2f}"
            ctk.CTkLabel(row_frame, text=text, anchor="w").grid(row=0, column=0, sticky="w")

            remove_button = ctk.CTkButton(
                row_frame,
                text="Remove",
                width=70,
                command=lambda i=index: self.presenter.remove_adjustment(i),
            )
            remove_button.grid(row=0, column=1, padx=(10, 0))

    def _render_ai_controls(self):
        state = self.presenter.narrative_state

        if self.presenter.result is None:
            self.explain_button.configure(state="disabled")
        else:
            self.explain_button.configure(
                state="disabled" if state == NarrativeState.RUNNING else "normal"
            )

        if state == NarrativeState.RUNNING:
            self.ai_status_label.configure(text="Strategic Advisor is thinking...")
            self.ai_progress_bar.grid()
            self.ai_progress_bar.start()
        else:
            self.ai_status_label.configure(text="")
            self.ai_progress_bar.stop()
            self.ai_progress_bar.grid_remove()

    def _render_results(self):
        for child in self.results_frame.winfo_children():
            child.destroy()

        result = self.presenter.result

        if result is None:
            ctk.CTkLabel(
                self.results_frame,
                text='Add at least one adjustment and click "Run Scenario" to see a projection.',
                text_color="gray60",
                anchor="w",
            ).grid(row=0, column=0, sticky="w", pady=10)
            return

        row = 0

        facts_card = build_scenario_facts_card(self.results_frame, result.scenario_facts)
        facts_card.grid(row=row, column=0, sticky="ew", pady=(0, 10))
        row += 1

        changes = interpret_comparison(result.comparison)
        changes_card = build_changes_card(self.results_frame, changes)
        changes_card.grid(row=row, column=0, sticky="ew", pady=(0, 10))
        row += 1

        snapshot_card = build_snapshot_card(self.results_frame, result.projected_snapshot)
        snapshot_card.grid(row=row, column=0, sticky="ew", pady=(0, 10))
        row += 1

        decisions_card = build_decisions_card(
            self.results_frame, result.projected_decisions.decisions[:3]
        )
        decisions_card.grid(row=row, column=0, sticky="ew", pady=(0, 10))

    def _render_narrative(self):
        for child in self.narrative_frame.winfo_children():
            child.destroy()

        text = (
            self.presenter.narrative_text
            or 'Click "Explain with AI" above to see an AI explanation of this scenario.'
        )
        card = build_ai_narrative_card(self.narrative_frame, text)
        card.grid(row=0, column=0, sticky="ew")
