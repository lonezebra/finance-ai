from dataclasses import dataclass
from enum import Enum

from finance_ai.finance.confidence import FinancialConfidenceScore
from finance_ai.finance.health import FinancialHealthScore
from finance_ai.finance.metrics import FinancialSnapshot


class OpportunityCategory(str, Enum):
    DATA_QUALITY = "data_quality"
    CASH_FLOW = "cash_flow"
    EMERGENCY_FUND = "emergency_fund"
    DEBT = "debt"
    SAVINGS = "savings"
    MAINTENANCE = "maintenance"


class Difficulty(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass(frozen=True)
class Opportunity:
    title: str
    description: str
    category: OpportunityCategory
    impact_score: int
    confidence_score: int
    difficulty: Difficulty
    time_horizon: str
    reason: str

    @property
    def opportunity_score(self) -> float:
        difficulty_multiplier = {
            Difficulty.LOW: 1.0,
            Difficulty.MEDIUM: 0.75,
            Difficulty.HIGH: 0.5,
        }[self.difficulty]

        return round(
            self.impact_score
            * (self.confidence_score / 100)
            * difficulty_multiplier,
            2,
        )


def generate_opportunities(
    snapshot: FinancialSnapshot,
    health: FinancialHealthScore,
    confidence: FinancialConfidenceScore,
) -> list[Opportunity]:
    opportunities: list[Opportunity] = []

    if confidence.score < 70:
        opportunities.append(
            Opportunity(
                title="Improve financial data quality",
                description="Add missing accounts, transactions, budgets, goals, or debt details.",
                category=OpportunityCategory.DATA_QUALITY,
                impact_score=95,
                confidence_score=100,
                difficulty=Difficulty.LOW,
                time_horizon="Immediate",
                reason="Open CFO cannot make high-confidence recommendations until the data is more complete.",
            )
        )

    if snapshot.monthly_cash_flow < 0:
        opportunities.append(
            Opportunity(
                title="Stabilize monthly cash flow",
                description="Review spending and income to eliminate negative monthly cash flow.",
                category=OpportunityCategory.CASH_FLOW,
                impact_score=90,
                confidence_score=confidence.score,
                difficulty=Difficulty.MEDIUM,
                time_horizon="This month",
                reason="Negative cash flow weakens every other financial goal.",
            )
        )

    if snapshot.emergency_fund_months < 3:
        opportunities.append(
            Opportunity(
                title="Build emergency fund to 3 months",
                description="Prioritize cash reserves until essential expenses are covered for at least 3 months.",
                category=OpportunityCategory.EMERGENCY_FUND,
                impact_score=85,
                confidence_score=confidence.score,
                difficulty=Difficulty.MEDIUM,
                time_horizon="1-12 months",
                reason="Emergency fund coverage below 3 months creates financial fragility.",
            )
        )
    elif snapshot.emergency_fund_months < 6:
        opportunities.append(
            Opportunity(
                title="Build emergency fund to 6 months",
                description="Continue increasing cash reserves toward a 6-month emergency fund.",
                category=OpportunityCategory.EMERGENCY_FUND,
                impact_score=65,
                confidence_score=confidence.score,
                difficulty=Difficulty.MEDIUM,
                time_horizon="3-18 months",
                reason="Six months of expenses provides stronger protection against income disruption.",
            )
        )

    if snapshot.debt_to_income_ratio > 0.36:
        opportunities.append(
            Opportunity(
                title="Reduce debt-to-income ratio",
                description="Evaluate whether extra debt payments or refinancing would improve flexibility.",
                category=OpportunityCategory.DEBT,
                impact_score=75,
                confidence_score=confidence.score,
                difficulty=Difficulty.MEDIUM,
                time_horizon="3-24 months",
                reason="Debt-to-income above 36% can limit flexibility and increase financial risk.",
            )
        )

    if snapshot.savings_rate < 0.10 and snapshot.monthly_income > 0:
        opportunities.append(
            Opportunity(
                title="Increase savings rate",
                description="Look for a realistic way to increase savings toward at least 10% of income.",
                category=OpportunityCategory.SAVINGS,
                impact_score=70,
                confidence_score=confidence.score,
                difficulty=Difficulty.MEDIUM,
                time_horizon="This month",
                reason="A savings rate below 10% slows wealth building and goal progress.",
            )
        )

    if not opportunities:
        opportunities.append(
            Opportunity(
                title="Maintain current plan",
                description="No urgent opportunities were detected from the current snapshot.",
                category=OpportunityCategory.MAINTENANCE,
                impact_score=30,
                confidence_score=confidence.score,
                difficulty=Difficulty.LOW,
                time_horizon="Ongoing",
                reason="Current snapshot does not show major issues requiring immediate action.",
            )
        )

    return sorted(
        opportunities,
        key=lambda opportunity: opportunity.opportunity_score,
        reverse=True,
    )