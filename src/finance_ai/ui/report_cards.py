import customtkinter as ctk

from finance_ai.finance.summary import format_currency, format_months, format_percent
from finance_ai.history.interpreter import ChangeDirection

IMPROVED_COLOR = "#2fa572"
WORSENED_COLOR = "#d9534f"
NEUTRAL_COLOR = "gray60"


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
        ("Debt-to-Income", format_percent(snapshot.debt_to_income_ratio)),
        ("Emergency Fund", format_months(snapshot.emergency_fund_months)),
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
