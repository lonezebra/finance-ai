from dataclasses import dataclass, field

from finance_ai.finance.metrics import FinancialSnapshot, create_financial_snapshot


@dataclass(frozen=True)
class HealthIssue:
    severity: str
    message: str


@dataclass(frozen=True)
class FinancialHealthScore:
    score: int
    issues: list[HealthIssue] = field(default_factory=list)

    @property
    def label(self) -> str:
        if self.score >= 90:
            return "Excellent"
        if self.score >= 80:
            return "Strong"
        if self.score >= 70:
            return "Stable"
        if self.score >= 60:
            return "Needs Attention"
        return "At Risk"


def calculate_financial_health_score(month: str) -> FinancialHealthScore:
    snapshot = create_financial_snapshot(month)
    return calculate_financial_health_from_snapshot(snapshot)


def calculate_financial_health_from_snapshot(snapshot: FinancialSnapshot) -> FinancialHealthScore:
    score = 100
    issues: list[HealthIssue] = []

    if snapshot.monthly_income <= 0:
        score -= 25
        issues.append(HealthIssue("high", "No monthly income is recorded."))
    elif snapshot.monthly_cash_flow < 0:
        score -= 25
        issues.append(HealthIssue("high", "Monthly cash flow is negative."))
    elif snapshot.savings_rate < 0.10:
        score -= 10
        issues.append(HealthIssue("medium", "Savings rate is below 10%."))
    elif snapshot.savings_rate < 0.20:
        score -= 5
        issues.append(HealthIssue("low", "Savings rate is below 20%."))

    if snapshot.emergency_fund_months < 1:
        score -= 25
        issues.append(HealthIssue("high", "Emergency fund is below 1 month of expenses."))
    elif snapshot.emergency_fund_months < 3:
        score -= 15
        issues.append(HealthIssue("medium", "Emergency fund is below 3 months of expenses."))
    elif snapshot.emergency_fund_months < 6:
        score -= 5
        issues.append(HealthIssue("low", "Emergency fund is below 6 months of expenses."))

    if snapshot.debt_to_income_ratio > 0.50:
        score -= 20
        issues.append(HealthIssue("high", "Debt-to-income ratio is above 50%."))
    elif snapshot.debt_to_income_ratio > 0.36:
        score -= 10
        issues.append(HealthIssue("medium", "Debt-to-income ratio is above 36%."))
    elif snapshot.debt_to_income_ratio > 0.25:
        score -= 5
        issues.append(HealthIssue("low", "Debt-to-income ratio is above 25%."))

    if snapshot.net_worth < 0:
        score -= 15
        issues.append(HealthIssue("medium", "Net worth is negative."))

    return FinancialHealthScore(score=max(score, 0), issues=issues)