from finance_ai.finance.health import calculate_financial_health_from_snapshot
from finance_ai.finance.metrics import FinancialSnapshot
from finance_ai.finance.thresholds import DTI_CONSERVATIVE, DTI_ELEVATED, DTI_HIGH


def make_snapshot(**overrides) -> FinancialSnapshot:
    """A deliberately healthy baseline: positive income and cash flow, 20% savings rate,
    6 months of emergency fund, conservative DTI, positive net worth. Scores 100, so any
    test can override a single field and attribute the whole difference to that field."""

    base = {
        "month": "2026-06",
        "total_assets": 100000.0,
        "total_debt": 20000.0,
        "net_worth": 80000.0,
        "cash_balance": 33600.0,
        "monthly_income": 7000.0,
        "monthly_expenses": 5600.0,
        "monthly_cash_flow": 1400.0,
        "savings_rate": 0.20,
        "debt_to_income_ratio": 0.20,
        "emergency_fund_months": 6.0,
    }
    base.update(overrides)
    return FinancialSnapshot(**base)


def test_healthy_baseline_scores_100_with_no_issues():
    result = calculate_financial_health_from_snapshot(make_snapshot())

    assert result.score == 100
    assert result.label == "Excellent"
    assert result.issues == []


# --- income / cash flow / savings rate ladder -------------------------------------------


def test_no_income_is_the_most_severe_cash_flow_problem():
    result = calculate_financial_health_from_snapshot(make_snapshot(monthly_income=0.0))

    assert any("No monthly income" in issue.message for issue in result.issues)
    assert any(issue.severity == "high" for issue in result.issues)


def test_negative_cash_flow_costs_more_than_a_merely_low_savings_rate():
    negative = calculate_financial_health_from_snapshot(
        make_snapshot(monthly_cash_flow=-500.0, savings_rate=-0.07)
    )
    low_savings = calculate_financial_health_from_snapshot(
        make_snapshot(monthly_cash_flow=350.0, savings_rate=0.05)
    )

    assert negative.score < low_savings.score


def test_savings_rate_tiers_are_ordered():
    under_10 = calculate_financial_health_from_snapshot(make_snapshot(savings_rate=0.05))
    under_20 = calculate_financial_health_from_snapshot(make_snapshot(savings_rate=0.15))

    assert under_10.score < under_20.score < 100


# --- emergency fund ---------------------------------------------------------------------


def test_emergency_fund_tiers_are_ordered():
    under_1 = calculate_financial_health_from_snapshot(make_snapshot(emergency_fund_months=0.5))
    under_3 = calculate_financial_health_from_snapshot(make_snapshot(emergency_fund_months=2.0))
    under_6 = calculate_financial_health_from_snapshot(make_snapshot(emergency_fund_months=4.0))

    assert under_1.score < under_3.score < under_6.score < 100


def test_six_months_of_emergency_fund_is_not_penalized():
    result = calculate_financial_health_from_snapshot(make_snapshot(emergency_fund_months=6.0))

    assert not any("Emergency fund" in issue.message for issue in result.issues)


# --- debt-to-income ---------------------------------------------------------------------


def test_debt_to_income_tiers_are_ordered():
    # Derived from the threshold constants rather than hardcoded, so re-baselining the bands
    # can't leave this test silently asserting the wrong tiers.
    over_high = calculate_financial_health_from_snapshot(
        make_snapshot(debt_to_income_ratio=DTI_HIGH + 0.05)
    )
    over_elevated = calculate_financial_health_from_snapshot(
        make_snapshot(debt_to_income_ratio=DTI_ELEVATED + 0.05)
    )
    over_conservative = calculate_financial_health_from_snapshot(
        make_snapshot(debt_to_income_ratio=DTI_CONSERVATIVE + 0.05)
    )

    assert over_high.score < over_elevated.score < over_conservative.score < 100


def test_debt_at_the_conservative_band_is_not_penalized():
    result = calculate_financial_health_from_snapshot(
        make_snapshot(debt_to_income_ratio=DTI_CONSERVATIVE)
    )

    assert result.score == 100
    assert not any("Debt payments" in issue.message for issue in result.issues)


def test_bands_are_calibrated_for_take_home_not_gross_income():
    """The conventional 36% lender band is defined on gross income. Open CFO's income figure
    is take-home, so a burden at 36% of take-home is materially lighter than 36% of gross and
    should no longer be flagged as elevated."""

    result = calculate_financial_health_from_snapshot(make_snapshot(debt_to_income_ratio=0.36))

    assert not any("elevated" in issue.message.lower() for issue in result.issues)
    # It's above the conservative band, so it's still worth a low-severity mention.
    assert any(issue.severity == "low" for issue in result.issues)


def test_zero_income_flags_dti_as_unmeasurable_rather_than_silently_passing():
    """Regression test for the masking bug: debt_to_income_ratio is debt payments / income,
    which _safe_divide stores as 0.0 when income is 0. That used to fall through every
    threshold and read as a perfect 0% debt burden, so an unemployed user with real debt
    obligations was silently credited for it."""

    result = calculate_financial_health_from_snapshot(
        make_snapshot(monthly_income=0.0, debt_to_income_ratio=0.0, total_debt=90000.0)
    )

    assert any(
        "can't be assessed" in issue.message for issue in result.issues
    )


def test_zero_income_does_not_double_penalize_for_the_unmeasurable_dti():
    """The -25 for "no income" already reflects the root cause, so flagging DTI as
    unmeasurable adds transparency without charging twice for one problem."""

    # Everything else in the baseline is healthy, so the only penalty that should land is
    # the -25 for having no income -- the unmeasurable DTI must not add a second charge.
    no_income = calculate_financial_health_from_snapshot(
        make_snapshot(monthly_income=0.0, debt_to_income_ratio=0.0)
    )

    assert no_income.score == 75


# --- net worth --------------------------------------------------------------------------


def test_negative_net_worth_is_scaled_by_magnitude_not_a_flat_cliff():
    """Regression test: -$1 and -$500,000 used to cost exactly the same 15 points."""

    barely = calculate_financial_health_from_snapshot(make_snapshot(net_worth=-1.0))
    moderate = calculate_financial_health_from_snapshot(make_snapshot(net_worth=-50000.0))
    severe = calculate_financial_health_from_snapshot(make_snapshot(net_worth=-500000.0))

    assert severe.score < moderate.score < barely.score < 100


def test_negative_net_worth_severity_labels_escalate():
    barely = calculate_financial_health_from_snapshot(make_snapshot(net_worth=-1.0))
    severe = calculate_financial_health_from_snapshot(make_snapshot(net_worth=-500000.0))

    assert any(issue.severity == "low" for issue in barely.issues)
    assert any(issue.severity == "high" for issue in severe.issues)


def test_negative_net_worth_falls_back_to_a_flat_penalty_without_income_to_scale_against():
    """With no income there's no denominator to measure the shortfall against, so the
    original flat penalty is kept rather than guessing at a magnitude."""

    result = calculate_financial_health_from_snapshot(
        make_snapshot(monthly_income=0.0, net_worth=-500000.0)
    )

    assert any(issue.message == "Net worth is negative." for issue in result.issues)


def test_positive_net_worth_is_not_penalized():
    result = calculate_financial_health_from_snapshot(make_snapshot(net_worth=1.0))

    assert not any("Net worth" in issue.message for issue in result.issues)


# --- score bounds and labels ------------------------------------------------------------


def test_score_never_goes_below_zero():
    result = calculate_financial_health_from_snapshot(
        make_snapshot(
            monthly_income=0.0,
            monthly_cash_flow=-5000.0,
            savings_rate=0.0,
            emergency_fund_months=0.0,
            debt_to_income_ratio=0.0,
            net_worth=-500000.0,
        )
    )

    assert result.score >= 0


def test_labels_map_to_the_documented_bands():
    from finance_ai.finance.health import FinancialHealthScore

    assert FinancialHealthScore(score=95).label == "Excellent"
    assert FinancialHealthScore(score=85).label == "Strong"
    assert FinancialHealthScore(score=75).label == "Stable"
    assert FinancialHealthScore(score=65).label == "Needs Attention"
    assert FinancialHealthScore(score=40).label == "At Risk"
