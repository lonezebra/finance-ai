from dataclasses import dataclass, field

from finance_ai.finance.confidence import FinancialConfidenceScore, calculate_financial_confidence_score
from finance_ai.finance.health import FinancialHealthScore, calculate_financial_health_from_snapshot
from finance_ai.finance.metrics import FinancialSnapshot, create_financial_snapshot
from finance_ai.finance.opportunities import Opportunity, generate_opportunities


@dataclass(frozen=True)
class OpenCFOBriefing:
    snapshot: FinancialSnapshot
    confidence: FinancialConfidenceScore
    health: FinancialHealthScore
    top_opportunities: list[Opportunity] = field(default_factory=list)

    @property
    def headline(self) -> str:
        if self.confidence.score < 50:
            return (
                "Your financial data needs attention before Open CFO can make "
                "high-confidence recommendations."
            )

        if self.health.score < 60:
            return "Your financial health requires attention. Review today's opportunities."

        if self.health.score < 80:
            return "Your finances are stable, but there are opportunities to improve."

        return "Your finances appear healthy and your data is current."


def create_open_cfo_briefing(month: str) -> OpenCFOBriefing:
    snapshot = create_financial_snapshot(month)
    confidence = calculate_financial_confidence_score()
    health = calculate_financial_health_from_snapshot(snapshot)
    top_opportunities = generate_opportunities(snapshot, health, confidence)

    return OpenCFOBriefing(
        snapshot=snapshot,
        confidence=confidence,
        health=health,
        top_opportunities=top_opportunities,
    )