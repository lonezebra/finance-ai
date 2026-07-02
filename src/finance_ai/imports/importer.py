from finance_ai.db.database import SessionLocal
from finance_ai.db.models import Account, Asset, Budget, Category, Debt, Goal, Transaction
from finance_ai.imports.mapper import ImportDataset


def import_dataset(dataset: ImportDataset) -> dict[str, int]:
    imported_counts = {
        "accounts": 0,
        "categories": 0,
        "transactions": 0,
        "debts": 0,
        "assets": 0,
        "budgets": 0,
        "goals": 0,
    }

    with SessionLocal() as session:
        try:
            account_lookup: dict[str, Account] = {}
            category_lookup: dict[str, Category] = {}

            for item in dataset.accounts:
                account = Account(
                    name=item.name,
                    account_type=item.account_type,
                    institution=item.institution,
                    current_balance=item.current_balance,
                    notes=item.notes,
                )
                session.add(account)
                account_lookup[item.name] = account
                imported_counts["accounts"] += 1

            for item in dataset.categories:
                category = Category(
                    name=item.name,
                    category_type=item.category_type,
                )
                session.add(category)
                category_lookup[item.name] = category
                imported_counts["categories"] += 1

            session.flush()

            for item in dataset.transactions:
                transaction = Transaction(
                    transaction_date=item.transaction_date,
                    merchant=item.merchant,
                    description=item.description,
                    amount=item.amount,
                    account_id=account_lookup.get(item.account_name).id
                    if item.account_name in account_lookup
                    else None,
                    category_id=category_lookup.get(item.category_name).id
                    if item.category_name in category_lookup
                    else None,
                    notes=item.notes,
                )
                session.add(transaction)
                imported_counts["transactions"] += 1

            for item in dataset.debts:
                debt = Debt(
                    name=item.name,
                    lender=item.lender,
                    balance=item.balance,
                    interest_rate=item.interest_rate,
                    minimum_payment=item.minimum_payment,
                    due_day=item.due_day,
                    notes=item.notes,
                )
                session.add(debt)
                imported_counts["debts"] += 1

            for item in dataset.assets:
                asset = Asset(
                    name=item.name,
                    asset_type=item.asset_type,
                    current_value=item.current_value,
                    notes=item.notes,
                )
                session.add(asset)
                imported_counts["assets"] += 1

            for item in dataset.budgets:
                budget = Budget(
                    month=item.month,
                    category_name=item.category_name,
                    budgeted_amount=item.budgeted_amount,
                )
                session.add(budget)
                imported_counts["budgets"] += 1

            for item in dataset.goals:
                goal = Goal(
                    name=item.name,
                    target_amount=item.target_amount,
                    current_amount=item.current_amount,
                    target_date=item.target_date,
                    notes=item.notes,
                )
                session.add(goal)
                imported_counts["goals"] += 1

            session.commit()
            return imported_counts

        except Exception:
            session.rollback()
            raise