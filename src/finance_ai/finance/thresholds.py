"""Deterministic bands for interpreting financial metrics.

Centralized because the debt-to-income bands were previously bare literals duplicated
across health.py, reports/engine.py, decision/engine.py and opportunities.py -- four copies
that could drift apart, and that all had to move together to correct the income basis
described below.
"""

# Open CFO's monthly_income is the sum of positive transactions for the month -- money that
# actually landed in an account, i.e. take-home (net) pay. The template's own example makes
# this concrete: a "Paycheck" of 3500 deposited into Checking. Gross pay never lands in a
# checking account.
#
# The conventional debt-to-income bands people know (25% / 36% / 50%) are lender figures
# defined on GROSS income. Applying them to a net denominator reports a systematically
# inflated ratio -- the same debt burden looks worse purely because the denominator is
# smaller -- which produced false "elevated debt" concerns, a Health Score penalty, and an
# inflated ranking for "reduce debt burden" in the Decision Engine.
#
# These bands are the conventional gross ones scaled for take-home pay, on the basis that
# net is typically around 75-80% of gross for a household with payroll withholding. They
# are heuristics in the same spirit as the emergency-fund and savings-rate bands: useful
# guidance, not lender-grade rules. A true lender DTI would require the user's gross income,
# which the data model does not currently capture -- deriving it from net via an assumed tax
# rate would be fabricating a figure, which Rule 3 rules out.
DTI_CONSERVATIVE = 0.30
"""At or below this share of take-home pay, the debt load counts as a strength."""

DTI_ELEVATED = 0.45
"""Above this share of take-home pay, the debt load is worth attention."""

DTI_HIGH = 0.60
"""Above this share of take-home pay, the debt load is a serious constraint."""
