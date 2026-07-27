from dataclasses import dataclass, field

from finance_ai.finance.metrics import FinancialSnapshot, create_financial_snapshot
from finance_ai.finance.thresholds import DTI_CONSERVATIVE, DTI_ELEVATED, DTI_HIGH


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

    if snapshot.monthly_income <= 0:
        # DTI is debt payments / income, so it's undefined without income. The snapshot
        # stores 0.0 (from _safe_divide's zero-denominator guard), which would otherwise
        # fall through every threshold below and read as a perfect 0% debt burden -- an
        # unemployed user with real debt obligations would be silently credited for it.
        # Flagged rather than penalized: the -25 above already reflects the root cause
        # (no income), so charging again here would double-count one problem. The value
        # added is transparency -- the user sees the metric wasn't assessed instead of
        # seeing nothing at all.
        issues.append(
            HealthIssue(
                "medium",
                "Debt payments can't be assessed as a share of income "
                "without recorded income.",
            )
        )
    elif snapshot.debt_to_income_ratio > DTI_HIGH:
        score -= 20
        issues.append(
            HealthIssue(
                "high",
                f"Debt payments are above {DTI_HIGH:.0%} of take-home income.",
            )
        )
    elif snapshot.debt_to_income_ratio > DTI_ELEVATED:
        score -= 10
        issues.append(
            HealthIssue(
                "medium",
                f"Debt payments are above {DTI_ELEVATED:.0%} of take-home income.",
            )
        )
    elif snapshot.debt_to_income_ratio > DTI_CONSERVATIVE:
        score -= 5
        issues.append(
            HealthIssue(
                "low",
                f"Debt payments are above {DTI_CONSERVATIVE:.0%} of take-home income.",
            )
        )

    # Negative net worth was previously a flat -15 cliff: -$1 and -$500,000 cost exactly
    # the same. Scaled against annual income instead, the standard reference point for
    # "how deep is this hole relative to what you earn" -- a new graduate slightly
    # underwater on student loans is a materially different situation from someone owing
    # several years of income. Thresholds are heuristics, in the same spirit as the DTI
    # and emergency-fund bands above, not lender-grade rules.
    if snapshot.net_worth < 0:
        annual_income = snapshot.monthly_income * 12

        if annual_income <= 0:
            # No income to scale against -- keep the original flat penalty rather than
            # guessing at a magnitude we have no denominator for.
            score -= 15
            issues.append(HealthIssue("medium", "Net worth is negative."))
        else:
            shortfall_vs_income = abs(snapshot.net_worth) / annual_income

            if shortfall_vs_income > 2.0:
                score -= 20
                issues.append(
                    HealthIssue(
                        "high",
                        "Net worth is negative by more than two years of income.",
                    )
                )
            elif shortfall_vs_income > 0.5:
                score -= 12
                issues.append(
                    HealthIssue(
                        "medium",
                        "Net worth is negative by more than six months of income.",
                    )
                )
            else:
                score -= 5
                issues.append(
                    HealthIssue("low", "Net worth is slightly negative.")
                )

    return FinancialHealthScore(score=max(score, 0), issues=issues)