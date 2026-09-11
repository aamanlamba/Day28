# Results — Prompt 09: Rapid Transaction Velocity (CH-09)

**Prompt run:** `prompts/09-rapid-transaction-velocity.md` (unmodified)
**Date:** 2026-09-11
**Requirements:** CH-09 (`docs/15_integrated_engineering_challenges.md` row 9)
**Approved plan:** current-state finding, root cause and design were reported in-session and
approved before any code was written.

## 1. Problem Diagnosed

Same shape of gap as Prompt 08: velocity detection (5+ events in a 60-minute sliding window)
was already correctly implemented, but its thresholds were inline magic numbers with no
boundary-condition test coverage.

## 2. Current-State Findings

- Confirmed velocity detection already uses a proper forward-looking sliding window
  (`ordered[i:]` on a time-sorted list) — a cleaner design than structuring's
  anchor-symmetric approach — and already benefits from Prompt 07's substrate fix.
- Confirmed `5` and `timedelta(minutes=60)` were inline literals, not named constants.
- Checked whether "many counterparties" (mentioned in the challenge brief) is a separate
  requirement: `docs/compliance_monitoring_patterns.md` and `CMP-FR-004` both describe this
  purely as a count-within-window check with no counterparty-diversity condition. Read the
  change boundary's test suggestion as asking to *verify* the rule is counterparty-agnostic,
  not to add an unspecified new sub-rule — confirmed CASE-010's real fixture already uses 6
  distinct counterparties, and added an explicit contrast test with a single-counterparty
  burst to prove the rule fires either way.
- "Reliable identity linkage prevents burst activity from being split across aliases" —
  already structurally satisfied by Prompt 01's case-id linkage; nothing new needed.

## 3. Root Cause

Same as Prompt 08: correct logic, undocumented magic-number thresholds, untested edges.

## 4. Architecture / Design Decision

Extracted `VELOCITY_MIN_COUNT = 5` and `VELOCITY_WINDOW = timedelta(minutes=60)` as named
module-level constants, same pattern and Prompt-14 deferral note as Prompt 08's structuring
constants. No change to detection semantics.

## 5. Files Changed

- `src/monitoring.py` — 2 named constants added; Pattern 2 references them instead of
  literals.
- `tests/test_integrated_compliance.py` — 4 new tests plus 2 shared helpers, and a comment
  added to the existing CASE-010 test noting its incidental many-counterparties coverage.

No files added. No schema, spec, or `/v1` change.

## 6. Implementation Summary

Velocity's policy values are now named and documented, and every boundary (zero-result,
count, window, counterparty-diversity) now has an explicit, passing test.

## 7. Data / Schema Changes

None.

## 8. Tests Added

- `test_velocity_zero_result_below_count` — 4 events within the window → no alert.
- `test_velocity_count_boundary` — 4 vs. 5 events at the same cadence.
- `test_velocity_window_boundary` — events at 0/15/30/45/60 min → alert (inclusive `<=`);
  shifted so the 5th lands at 61 min → no alert.
- `test_velocity_fires_regardless_of_counterparty_diversity` — 5-event burst on a single
  `counterparty_id` → alert, contrasting with CASE-010's many-counterparties case.
- All via new shared helpers `_velocity_batch`/`_has_velocity_alert`, reusing CASE-001's
  real case id with only the transactions payload faked via `monkeypatch`.

## 9. Test Results

| Command | Exit | Result |
| --- | --- | --- |
| All 5 tests (against pre-refactor code) | 0 | All passed immediately — confirms the existing detection logic was already correct at every edge |
| Same 5 tests (after constant-extraction refactor) | 0 | All passed — confirms the refactor is behavior-preserving |
| `pytest -q` (full suite) | 0 | `51 passed, 1 warning in 0.18s` (was 47; +4 new tests, zero regressions) |
| `workshop_preflight.py` | 0 | `PREFLIGHT PASSED` |
| `sanity_check.py` | 0 | `SANITY CHECK PASSED` — counts unchanged |
| `run_integrated_evals.py` | 0 | `{"status": "PASS", "failures": []}` |
| `smoke_server.py` | 0 | `SMOKE SERVER PASSED` |

## 10. Edge Cases Covered

- Zero-result (below count threshold).
- Count boundary (4 vs. 5).
- Window boundary (exactly 60 min inclusive vs. 61 min).
- Counterparty concentration vs. diversity (rule is agnostic to either).

Not covered (explicitly out of scope per the prompt): monetary-threshold structuring
(Prompt 08, done), pass-through/funnel pairing (Prompt 11).

## 11. Security / Privacy Impact

None. Pure refactor plus additive boundary tests over already-validated fields.

## 12. Observability Added

None new — same as Prompt 08, this is a naming/documentation and test-rigor improvement,
not a new runtime signal.

## 13. Compatibility Assessment

Fully non-breaking. `/v1` untouched. `/v2` schemas and threshold values unchanged.
Confirmed behavior-identical by the full regression suite (47 pre-existing tests unchanged,
4 new tests added, all green).

## 14. Remaining Risks / Assumptions

- Same as Prompt 08: constants remain plain Python module attributes pending Prompt 14's
  versioning mechanism.
- No real fixture sits exactly on a boundary or uses a single concentrated counterparty for
  this pattern; both use synthetic data via `monkeypatch`, consistent with this run.

## 15. Production-Readiness Verdict

**READY** — the implemented change is a safe, fully-tested, behavior-preserving refactor
plus meaningful new boundary coverage. No conditions.
