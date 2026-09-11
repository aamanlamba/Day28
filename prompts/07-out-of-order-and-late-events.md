# Prompt 07 — Out-of-Order and Late Events (CH-07)

## Prerequisite
Prompts 00–06 complete.

## Section 2 fill-in
- **Engineering transformation:** Out-of-Order and Late Events
- **Problem to solve:** Events may arrive after newer transactions or significantly after
  their actual business timestamp; identity and KYC context may also have changed by the
  time a late event arrives, requiring the correct *historical* state to be reconstructed.
  Check whether `src/monitoring.py` currently windows/sorts by `TransactionEvent.timestamp`
  (event time) or by list/arrival order (ingestion order).
- **Desired production outcome:** Temporal rules use event time and explicit windows, and
  reconstruct the customer/KYC context as it existed at the event's business timestamp, not
  whatever the current-request-time context happens to be.
- **Business/risk consequence:** Rules that key off ingestion order instead of event time
  miscompute windowed patterns (structuring, velocity) and can attribute a transaction to
  the wrong identity/KYC state, producing an alert that cannot be reproduced or defended
  later.

## Repo grounding
- `challenges/CH-07.md`, row 7 of `docs/15_integrated_engineering_challenges.md`
- Evidence: `data/` for **CASE-010** (shared with Prompt 09 — that prompt covers velocity
  detection logic; this prompt covers the temporal-ordering/windowing mechanics underneath
  it, so land this one first)
- Code: `src/monitoring.py`, `src/models_v2.py` (`TransactionEvent.timestamp`)
- Specs: `specs/02_features/COMPLIANCE_MONITORING.md`, `specs/03_non_functional/NFR.md`
- Tests: `tests/test_integrated_compliance.py`

## Suggested change boundary
- In scope: sorting/windowing logic in `src/monitoring.py` to use event time; a test that
  feeds the same transactions in shuffled/reversed order and asserts identical output to the
  correctly-ordered case.
- Out of scope: the specific structuring/velocity/pass-through pattern rules that will run
  on top of correct ordering (Prompts 08, 09, 11) — this prompt only guarantees the
  windowing substrate is temporally correct.

## STOP conditions
1. Complete CLAUDE.md §3 and §15 before implementing. Demonstrate the gap first: a failing
   test showing that reordering the same transaction list changes the monitoring result.
2. Cover late events (arriving after newer ones) and out-of-order events (arriving in wrong
   sequence) as distinct edge cases per CLAUDE.md §9.
3. Follow CLAUDE.md §22 in order and close with §24.
