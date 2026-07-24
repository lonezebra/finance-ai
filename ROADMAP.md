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

## Version 0.7

Decision Engine 2.0

v1 scope notes (see CLAUDE.md section 10.C for full context):
- Adds instance-level candidates on top of the existing snapshot-level ones: debt-specific
  payoff candidates (ranked avalanche-style by interest rate), an emergency-fund target
  candidate with a real dollar gap and suggested monthly contribution, an investment candidate
  recommending the actual monthly surplus, and goal-funding candidates computed from each
  Goal's target_amount/current_amount/target_date.
- generate_decisions() stays a pure, DB-free function (snapshot, debts, goals as explicit
  arguments) with a thin DB-reading wrapper, consistent with how create_financial_snapshot()
  and the Scenario Engine are structured — keeps decision logic testable without a database.
- Deferred to a follow-up pass: wiring each numeric decision candidate to an auto-generated
  Scenario projection (e.g. "pay off Card X" showing its projected net worth/emergency-fund
  impact via the Scenario Engine). This is explicitly called out in CLAUDE.md 10.C
  ("compare decisions through scenarios") but was intentionally scoped out of the first pass
  to keep candidate generation and scenario-linking as separate, reviewable pieces of work.

## Version 1.0

Open CFO