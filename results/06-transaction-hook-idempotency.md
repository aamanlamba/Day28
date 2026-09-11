# Results — Prompt 06: Transaction-Hook Idempotency (CH-06)

**Prompt run:** `prompts/06-transaction-hook-idempotency.md` (unmodified)
**Date:** 2026-09-11
**Requirements:** CH-06 (`docs/15_integrated_engineering_challenges.md` row 6); CMP-FR-002
**Approved plan:** current-state finding, root cause and design were reported in-session and
approved before any code was written. This is the first transaction/monitoring-side prompt
(06–11), building on the identity-side foundation from Prompts 00–05.

## 1. Problem Diagnosed

`_dedupe` treated any repeated `transaction_id` as an ordinary duplicate and silently
dropped it, without checking whether its content actually matched the first occurrence — so
a **conflicting** redelivery (same ID, different `amount`/fields — a genuine data-integrity
signal) was indistinguishable from routine exact-duplicate noise.

## 2. Current-State Findings

- Confirmed dedup logic was already implemented and tested (`_dedupe`, added prior to this
  run) — `DUPLICATE_EVENT_SUPPRESSED` correctly suppresses exact duplicates, verified against
  CASE-009's real fixture (its `T901` duplicate is byte-identical across both occurrences).
- Checked for latent non-determinism per CLAUDE.md §7 ("historical decisions must remain
  reproducible"): no use of `datetime.now()` or any other non-deterministic source anywhere
  in `src/monitoring.py` — the architecture is fully stateless (recomputes from `data/*.json`
  on every call, no persistence, no caching). Calling `evaluate_transactions` twice was
  already trivially deterministic; added an explicit test to codify this as a guard against
  future regression (e.g. someone adding a cache or a real-time field later).
- **The real gap:** no code path distinguished an exact duplicate from a conflicting one.
  Both produced the identical `DUPLICATE_EVENT_SUPPRESSED` warning, so an analyst had no way
  to tell "harmless redelivery" from "someone reused a transaction ID with different
  content" — the latter is explicitly one of CLAUDE.md §9's required edge cases
  ("conflicting information"), distinct from "duplicate events."

## 3. Root Cause

`_dedupe` keyed on `transaction_id` alone via a `set`, never comparing the content of a
repeated event against what was first seen under that ID.

## 4. Architecture / Design Decision

Changed `_dedupe`'s internal tracking from a `set` of seen IDs to a `dict` mapping
`transaction_id -> first-seen event`. On a repeat ID, full equality is compared (pydantic
models compare field-by-field by default): if equal, the existing `DUPLICATE_EVENT_SUPPRESSED`
warning is unchanged; if not, a new `CONFLICTING_DUPLICATE_TRANSACTION` warning fires
instead. Either way the event is still excluded from processing — never double-counted —
this only makes the *reason* more specific.

## 5. Files Changed

- `src/monitoring.py` — `_dedupe` rewritten as described above (7 lines changed/added).
- `tests/test_integrated_compliance.py` — two new tests.

No files added. No schema, spec, or `/v1` change.

## 6. Implementation Summary

A repeated `transaction_id` with matching content is still suppressed exactly as before. A
repeated `transaction_id` with *different* content is now suppressed but flagged distinctly
as `CONFLICTING_DUPLICATE_TRANSACTION`, never both codes for the same event.

## 7. Data / Schema Changes

None. `hook_warnings: list[str]` already existed; this adds a new possible value.

## 8. Tests Added

- `test_conflicting_duplicate_transaction_id_is_distinguished_from_true_duplicate` —
  synthetic batch (via `monkeypatch` on `src.monitoring.load_json`) with two `T901` events
  differing only in `amount`; asserts the new warning fires, the old one does not, and the
  conflicting event is excluded from `processed_transaction_count`.
- `test_evaluate_transactions_is_replayable` — calls `evaluate_transactions('CASE-007')`
  twice and asserts identical `model_dump()` output — codifies the existing determinism
  guarantee as an explicit regression guard.

## 9. Test Results

| Command | Exit | Result |
| --- | --- | --- |
| Conflicting-duplicate test (before fix) | 1 | Failed as expected: `CONFLICTING_DUPLICATE_TRANSACTION` absent, only `DUPLICATE_EVENT_SUPPRESSED` present |
| Replayability test (before fix) | 0 | Already passed — confirms determinism already held |
| Both new tests + existing `test_duplicate_transaction_hook_is_idempotently_suppressed` (after fix) | 0 | All 3 passed — confirms CASE-009's real duplicate behavior is unchanged |
| `pytest -q` (full suite) | 0 | `41 passed, 1 warning in 0.17s` (was 39; +2 new tests, zero regressions) |
| `workshop_preflight.py` | 0 | `PREFLIGHT PASSED` |
| `sanity_check.py` | 0 | `SANITY CHECK PASSED` — counts unchanged |
| `run_integrated_evals.py` | 0 | `{"status": "PASS", "failures": []}` |
| `smoke_server.py` | 0 | `SMOKE SERVER PASSED` |

## 10. Edge Cases Covered

- Exact duplicate (existing, CASE-009, unchanged).
- Conflicting duplicate — same ID, different content (new).
- Repeat invocation determinism/replayability (new, explicit guard).

Not covered (architectural limitation, not a gap to fix here): true redelivery *over time*
via separate API calls — the system has no persistence layer at all, so every call
independently reloads and reprocesses the same file; there is no queue/broker to actually
redeliver anything. This was already noted in Prompt 01's results and remains accurate.

## 11. Security / Privacy Impact

None. Pure in-memory equality comparison of already-validated fields; no new external input
surface, no new logging of sensitive content — a fixed warning-code string.

## 12. Observability Added

`CONFLICTING_DUPLICATE_TRANSACTION` is a new, distinct, audit-traceable warning — a
genuinely more serious condition (potential data-integrity or fraud signal) is no longer
indistinguishable from routine duplicate-delivery noise.

## 13. Compatibility Assessment

Fully additive. `/v1` untouched. `/v2` `MonitoringResult` schema unchanged (reusing
`hook_warnings`). CASE-009's existing exact-duplicate behavior is verified unchanged by the
full regression suite (39 pre-existing tests unchanged, 2 new tests added, all green).

## 14. Remaining Risks / Assumptions

- No real fixture currently exercises a conflicting duplicate — same limitation pattern as
  several prior prompts (synthetic test only). Low risk given the logic is a direct,
  narrow equality check.
- The stateless, no-persistence architecture means true cross-call redelivery idempotency
  remains structurally untestable without a larger architecture change — out of scope for a
  "smallest safe change" prompt; noted, not treated as a defect of this specific prompt.

## 15. Production-Readiness Verdict

**READY** — the implemented fix is safe, tested, additive, and backward-compatible, and
closes the concrete gap this prompt targeted without requiring any deferred policy decision.
