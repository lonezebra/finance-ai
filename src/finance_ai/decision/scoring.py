def decision_score(
    expected_impact_score: float,
    confidence_score: float,
    ease_multiplier: float,
) -> float:
    """Deterministic ranking score for a financial decision. Higher means higher priority.

    Takes the three inputs as plain numbers rather than a FinancialDecision. That's what
    keeps this module free of any import from decision.models -- previously scoring.py
    imported FinancialDecision while models.py needed decision_score, a cycle that
    FinancialDecision.score worked around with a function-local import. With the dependency
    running one way only (models -> scoring), that workaround is gone.

    ease_multiplier scales the result down for decisions that are harder to actually carry
    out: 1.0 is frictionless, lower values mean more effort or disruption. Note the
    direction -- a *higher* multiplier ranks a decision *higher*.
    """

    return round(
        expected_impact_score * (confidence_score / 100) * ease_multiplier,
        2,
    )
