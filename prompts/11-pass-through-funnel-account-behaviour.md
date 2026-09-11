# Prompt 11 — Pass-Through / Funnel-Account Behaviour (CH-11)

## Prerequisite
Prompts 00–10 complete.

## Section 2 fill-in
- **Engineering transformation:** Pass-Through / Funnel-Account Behaviour Detection
- **Problem to solve:** Suspicious behavior may involve rapid movement of incoming funds
  (credit quickly followed by near-equivalent outward transfer or dispersal to multiple
  beneficiaries) rather than unusually large individual transactions; this requires knowing
  who actually owns/controls the account (Prompt 01's linkage) and pairing CREDIT/DEBIT
  events by amount similarity and time proximity.
- **Desired production outcome:** `src/monitoring.py` detects incoming-credit-then-
  near-equivalent-outward-transfer patterns, including dispersal to multiple counterparties,
  using `TransactionEvent.direction`/`amount`/`counterparty_id`/`timestamp`.
- **Business/risk consequence:** Funnel/pass-through accounts are a standard layering
  technique; individually each leg looks like an ordinary transaction, so only temporal
  pairing surfaces the pattern.

## Repo grounding
- `challenges/CH-11.md`, row 11 of `docs/15_integrated_engineering_challenges.md`
- Evidence: `data/` for **CASE-012**
- Code: `src/monitoring.py`, `src/models_v2.py` (`TransactionEvent.direction`,
  `MonitoringAlert`)
- Specs: `specs/02_features/COMPLIANCE_MONITORING.md`
- Tests: `tests/test_integrated_compliance.py`

## Suggested change boundary
- In scope: a credit/debit-pairing pattern rule in `src/monitoring.py` with an
  amount-similarity tolerance and a time-proximity window, both as explicit versioned
  constants; test cases covering a single beneficiary and dispersal to multiple
  beneficiaries.
- Out of scope: velocity (Prompt 09) and structuring (Prompt 08) — a pass-through pattern is
  specifically the credit→debit pairing shape, not raw frequency or aggregate value.

## STOP conditions
1. Complete CLAUDE.md §3 and §15 before implementing.
2. Cover the zero-result case (credits with no matching debit) and the boundary of the
   amount-similarity tolerance explicitly, per CLAUDE.md §9.
3. Follow CLAUDE.md §22 in order and close with §24.
