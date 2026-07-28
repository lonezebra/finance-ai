from datetime import datetime

from finance_ai.db.database import SessionLocal
from finance_ai.db.models import FinancialSnapshotRecord
from finance_ai.finance.metrics import FinancialSnapshot, create_financial_snapshot
from finance_ai.history.models import SnapshotRecord


def save_snapshot(month: str) -> SnapshotRecord:
    snapshot = create_financial_snapshot(month)

    with SessionLocal() as session:
        record = FinancialSnapshotRecord(
            created_at=datetime.now(),
            month=snapshot.month,
            total_assets=snapshot.total_assets,
            total_debt=snapshot.total_debt,
            net_worth=snapshot.net_worth,
            cash_balance=snapshot.cash_balance,
            monthly_income=snapshot.monthly_income,
            monthly_expenses=snapshot.monthly_expenses,
            monthly_cash_flow=snapshot.monthly_cash_flow,
            savings_rate=snapshot.savings_rate,
            debt_to_income_ratio=snapshot.debt_to_income_ratio,
            emergency_fund_months=snapshot.emergency_fund_months,
            essential_monthly_expenses=snapshot.essential_monthly_expenses,
            essential_emergency_fund_months=snapshot.essential_emergency_fund_months,
        )

        session.add(record)
        session.commit()
        session.refresh(record)

        return _to_snapshot_record(record)


def get_latest_snapshot() -> SnapshotRecord | None:
    with SessionLocal() as session:
        record = (
            session.query(FinancialSnapshotRecord)
            .order_by(FinancialSnapshotRecord.created_at.desc())
            .first()
        )

        return _to_snapshot_record(record) if record else None


def get_previous_snapshot() -> SnapshotRecord | None:
    with SessionLocal() as session:
        records = (
            session.query(FinancialSnapshotRecord)
            .order_by(FinancialSnapshotRecord.created_at.desc())
            .limit(2)
            .all()
        )

        if len(records) < 2:
            return None

        return _to_snapshot_record(records[1])


def _to_snapshot_record(record: FinancialSnapshotRecord) -> SnapshotRecord:
    snapshot = FinancialSnapshot(
        month=record.month,
        total_assets=record.total_assets,
        total_debt=record.total_debt,
        net_worth=record.net_worth,
        cash_balance=record.cash_balance,
        monthly_income=record.monthly_income,
        monthly_expenses=record.monthly_expenses,
        monthly_cash_flow=record.monthly_cash_flow,
        savings_rate=record.savings_rate,
        debt_to_income_ratio=record.debt_to_income_ratio,
        emergency_fund_months=record.emergency_fund_months,
        # Stays None for snapshots saved before this feature existed -- see the note on
        # the columns in db/models.py.
        essential_monthly_expenses=record.essential_monthly_expenses,
        essential_emergency_fund_months=record.essential_emergency_fund_months,
    )

    return SnapshotRecord(
        id=record.id,
        created_at=record.created_at,
        snapshot=snapshot,
    )