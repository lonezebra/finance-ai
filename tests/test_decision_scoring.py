from finance_ai.decision.models import DecisionPriority, FinancialDecision, TimeHorizon
from finance_ai.decision.scoring import decision_score


def make_decision(**overrides) -> FinancialDecision:
    base = {
        "title": "Build emergency fund",
        "description": "Set aside three months of expenses.",
        "priority": DecisionPriority.HIGH,
        "expected_impact_score": 80.0,
        "confidence_score": 90.0,
        "ease_multiplier": 1.0,
        "time_horizon": TimeHorizon.SHORT_TERM,
        "reasoning": "Emergency fund is below three months of expenses.",
    }
    base.update(overrides)
    return FinancialDecision(**base)


def test_score_is_impact_times_confidence_fraction_times_ease():
    # 80 * (90/100) * 1.0
    assert decision_score(80.0, 90.0, 1.0) == 72.0


def test_score_is_rounded_to_two_decimals():
    # 75 * (85/100) * 0.6 = 38.25 exactly; use a case that would otherwise trail off
    assert decision_score(77.0, 83.0, 0.61) == round(77.0 * 0.83 * 0.61, 2)
    assert decision_score(1.0, 33.0, 0.33) == 0.11


def test_full_confidence_leaves_impact_untouched_when_frictionless():
    assert decision_score(50.0, 100.0, 1.0) == 50.0


def test_lower_confidence_lowers_the_score():
    assert decision_score(80.0, 50.0, 1.0) < decision_score(80.0, 90.0, 1.0)


def test_a_harder_decision_scores_lower_than_an_identical_easy_one():
    """Guards the direction of ease_multiplier -- the field was previously named
    difficulty_score, which read as though a higher value meant harder. It does not: a
    higher multiplier ranks a decision higher."""

    easy = decision_score(80.0, 90.0, 1.0)
    hard = decision_score(80.0, 90.0, 0.5)

    assert hard < easy


def test_zero_ease_multiplier_zeroes_the_score():
    assert decision_score(100.0, 100.0, 0.0) == 0.0


# --- the property on the model -----------------------------------------------------------


def test_model_score_property_matches_the_scoring_function():
    decision = make_decision(expected_impact_score=75.0, confidence_score=85.0, ease_multiplier=0.6)

    assert decision.score == decision_score(75.0, 85.0, 0.6)
    assert decision.score == 38.25


def test_scoring_module_does_not_import_the_models_module():
    """Regression guard for the circular import: scoring.py used to import
    FinancialDecision while models.py needed decision_score, which forced
    FinancialDecision.score to do a function-local import to break the cycle. scoring.py
    must stay dependency-free so that workaround can't creep back."""

    import importlib
    import sys

    for name in ("finance_ai.decision.scoring", "finance_ai.decision.models"):
        sys.modules.pop(name, None)

    importlib.import_module("finance_ai.decision.scoring")

    assert "finance_ai.decision.models" not in sys.modules
