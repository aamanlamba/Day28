# Prompt 09 — Rapid Transaction Velocity (CH-09)

## Prerequisite
Prompts 00–08 complete.

## Section 2 fill-in
- **Engineering transformation:** Rapid Transaction Velocity Monitoring
- **Problem to solve:** Risk emerges from a sequence of events rather than any single
  transaction; reliable identity linkage (Prompt 01) prevents burst activity from being
  incorrectly split across aliases or duplicate customer records, which would otherwise mask
  the velocity signal.
- **Desired production outcome:** `src/monitoring.py` detects bursts of transactions, many
  distinct counterparties, rapid transfers or unusual frequency within a configurable,
  event-time-correct window (built on Prompt 07's ordering fix), and raises an alert with
  the contributing transaction IDs.
- **Business/risk consequence:** Point-in-time rules that only look at individual
  transactions miss sequence-based abuse (e.g. many rapid small transfers to different
  counterparties) that is a recognized money-laundering typology.

## Repo grounding
- `challenges/CH-09.md`, row 9 of `docs/15_integrated_engineering_challenges.md`
- Evidence: `data/` for **CASE-010** (shared with Prompt 07 — that prompt fixed the temporal
  substrate; this prompt adds the velocity pattern rule on top of it)
- Code: `src/monitoring.py`, `src/models_v2.py` (`MonitoringAlert`)
- Specs: `specs/02_features/COMPLIANCE_MONITORING.md`
- Tests: `tests/test_integrated_compliance.py`

## Suggested change boundary
- In scope: a velocity/frequency pattern rule in `src/monitoring.py`, its window and
  frequency threshold as explicit versioned constants, tests with bursts just under/at/over
  the threshold and with transactions spread across many vs. few counterparties.
- Out of scope: monetary-threshold structuring (Prompt 08) and pass-through/funnel pairing
  of credits and debits (Prompt 11) — those are different pattern shapes even though all
  three live in `src/monitoring.py`.

## STOP conditions
1. Complete CLAUDE.md §3 and §15 before implementing (verify Prompt 07's event-time
   windowing is actually in place first — this rule is meaningless without it).
2. Cover the zero-result case (no burst present) and the threshold-boundary case explicitly,
   per CLAUDE.md §9.
3. Follow CLAUDE.md §22 in order and close with §24.
