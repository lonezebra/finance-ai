from finance_ai.decision.models import FinancialDecision


def decision_score(decision: FinancialDecision) -> float:
    """
    Calculate a deterministic ranking score for a financial decision.

    Higher score means higher priority.
    """

    return round(
        decision.expected_impact_score
        * (decision.confidence_score / 100)
        * decision.difficulty_score,
        2,
    )