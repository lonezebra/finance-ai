import customtkinter as ctk

from finance_ai.finance.summary import (
    format_currency,
    format_months,
    format_optional_months,
    format_percent,
)
from finance_ai.history.interpreter import ChangeDirection

IMPROVED_COLOR = "#2fa572"
WORSENED_COLOR = "#d9534f"
NEUTRAL_COLOR = "gray60"
MODERATE_COLOR = "#e0a030"

CONFIDENCE_LABEL_COLORS = {
    "High": IMPROVED_COLOR,
    "Moderate": MODERATE_COLOR,
    "Low": WORSENED_COLOR,
    "Very Low": WORSENED_COLOR,
}


def _card_frame(parent, title: str) -> ctk.CTkFrame:
    card = ctk.CTkFrame(
        parent,
        fg_color=("gray86", "gray17"),
        border_width=1,
        border_color=("gray70", "gray30"),
    )
    card.grid_columnconfigure(0, weight=1)

    label = ctk.CTkLabel(
        card,
        text=title,
        font=ctk.CTkFont(size=16, weight="bold"),
        anchor="w",
    )
    label.grid(row=0, column=0, sticky="w", padx=14, pady=(12, 6))

    return card


def build_confidence_card(parent, confidence) -> ctk.CTkFrame:
    card = _card_frame(parent, "Data Confidence")
    body = ctk.CTkFrame(card, fg_color="transparent")
    body.grid(row=1, column=0, sticky="ew", padx=14, pady=(0, 12))
    body.grid_columnconfigure(0, weight=1)

    caption = ctk.CTkLabel(
        body,
        text="How complete and trustworthy your data is -- not a measure of your finances.",
        text_color="gray60",
        anchor="w",
        justify="left",
        wraplength=520,
    )
    caption.pack(anchor="w", pady=(0, 6))

    score_color = CONFIDENCE_LABEL_COLORS.get(confidence.label, NEUTRAL_COLOR)
    header = ctk.CTkLabel(
        body,
        text=f"{confidence.score}/100  ·  {confidence.label}",
        font=ctk.CTkFont(size=18, weight="bold"),
        text_color=score_color,
        anchor="w",
    )
    header.pack(anchor="w", pady=(0, 4))

    if not confidence.issues:
        ctk.CTkLabel(body, text="No data-quality issues identified.", anchor="w").pack(
            anchor="w", pady=2
        )
        return card

    for issue in confidence.issues:
        ctk.CTkLabel(
            body,
            text=f"- {issue.message}",
            text_color="gray60",
            anchor="w",
            justify="left",
            wraplength=520,
        ).pack(anchor="w", pady=2)

    return card


def build_snapshot_card(parent, snapshot) -> ctk.CTkFrame:
    card = _card_frame(parent, "Financial Snapshot")

    stats = [
        ("Net Worth", format_currency(snapshot.net_worth)),
        ("Total Assets", format_currency(snapshot.total_assets)),
        ("Total Debt", format_currency(snapshot.total_debt)),
        ("Cash Balance", format_currency(snapshot.cash_balance)),
        ("Monthly Income", format_currency(snapshot.monthly_income)),
        ("Monthly Expenses", format_currency(snapshot.monthly_expenses)),
        ("Monthly Cash Flow", format_currency(snapshot.monthly_cash_flow)),
        ("Savings Rate", format_percent(snapshot.savings_rate)),
        ("Debt-to-Income (take-home)", format_percent(snapshot.debt_to_income_ratio)),
        ("Emergency Fund (current spending)", format_months(snapshot.emergency_fund_months)),
        (
            "Emergency Fund (essentials only)",
            format_optional_months(snapshot.essential_emergency_fund_months),
        ),
    ]

    body = ctk.CTkFrame(card, fg_color="transparent")
    body.grid(row=1, column=0, sticky="ew", padx=14, pady=(0, 12))
    body.grid_columnconfigure((0, 1), weight=1)

    for index, (label_text, value_text) in enumerate(stats):
        row, column = divmod(index, 2)
        tile = ctk.CTkFrame(body, fg_color="transparent")
        tile.grid(row=row, column=column, sticky="w", padx=6, pady=4)

        ctk.CTkLabel(tile, text=label_text, text_color="gray60", anchor="w").pack(anchor="w")
        ctk.CTkLabel(
            tile,
            text=value_text,
            font=ctk.CTkFont(size=15, weight="bold"),
            anchor="w",
        ).pack(anchor="w")

    return card


def build_changes_card(parent, changes) -> ctk.CTkFrame:
    card = _card_frame(parent, "Changes Since Last Update")
    body = ctk.CTkFrame(card, fg_color="transparent")
    body.grid(row=1, column=0, sticky="ew", padx=14, pady=(0, 12))
    body.grid_columnconfigure(0, weight=1)

    if not changes:
        ctk.CTkLabel(
            body,
            text="No significant changes since the last snapshot.",
            anchor="w",
        ).pack(anchor="w", pady=2)
        return card

    colors = {
        ChangeDirection.IMPROVED: IMPROVED_COLOR,
        ChangeDirection.WORSENED: WORSENED_COLOR,
        ChangeDirection.NEUTRAL: NEUTRAL_COLOR,
    }

    for change in changes:
        text = (
            f"{change.metric}: {change.direction.value} "
            f"({change.previous:,.2f} -> {change.current:,.2f}, "
            f"{change.percent_change * 100:+.1f}%)"
        )
        ctk.CTkLabel(body, text=text, text_color=colors[change.direction], anchor="w").pack(
            anchor="w", pady=2
        )

    return card


def build_strengths_concerns_card(parent, strengths, concerns) -> ctk.CTkFrame:
    card = _card_frame(parent, "Strengths & Concerns")
    body = ctk.CTkFrame(card, fg_color="transparent")
    body.grid(row=1, column=0, sticky="ew", padx=14, pady=(0, 12))
    body.grid_columnconfigure(0, weight=1)

    if not strengths and not concerns:
        ctk.CTkLabel(body, text="Nothing notable identified.", anchor="w").pack(
            anchor="w", pady=2
        )
        return card

    for strength in strengths:
        ctk.CTkLabel(body, text=f"+ {strength}", text_color=IMPROVED_COLOR, anchor="w").pack(
            anchor="w", pady=2
        )

    for concern in concerns:
        ctk.CTkLabel(body, text=f"- {concern}", text_color=WORSENED_COLOR, anchor="w").pack(
            anchor="w", pady=2
        )

    return card


def build_scenario_facts_card(parent, facts: list[str]) -> ctk.CTkFrame:
    card = _card_frame(parent, "Adjustments Applied")
    body = ctk.CTkFrame(card, fg_color="transparent")
    body.grid(row=1, column=0, sticky="ew", padx=14, pady=(0, 12))
    body.grid_columnconfigure(0, weight=1)

    if not facts:
        ctk.CTkLabel(body, text="No adjustments applied.", anchor="w").pack(anchor="w", pady=2)
        return card

    for fact in facts:
        ctk.CTkLabel(
            body, text=f"- {fact}", anchor="w", justify="left", wraplength=520
        ).pack(anchor="w", pady=2)

    return card


def build_ai_narrative_card(parent, text: str) -> ctk.CTkFrame:
    card = _card_frame(parent, "AI Explanation")
    body = ctk.CTkFrame(card, fg_color="transparent")
    body.grid(row=1, column=0, sticky="ew", padx=14, pady=(0, 12))
    body.grid_columnconfigure(0, weight=1)

    ctk.CTkLabel(body, text=text, anchor="w", justify="left", wraplength=520).pack(
        anchor="w", pady=2
    )

    return card


def build_decisions_card(parent, decisions) -> ctk.CTkFrame:
    card = _card_frame(parent, "Top Decisions")
    body = ctk.CTkFrame(card, fg_color="transparent")
    body.grid(row=1, column=0, sticky="ew", padx=14, pady=(0, 12))
    body.grid_columnconfigure(0, weight=1)

    if not decisions:
        ctk.CTkLabel(body, text="No decisions surfaced.", anchor="w").pack(anchor="w", pady=2)
        return card

    for decision in decisions:
        header = ctk.CTkLabel(
            body,
            text=f"{decision.title}  ·  {decision.priority.value.upper()}  ·  "
            f"score {decision.score}",
            font=ctk.CTkFont(weight="bold"),
            anchor="w",
        )
        header.pack(anchor="w", pady=(6, 0))

        reasoning = ctk.CTkLabel(
            body,
            text=decision.reasoning,
            text_color="gray60",
            anchor="w",
            justify="left",
            wraplength=520,
        )
        reasoning.pack(anchor="w", pady=(0, 4))

    return card


def _empty_row(body, text: str) -> None:
    ctk.CTkLabel(body, text=text, text_color="gray60", anchor="w").pack(anchor="w", pady=2)


def build_accounts_card(parent, accounts) -> ctk.CTkFrame:
    card = _card_frame(parent, "Accounts")
    body = ctk.CTkFrame(card, fg_color="transparent")
    body.grid(row=1, column=0, sticky="ew", padx=14, pady=(0, 12))
    body.grid_columnconfigure(0, weight=1)

    if not accounts:
        _empty_row(body, "No accounts have been added yet.")
        return card

    for account in accounts:
        detail = account.account_type.replace("_", " ").title()
        if account.institution:
            detail = f"{detail}  ·  {account.institution}"

        row = ctk.CTkFrame(body, fg_color="transparent")
        row.grid_columnconfigure(0, weight=1)
        row.pack(fill="x", pady=2)

        ctk.CTkLabel(row, text=account.name, anchor="w").grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(row, text=detail, text_color="gray60", anchor="w").grid(
            row=1, column=0, sticky="w"
        )
        ctk.CTkLabel(
            row, text=format_currency(account.balance), font=ctk.CTkFont(weight="bold")
        ).grid(row=0, column=1, rowspan=2, sticky="e", padx=(10, 0))

    return card


def build_debts_card(parent, debts) -> ctk.CTkFrame:
    card = _card_frame(parent, "Debts")
    body = ctk.CTkFrame(card, fg_color="transparent")
    body.grid(row=1, column=0, sticky="ew", padx=14, pady=(0, 12))
    body.grid_columnconfigure(0, weight=1)

    if not debts:
        _empty_row(body, "No debts have been added yet.")
        return card

    for debt in debts:
        details = []
        if debt.lender:
            details.append(debt.lender)
        if debt.interest_rate is not None:
            details.append(f"{debt.interest_rate:.1f}% APR")
        if debt.minimum_payment is not None:
            details.append(f"{format_currency(debt.minimum_payment)}/mo minimum")
        detail_text = "  ·  ".join(details) if details else "No further details recorded."

        row = ctk.CTkFrame(body, fg_color="transparent")
        row.grid_columnconfigure(0, weight=1)
        row.pack(fill="x", pady=2)

        ctk.CTkLabel(row, text=debt.name, anchor="w").grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(row, text=detail_text, text_color="gray60", anchor="w").grid(
            row=1, column=0, sticky="w"
        )
        ctk.CTkLabel(
            row, text=format_currency(debt.balance), font=ctk.CTkFont(weight="bold")
        ).grid(row=0, column=1, rowspan=2, sticky="e", padx=(10, 0))

    return card


def build_assets_card(parent, assets) -> ctk.CTkFrame:
    card = _card_frame(parent, "Assets")
    body = ctk.CTkFrame(card, fg_color="transparent")
    body.grid(row=1, column=0, sticky="ew", padx=14, pady=(0, 12))
    body.grid_columnconfigure(0, weight=1)

    if not assets:
        _empty_row(body, "No assets have been added yet.")
        return card

    for asset in assets:
        row = ctk.CTkFrame(body, fg_color="transparent")
        row.grid_columnconfigure(0, weight=1)
        row.pack(fill="x", pady=2)

        ctk.CTkLabel(row, text=asset.name, anchor="w").grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(
            row, text=asset.asset_type.replace("_", " ").title(), text_color="gray60", anchor="w"
        ).grid(row=1, column=0, sticky="w")
        ctk.CTkLabel(
            row, text=format_currency(asset.value), font=ctk.CTkFont(weight="bold")
        ).grid(row=0, column=1, rowspan=2, sticky="e", padx=(10, 0))

    return card


def build_recent_transactions_card(parent, transactions) -> ctk.CTkFrame:
    card = _card_frame(parent, "Recent Transactions")
    body = ctk.CTkFrame(card, fg_color="transparent")
    body.grid(row=1, column=0, sticky="ew", padx=14, pady=(0, 12))
    body.grid_columnconfigure(0, weight=1)

    if not transactions:
        _empty_row(body, "No transactions have been imported yet.")
        return card

    for transaction in transactions:
        category = f"  ·  {transaction.category_name}" if transaction.category_name else ""
        detail = f"{transaction.transaction_date:%d %b %Y}{category}"
        color = IMPROVED_COLOR if transaction.amount > 0 else None

        row = ctk.CTkFrame(body, fg_color="transparent")
        row.grid_columnconfigure(0, weight=1)
        row.pack(fill="x", pady=2)

        ctk.CTkLabel(row, text=transaction.description, anchor="w").grid(
            row=0, column=0, sticky="w"
        )
        ctk.CTkLabel(row, text=detail, text_color="gray60", anchor="w").grid(
            row=1, column=0, sticky="w"
        )
        amount_label = ctk.CTkLabel(
            row, text=format_currency(transaction.amount), font=ctk.CTkFont(weight="bold")
        )
        if color:
            amount_label.configure(text_color=color)
        amount_label.grid(row=0, column=1, rowspan=2, sticky="e", padx=(10, 0))

    return card


def build_budget_status_card(parent, budget_lines) -> ctk.CTkFrame:
    card = _card_frame(parent, "Budget Status")
    body = ctk.CTkFrame(card, fg_color="transparent")
    body.grid(row=1, column=0, sticky="ew", padx=14, pady=(0, 12))
    body.grid_columnconfigure(0, weight=1)

    if not budget_lines:
        _empty_row(body, "No budgets have been set for this month.")
        return card

    for line in budget_lines:
        color = WORSENED_COLOR if line.is_over_budget else IMPROVED_COLOR
        detail = (
            f"{format_currency(line.actual_amount)} of {format_currency(line.budgeted_amount)} "
            f"budgeted"
        )

        row = ctk.CTkFrame(body, fg_color="transparent")
        row.grid_columnconfigure(0, weight=1)
        row.pack(fill="x", pady=2)

        ctk.CTkLabel(row, text=line.category_name, anchor="w").grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(row, text=detail, text_color="gray60", anchor="w").grid(
            row=1, column=0, sticky="w"
        )
        variance_text = (
            f"{format_currency(abs(line.variance))} over"
            if line.is_over_budget
            else f"{format_currency(line.variance)} left"
        )
        ctk.CTkLabel(row, text=variance_text, text_color=color, font=ctk.CTkFont(weight="bold")).grid(
            row=0, column=1, rowspan=2, sticky="e", padx=(10, 0)
        )

    return card
