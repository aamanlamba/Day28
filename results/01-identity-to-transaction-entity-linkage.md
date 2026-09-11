# Results — Prompt 01: Identity-to-Transaction Entity Linkage (CH-01)

**Prompt run:** `prompts/01-identity-to-transaction-entity-linkage.md` (unmodified)
**Date:** 2026-09-11
**Requirements:** CH-01 (`docs/15_integrated_engineering_challenges.md` row 1); relates to
`specs/02_features/COMPLIANCE_MONITORING.md` intent #1 ("consume synthetic transaction
events keyed to a case/customer identity")
**Approved plan:** current-state finding, root cause and design were reported in-session and
approved before any code was written (per the prompt's own STOP gate and
`CURSOR_WORKFLOW.md` step 3).

## 1. Problem Diagnosed

Every `/v2` function is keyed uniformly by `case_id`, but nothing ever verifies that a
`TransactionEvent`'s own embedded `case_id` field actually agrees with the case it was
loaded under. This is a genuine false-join risk: a misfiled or corrupted event would be
silently trusted and attributed to the wrong case.

## 2. Current-State Findings

- `src/monitoring.py:26-28` (pre-change) loaded `data/transactions/{case_id}.json` and
  constructed `TransactionEvent` objects directly, with no cross-check against the
  `case_id` each event independently carries.
- Confirmed via `grep -rn "case_id" src/*.py` that no such comparison existed anywhere in
  the codebase.
- **Discrepancy found:** `challenges/CH-01.md` cites CASE-005 and CASE-009 as "evidence
  already in repo." Neither fixture actually contains a misaligned identifier —
  `data/transactions/CASE-005.json` is a single clean transaction, and CASE-009's anomaly
  (a duplicated `T901` event) is the CH-06 idempotency scenario, not an identifier-mismatch
  scenario. No existing fixture exercised this gap; a new test was required to prove it
  (see below).
- Document-id-to-case linkage (the other half of CH-01's stated friction) is enforced only
  by a naming convention (`CASE-005-PASSPORT` prefixed with its case id), never validated in
  code, and there is no independent ground-truth field to validate against. This was
  identified but deliberately **not** fixed in this pass (see Remaining Risks).

## 3. Root Cause

The `/v2` layer trusts positional/filename correspondence between the requested `case_id`
and the data loaded for it, instead of validating identifiers embedded in that data.
Alignment held only because the synthetic fixtures happen to be well-formed by construction,
not because the code defends against misalignment.

## 4. Architecture / Design Decision

Added a dedicated filtering step, `_filter_case_mismatch`, in `src/monitoring.py`, run before
`_dedupe` and structured the same way (quarantine + warning code, not a hard failure). A
mismatched event is excluded from processing and recorded via a new `hook_warning` code,
`TRANSACTION_CASE_ID_MISMATCH`, reusing the existing `MonitoringResult.hook_warnings` field
(no schema change). Rejected an alternative of adding a new `CASE-013` fixture file, since
that would also require updating `scripts/sanity_check.py`'s hardcoded case count and
`evals/golden_cases.json` for no added proof value — an in-memory test via `monkeypatch`
gives the same coverage with a smaller blast radius.

## 5. Files Changed

- `src/monitoring.py` — added `_filter_case_mismatch`; `evaluate_transactions` now runs
  loaded events through it before deduplication and merges both warning sets.
- `tests/test_integrated_compliance.py` — added
  `test_transaction_with_mismatched_case_id_is_quarantined`.

No files added. No schema, spec, or `/v1` change.

## 6. Implementation Summary

`evaluate_transactions` now: loads raw events → filters out any whose `case_id` disagrees
with the requested case (recording `TRANSACTION_CASE_ID_MISMATCH`) → deduplicates by
`transaction_id` (existing `DUPLICATE_EVENT_SUPPRESSED` behavior, unchanged) → proceeds to
pattern evaluation exactly as before. `received_transaction_count` still reflects the raw
loaded count (including mismatched events); `processed_transaction_count` reflects the count
after both filters, consistent with the existing duplicate-suppression semantics.

## 7. Data / Schema Changes

None. `hook_warnings: list[str]` already existed on `MonitoringResult`; this adds a new
possible value, not a new field.

## 8. Tests Added

`test_transaction_with_mismatched_case_id_is_quarantined` — constructs (via `monkeypatch` on
`src.monitoring.load_json`) a two-event batch where one event's `case_id` disagrees with the
requested case, and asserts: the warning is present, `received_transaction_count == 2`,
`processed_transaction_count == 1`, and no alert references the quarantined transaction.

## 9. Test Results

| Command | Exit | Result |
| --- | --- | --- |
| `pytest -q tests/test_integrated_compliance.py::test_transaction_with_mismatched_case_id_is_quarantined` (before fix) | 1 | Failed as expected: `assert 'TRANSACTION_CASE_ID_MISMATCH' in []` |
| Same test (after fix) | 0 | Passed |
| `pytest -q` (full suite) | 0 | `33 passed, 1 warning in 0.17s` (was 32; +1 new test, zero regressions) |
| `workshop_preflight.py` | 0 | `PREFLIGHT PASSED` (Python 3.13.15) |
| `sanity_check.py` | 0 | `SANITY CHECK PASSED: 6 legacy cases preserved, 12 integrated cases executable, 19 document artifacts validated, 15 challenge cards present` (unchanged — no fixture files added) |
| `run_integrated_evals.py` | 0 | `{"status": "PASS", "failures": []}` |
| `smoke_server.py` | 0 | `SMOKE SERVER PASSED` |

## 10. Edge Cases Covered

- Mismatched `case_id` on a transaction event (new).
- Mismatch and duplicate-suppression compose correctly (mismatch filter runs first, so a
  mismatched event is never even considered for dedup).
- Existing boundary/pattern behavior (structuring, velocity, corridor, expected-activity,
  pass-through, legitimate duplicate suppression) verified unchanged by the full regression
  run.

Not covered in this pass (explicitly out of scope, see prompt's change boundary): OCR/
document-intelligence confidence propagation (Prompt 02), cross-document name/DOB matching
internals (Prompt 03), document-id-to-case-id linkage validation (see Remaining Risks).

## 11. Security / Privacy Impact

None. The new check compares two already-validated, already-in-memory identifier strings
(`TransactionEvent.case_id` vs. the path parameter); it introduces no new external input
surface, no new logging of sensitive fields (the warning is a fixed code string, not
transaction content), and no new dependency.

## 12. Observability Added

`TRANSACTION_CASE_ID_MISMATCH` is now a visible, audit-traceable warning code on
`MonitoringResult.hook_warnings`, consistent with the existing
`DUPLICATE_EVENT_SUPPRESSED` pattern — a data-integrity problem that was previously
invisible is now surfaced rather than silently absorbed.

## 13. Compatibility Assessment

Fully additive. `/v1` untouched. `/v2` response shape unchanged (reusing an existing list
field). No existing fixture triggers the new warning code, so no existing test's expected
output changed — confirmed by the full regression suite (32 pre-existing tests unchanged,
1 new test added, all green).

## 14. Remaining Risks / Assumptions

- **Document-id-to-case-id linkage is still unvalidated.** It's enforced only by a naming
  convention (`{case_id}-{DOCTYPE}`), never asserted in code, and there's no independent
  ground-truth field to check it against without inventing one. Recommend raising this as a
  change request under `specs/09_change_requests/` if it should be addressed — it would
  likely require a data-model addition (e.g. an explicit `case_id` field on document/
  ground-truth records) rather than a pure code fix.
- This pass addresses the transaction-monitoring half of CH-01 only, per the approved scope;
  `src/identity.py`'s document-evidence linkage was not modified.

## 15. Production-Readiness Verdict

**READY WITH CONDITIONS** — the implemented fix is safe, tested, and backward-compatible.
Condition: the document-id-to-case-id linkage gap noted above should be tracked (change
request or a future prompt) before CH-01 is considered fully closed.
