## Version 0.3

Desktop Shell

## Version 0.4

Strategic Advisor

## Version 0.5

Financial History Engine

## Version 0.6

Scenario Planning

v1 scope notes (see CLAUDE.md and Decision Log for full context):
- Scenarios support stacking multiple adjustments (income change, recurring expense change,
  extra debt payment, savings/investment contribution change, one-time purchase, one-time
  windfall) into a single projected snapshot.
- Single-month projection only. No multi-month/recurring trajectory modeling yet — deferred to
  a later version.
- Extra debt payment reduces total_debt and cash_balance but does not recalculate
  debt_to_income_ratio, since minimum_payment isn't derived from balance in the current schema.
  Revisit if amortization-aware DTI projection is wanted later.
- No persistence in v1 — scenarios are computed on demand and never written to the database
  (avoids conflating hypothetical projections with real financial history). A `scenarios` table
  to save/compare scenario runs over time is a candidate for a post-1.0 release.

## Version 1.0

Open CFO