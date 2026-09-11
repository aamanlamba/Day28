# Prompt 06 — Transaction-Hook Idempotency (CH-06)

## Prerequisite
Prompts 00–05 complete (identity-side foundation exists). This is the first
transaction/monitoring-side prompt.

## Section 2 fill-in
- **Engineering transformation:** Transaction-Hook Idempotency / Event-Hook Deduplication
- **Problem to solve:** Streaming systems may redeliver the same event, causing duplicated
  alerts, cases or risk-score inflation; `MonitoringResult` in `src/models_v2.py` already
  has `received_transaction_count`, `processed_transaction_count` and `hook_warnings`
  fields — determine in forensics whether `src/monitoring.py` actually deduplicates by
  `transaction_id` or whether these fields are currently always equal (i.e. dedup is not
  implemented).
- **Desired production outcome:** Redelivered/duplicate transaction events are detected by
  a stable idempotency key and processed exactly once for scoring purposes, using the
  canonical customer/account correlation key from Prompt 01; duplicates are visible (via
  `hook_warnings` or an equivalent) rather than silently dropped or silently double-counted.
- **Business/risk consequence:** A redelivered high-value transaction can push a customer
  over a structuring or velocity threshold that was never actually crossed, generating a
  false compliance alert (or, if dedup double-suppresses, hiding a real one).

## Repo grounding
- `challenges/CH-06.md`, row 6 of `docs/15_integrated_engineering_challenges.md`
- Register question 14 in `docs/engineering_challenge_register.md`
- Evidence: `data/` for **CASE-009** (shared with Prompt 01 — that prompt's concern is
  identifier alignment, this prompt's is duplicate delivery of the same transaction)
- Code: `src/monitoring.py`, `src/models_v2.py` (`TransactionEvent`, `MonitoringResult`),
  `src/repository.py`
- Specs: `specs/02_features/COMPLIANCE_MONITORING.md`, `specs/03_non_functional/NFR.md`
- Tests: `tests/test_integrated_compliance.py`

## Suggested change boundary
- In scope: dedup logic keyed on `transaction_id` in `src/monitoring.py`, populating
  `hook_warnings` with a genuine reason when a duplicate is dropped, tests that POST/replay
  the same case evaluation twice and assert identical, non-inflated results.
- Out of scope: out-of-order/late-arrival handling (Prompt 07) — a duplicate event and a
  late event are different failure modes; don't conflate the fixes.

## STOP conditions
1. Complete CLAUDE.md §3 and §15 before implementing — first prove the gap with a failing
   test that replays a transaction and shows the current alert/score inflating.
2. Idempotency behavior must be deterministic and replayable per CLAUDE.md §7 invariants
   ("one transaction cannot be processed twice"); never silently discard a duplicate without
   an audit-visible warning, per CLAUDE.md §10.
3. Follow CLAUDE.md §22 in order and close with §24.
