import logging
from collections.abc import Callable
from contextlib import AbstractContextManager
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.orm import Session

from finance_ai.db.database import SessionLocal
from finance_ai.db.models import (
    Account,
    Asset,
    Budget,
    Category,
    Debt,
    Goal,
    ImportBatch,
    Transaction,
)
from finance_ai.imports.mapper import (
    AccountImport,
    AssetImport,
    BudgetImport,
    CategoryImport,
    DebtImport,
    GoalImport,
    ImportDataset,
    TransactionImport,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class EntityImportResult:
    created: int = 0
    updated: int = 0
    skipped_duplicate: int = 0

    @property
    def total(self) -> int:
        return self.created + self.updated + self.skipped_duplicate


@dataclass(frozen=True)
class ImportResult:
    accounts: EntityImportResult
    categories: EntityImportResult
    transactions: EntityImportResult
    debts: EntityImportResult
    assets: EntityImportResult
    budgets: EntityImportResult
    goals: EntityImportResult

    def by_label(self) -> list[tuple[str, EntityImportResult]]:
        return [
            ("accounts", self.accounts),
            ("categories", self.categories),
            ("transactions", self.transactions),
            ("debts", self.debts),
            ("assets", self.assets),
            ("budgets", self.budgets),
            ("goals", self.goals),
        ]

    def summary(self) -> str:
        parts = []
        for label, result in self.by_label():
            if result.created:
                parts.append(f"{result.created} {label} created")
            if result.updated:
                parts.append(f"{result.updated} {label} updated")
            if result.skipped_duplicate:
                parts.append(f"{result.skipped_duplicate} duplicate {label} skipped")

        return ", ".join(parts) if parts else "No changes."


def import_dataset(
    dataset: ImportDataset,
    source_file: str,
    source_type: str = "excel",
    session_factory: Callable[[], AbstractContextManager[Session]] = SessionLocal,
) -> ImportResult:
    """Re-importing the same workbook (or one with overlapping data) is safe: accounts,
    categories, debts, assets, budgets, and goals are upserted by their natural key (name,
    or month+category for budgets) so re-running an import to refresh balances updates
    existing rows instead of duplicating them. Transactions have no natural key -- they're
    an append-only ledger, not current state -- so they're matched on an exact full-row
    fingerprint (date, merchant, description, amount, account, category, notes) and skipped
    if that exact row already exists; anything that differs even slightly (e.g. an edited
    note) is treated as a new transaction rather than an update.
    """

    logger.info("Starting import from %s (%s)", source_file, source_type)

    with session_factory() as session:
        try:
            accounts_result, account_lookup = _upsert_accounts(session, dataset.accounts)
            categories_result, category_lookup = _upsert_categories(session, dataset.categories)

            # Newly-created accounts/categories need real primary keys before transactions
            # can reference them by id.
            session.flush()

            transactions_result = _import_transactions(
                session, dataset.transactions, account_lookup, category_lookup
            )
            debts_result = _upsert_debts(session, dataset.debts)
            assets_result = _upsert_assets(session, dataset.assets)
            budgets_result = _upsert_budgets(session, dataset.budgets)
            goals_result = _upsert_goals(session, dataset.goals)

            result = ImportResult(
                accounts=accounts_result,
                categories=categories_result,
                transactions=transactions_result,
                debts=debts_result,
                assets=assets_result,
                budgets=budgets_result,
                goals=goals_result,
            )

            session.add(
                ImportBatch(
                    imported_at=datetime.now(),
                    source_file=source_file,
                    source_type=source_type,
                    status="completed",
                    notes=result.summary(),
                )
            )

            session.commit()
            logger.info("Import from %s complete: %s", source_file, result.summary())
            return result

        except Exception:
            logger.exception("Import from %s failed", source_file)
            session.rollback()
            raise


def _upsert_accounts(
    session: Session, items: list[AccountImport]
) -> tuple[EntityImportResult, dict[str, Account]]:
    existing = {account.name: account for account in session.query(Account).all()}
    lookup: dict[str, Account] = {}
    created = updated = 0

    for item in items:
        account = existing.get(item.name)
        if account is None:
            account = Account(name=item.name)
            session.add(account)
            existing[item.name] = account
            created += 1
        else:
            updated += 1

        account.account_type = item.account_type
        account.institution = item.institution
        account.current_balance = item.current_balance
        account.notes = item.notes

        lookup[item.name] = account

    return EntityImportResult(created=created, updated=updated), lookup


def _upsert_categories(
    session: Session, items: list[CategoryImport]
) -> tuple[EntityImportResult, dict[str, Category]]:
    existing = {category.name: category for category in session.query(Category).all()}
    lookup: dict[str, Category] = {}
    created = updated = 0

    for item in items:
        category = existing.get(item.name)
        if category is None:
            category = Category(name=item.name)
            session.add(category)
            existing[item.name] = category
            created += 1
        else:
            updated += 1

        category.category_type = item.category_type

        lookup[item.name] = category

    return EntityImportResult(created=created, updated=updated), lookup


def _import_transactions(
    session: Session,
    items: list[TransactionImport],
    account_lookup: dict[str, Account],
    category_lookup: dict[str, Category],
) -> EntityImportResult:
    existing_fingerprints = {
        (
            row.transaction_date,
            row.merchant,
            row.description,
            row.amount,
            row.account_id,
            row.category_id,
            row.notes,
        )
        for row in session.query(Transaction).all()
    }

    created = skipped = 0

    for item in items:
        account = account_lookup.get(item.account_name)
        category = category_lookup.get(item.category_name)
        account_id = account.id if account else None
        category_id = category.id if category else None

        fingerprint = (
            item.transaction_date,
            item.merchant,
            item.description,
            item.amount,
            account_id,
            category_id,
            item.notes,
        )

        if fingerprint in existing_fingerprints:
            skipped += 1
            continue

        session.add(
            Transaction(
                transaction_date=item.transaction_date,
                merchant=item.merchant,
                description=item.description,
                amount=item.amount,
                account_id=account_id,
                category_id=category_id,
                notes=item.notes,
            )
        )
        existing_fingerprints.add(fingerprint)
        created += 1

    return EntityImportResult(created=created, skipped_duplicate=skipped)


def _upsert_debts(session: Session, items: list[DebtImport]) -> EntityImportResult:
    existing = {debt.name: debt for debt in session.query(Debt).all()}
    created = updated = 0

    for item in items:
        debt = existing.get(item.name)
        if debt is None:
            debt = Debt(name=item.name)
            session.add(debt)
            existing[item.name] = debt
            created += 1
        else:
            updated += 1

        debt.lender = item.lender
        debt.balance = item.balance
        debt.interest_rate = item.interest_rate
        debt.minimum_payment = item.minimum_payment
        debt.due_day = item.due_day
        debt.notes = item.notes

    return EntityImportResult(created=created, updated=updated)


def _upsert_assets(session: Session, items: list[AssetImport]) -> EntityImportResult:
    existing = {asset.name: asset for asset in session.query(Asset).all()}
    created = updated = 0

    for item in items:
        asset = existing.get(item.name)
        if asset is None:
            asset = Asset(name=item.name)
            session.add(asset)
            existing[item.name] = asset
            created += 1
        else:
            updated += 1

        asset.asset_type = item.asset_type
        asset.current_value = item.current_value
        asset.notes = item.notes

    return EntityImportResult(created=created, updated=updated)


def _upsert_budgets(session: Session, items: list[BudgetImport]) -> EntityImportResult:
    existing = {
        (budget.month, budget.category_name): budget
        for budget in session.query(Budget).all()
    }
    created = updated = 0

    for item in items:
        key = (item.month, item.category_name)
        budget = existing.get(key)
        if budget is None:
            budget = Budget(month=item.month, category_name=item.category_name)
            session.add(budget)
            existing[key] = budget
            created += 1
        else:
            updated += 1

        budget.budgeted_amount = item.budgeted_amount

    return EntityImportResult(created=created, updated=updated)


def _upsert_goals(session: Session, items: list[GoalImport]) -> EntityImportResult:
    existing = {goal.name: goal for goal in session.query(Goal).all()}
    created = updated = 0

    for item in items:
        goal = existing.get(item.name)
        if goal is None:
            goal = Goal(name=item.name)
            session.add(goal)
            existing[item.name] = goal
            created += 1
        else:
            updated += 1

        goal.target_amount = item.target_amount
        goal.current_amount = item.current_amount
        goal.target_date = item.target_date
        goal.notes = item.notes

    return EntityImportResult(created=created, updated=updated)
