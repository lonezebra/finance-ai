from dataclasses import dataclass
from datetime import date

import pandas as pd

from finance_ai.imports.models import WorkbookData


@dataclass(frozen=True)
class AccountImport:
    name: str
    account_type: str
    institution: str | None
    current_balance: float
    notes: str | None


@dataclass(frozen=True)
class CategoryImport:
    name: str
    category_type: str


@dataclass(frozen=True)
class TransactionImport:
    transaction_date: date
    merchant: str | None
    description: str | None
    amount: float
    account_name: str
    category_name: str
    notes: str | None


@dataclass(frozen=True)
class DebtImport:
    name: str
    lender: str | None
    balance: float
    interest_rate: float | None
    minimum_payment: float | None
    due_day: int | None
    notes: str | None


@dataclass(frozen=True)
class AssetImport:
    name: str
    asset_type: str
    current_value: float
    notes: str | None


@dataclass(frozen=True)
class BudgetImport:
    month: str
    category_name: str
    budgeted_amount: float


@dataclass(frozen=True)
class GoalImport:
    name: str
    target_amount: float | None
    current_amount: float | None
    target_date: date | None
    notes: str | None


@dataclass(frozen=True)
class ImportDataset:
    accounts: list[AccountImport]
    categories: list[CategoryImport]
    transactions: list[TransactionImport]
    debts: list[DebtImport]
    assets: list[AssetImport]
    budgets: list[BudgetImport]
    goals: list[GoalImport]


def _optional_text(value) -> str | None:
    return None if pd.isna(value) else str(value).strip()


def _optional_float(value) -> float | None:
    return None if pd.isna(value) else float(value)


def _optional_int(value) -> int | None:
    return None if pd.isna(value) else int(value)


def _optional_date(value) -> date | None:
    if pd.isna(value):
        return None
    return pd.to_datetime(value).date()


def map_workbook(workbook: WorkbookData) -> ImportDataset:
    return ImportDataset(
        accounts=map_accounts(workbook),
        categories=map_categories(workbook),
        transactions=map_transactions(workbook),
        debts=map_debts(workbook),
        assets=map_assets(workbook),
        budgets=map_budgets(workbook),
        goals=map_goals(workbook),
    )


def map_accounts(workbook: WorkbookData) -> list[AccountImport]:
    if not workbook.has_sheet("Accounts"):
        return []

    df = workbook.get_sheet("Accounts")
    return [
        AccountImport(
            name=str(row["Name"]).strip(),
            account_type=str(row["Account Type"]).strip().lower(),
            institution=_optional_text(row.get("Institution")),
            current_balance=float(row["Current Balance"]),
            notes=_optional_text(row.get("Notes")),
        )
        for _, row in df.iterrows()
    ]


def map_categories(workbook: WorkbookData) -> list[CategoryImport]:
    if not workbook.has_sheet("Categories"):
        return []

    df = workbook.get_sheet("Categories")
    return [
        CategoryImport(
            name=str(row["Name"]).strip(),
            category_type=str(row["Category Type"]).strip().lower(),
        )
        for _, row in df.iterrows()
    ]


def map_transactions(workbook: WorkbookData) -> list[TransactionImport]:
    if not workbook.has_sheet("Transactions"):
        return []

    df = workbook.get_sheet("Transactions")
    return [
        TransactionImport(
            transaction_date=pd.to_datetime(row["Transaction Date"]).date(),
            merchant=_optional_text(row.get("Merchant")),
            description=_optional_text(row.get("Description")),
            amount=float(row["Amount"]),
            account_name=str(row["Account Name"]).strip(),
            category_name=str(row["Category Name"]).strip(),
            notes=_optional_text(row.get("Notes")),
        )
        for _, row in df.iterrows()
    ]


def map_debts(workbook: WorkbookData) -> list[DebtImport]:
    if not workbook.has_sheet("Debts"):
        return []

    df = workbook.get_sheet("Debts")
    return [
        DebtImport(
            name=str(row["Name"]).strip(),
            lender=_optional_text(row.get("Lender")),
            balance=float(row["Balance"]),
            interest_rate=_optional_float(row.get("Interest Rate")),
            minimum_payment=_optional_float(row.get("Minimum Payment")),
            due_day=_optional_int(row.get("Due Day")),
            notes=_optional_text(row.get("Notes")),
        )
        for _, row in df.iterrows()
    ]


def map_assets(workbook: WorkbookData) -> list[AssetImport]:
    if not workbook.has_sheet("Assets"):
        return []

    df = workbook.get_sheet("Assets")
    return [
        AssetImport(
            name=str(row["Name"]).strip(),
            asset_type=str(row["Asset Type"]).strip().lower(),
            current_value=float(row["Current Value"]),
            notes=_optional_text(row.get("Notes")),
        )
        for _, row in df.iterrows()
    ]


def map_budgets(workbook: WorkbookData) -> list[BudgetImport]:
    if not workbook.has_sheet("Budgets"):
        return []

    df = workbook.get_sheet("Budgets")
    return [
        BudgetImport(
            month=str(row["Month"]).strip(),
            category_name=str(row["Category Name"]).strip(),
            budgeted_amount=float(row["Budgeted Amount"]),
        )
        for _, row in df.iterrows()
    ]


def map_goals(workbook: WorkbookData) -> list[GoalImport]:
    if not workbook.has_sheet("Goals"):
        return []

    df = workbook.get_sheet("Goals")
    return [
        GoalImport(
            name=str(row["Name"]).strip(),
            target_amount=_optional_float(row.get("Target Amount")),
            current_amount=_optional_float(row.get("Current Amount")),
            target_date=_optional_date(row.get("Target Date")),
            notes=_optional_text(row.get("Notes")),
        )
        for _, row in df.iterrows()
    ]