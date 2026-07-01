from dataclasses import dataclass, field

from sqlalchemy import func

from finance_ai.db.database import SessionLocal
from finance_ai.db.models import Account, Asset, Budget, Category, Debt, Goal, Transaction


@dataclass(frozen=True)
class ConfidenceIssue:
    severity: str
    message: str


@dataclass(frozen=True)
class FinancialConfidenceScore:
    score: int
    issues: list[ConfidenceIssue] = field(default_factory=list)

    @property
    def label(self) -> str:
        if self.score >= 90:
            return "High"
        if self.score >= 70:
            return "Moderate"
        if self.score >= 50:
            return "Low"
        return "Very Low"


def _count(session, model) -> int:
    return int(session.query(func.count(model.id)).scalar() or 0)


def calculate_financial_confidence_score() -> FinancialConfidenceScore:
    issues: list[ConfidenceIssue] = []
    score = 100

    with SessionLocal() as session:
        account_count = _count(session, Account)
        transaction_count = _count(session, Transaction)
        category_count = _count(session, Category)
        debt_count = _count(session, Debt)
        asset_count = _count(session, Asset)
        budget_count = _count(session, Budget)
        goal_count = _count(session, Goal)

        if account_count == 0:
            score -= 20
            issues.append(ConfidenceIssue("high", "No accounts have been added."))

        if transaction_count == 0:
            score -= 20
            issues.append(ConfidenceIssue("high", "No transactions have been imported."))

        if category_count == 0:
            score -= 10
            issues.append(ConfidenceIssue("medium", "No categories have been added."))

        if budget_count == 0:
            score -= 10
            issues.append(ConfidenceIssue("medium", "No budgets have been created."))

        if debt_count == 0:
            score -= 5
            issues.append(ConfidenceIssue("low", "No debts have been added."))

        if asset_count == 0:
            score -= 5
            issues.append(ConfidenceIssue("low", "No assets have been added."))

        if goal_count == 0:
            score -= 5
            issues.append(ConfidenceIssue("low", "No financial goals have been added."))

        uncategorized = (
            session.query(func.count(Transaction.id))
            .filter(Transaction.category_id.is_(None))
            .scalar()
            or 0
        )

        if uncategorized > 0:
            score -= min(15, int(uncategorized))
            issues.append(
                ConfidenceIssue(
                    "medium",
                    f"{uncategorized} transactions are uncategorized.",
                )
            )

        debts_missing_rate = (
            session.query(func.count(Debt.id))
            .filter(Debt.interest_rate.is_(None))
            .scalar()
            or 0
        )

        if debts_missing_rate > 0:
            score -= min(10, int(debts_missing_rate) * 3)
            issues.append(
                ConfidenceIssue(
                    "medium",
                    f"{debts_missing_rate} debts are missing interest rates.",
                )
            )

    return FinancialConfidenceScore(score=max(score, 0), issues=issues)