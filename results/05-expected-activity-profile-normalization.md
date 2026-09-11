# Results — Prompt 05: Expected-Activity Profile Normalization (CH-05)

**Prompt run:** `prompts/05-expected-activity-profile-normalization.md` (unmodified)
**Date:** 2026-09-11
**Requirements:** CH-05 (`docs/15_integrated_engineering_challenges.md` row 5)
**Approved plan:** current-state finding, root cause and design were reported in-session and
approved before any code was written.

## 1. Problem Diagnosed

A missing expected-activity baseline (`expected_monthly_turnover is None`) silently disables
`src/monitoring.py`'s `TM_EXPECTED_ACTIVITY_DEVIATION` pattern with no visible signal that
this happened.

## 2. Current-State Findings

- Confirmed `src/identity.py` does pure passthrough of `occupation`/`expected_monthly_turnover`
  from `data/customer_context/*.json` — no normalization logic exists.
- Confirmed CH-05's core friction (messy free text needing normalization) **does not occur**
  in this synthetic dataset: every `occupation` value is already a clean short string, every
  `expected_monthly_turnover` is already a clean number. This is a genuine finding — the
  challenge is bypassed by the data shape, not solved by any logic, and no amount of code
  change here would create a normalization problem that doesn't exist in the fixtures.
- `expected_monthly_turnover` is consumed by exactly one thing:
  `src/monitoring.py`'s `TM_EXPECTED_ACTIVITY_DEVIATION` pattern. Confirmed **CASE-002,
  CASE-003, CASE-006** have no `customer_context` file at all (they're `/v1`-legacy-only
  cases), so `build_identity_profile` on any of them yields `expected_monthly_turnover=None`
  with no prior visible signal.
- `occupation` is captured on `IdentityProfile` but confirmed via `grep` across
  `src/monitoring.py` and `src/compliance.py` to be consumed by **nothing** — logged as
  BL-007, not fixed here (would require an unrequested occupation-to-risk taxonomy).
- The change boundary's suggested "expected-counterparty-country set" field was considered
  and deliberately not built — it has no spec backing, no consumer yet (belongs to Prompts
  09/10), and speculatively guessing its shape risks a design that doesn't fit its actual
  future consumer. Logged as BL-008.

## 3. Root Cause

`IdentityProfile` construction never distinguished "no baseline exists" from "baseline
exists and is unremarkable" — both looked identical (field absent from the response, silent
non-firing of the one pattern that depends on it).

## 4. Architecture / Design Decision

In `src/identity.py`: when `ctx.get('expected_monthly_turnover')` is `None`, append a new,
purely informational risk flag `EXPECTED_ACTIVITY_BASELINE_MISSING`. Does not change
`identity_status` or `confidence` (no policy invented about how serious a missing baseline
is) and does not touch `src/monitoring.py` (staying out of Prompts 09/10's territory).

## 5. Files Changed

- `src/identity.py` — captured `expected_turnover` in a local variable, added the missing-
  baseline flag, reused the local variable when constructing `IdentityProfile`.
- `tests/test_integrated_compliance.py` — one new test.

No files added. No schema, spec, or `/v1` change.

## 6. Implementation Summary

`build_identity_profile` now flags `EXPECTED_ACTIVITY_BASELINE_MISSING` whenever a case has
no expected-turnover data, making a previously silent gap visible on the identity profile
itself.

## 7. Data / Schema Changes

None.

## 8. Tests Added

`test_missing_expected_activity_baseline_is_flagged_not_silent` — uses **CASE-002** directly
(a real fixture with no `customer_context` file, no `monkeypatch` needed); asserts
`expected_monthly_turnover is None` and the new flag is present.

## 9. Test Results

| Command | Exit | Result |
| --- | --- | --- |
| New test (before fix) | 1 | Failed as expected: flag absent (confirmed Prompt 02's `DOCUMENT_QUALITY_DEGRADED` flag already correctly fires on this same case) |
| New test (after fix) | 0 | Passed |
| `pytest -q` (full suite) | 0 | `39 passed, 1 warning in 0.19s` (was 38; +1 new test, zero regressions) |
| `workshop_preflight.py` | 0 | `PREFLIGHT PASSED` |
| `sanity_check.py` | 0 | `SANITY CHECK PASSED` — counts unchanged |
| `run_integrated_evals.py` | 0 | `{"status": "PASS", "failures": []}` |
| `smoke_server.py` | 0 | `SMOKE SERVER PASSED` |

## 10. Edge Cases Covered

- Case with no `customer_context` file at all (real fixture, CASE-002).
- Confirmed via the full regression run that the flag doesn't appear for any of the 9 cases
  that do have `expected_monthly_turnover` set, and doesn't interfere with the existing
  `test_expected_activity_deviation_uses_kyc_profile` (CASE-011) test.

Not covered (explicitly deferred to backlog): occupation-based risk categorization (BL-007),
expected-counterparty-country baseline (BL-008).

## 11. Security / Privacy Impact

None. No new external input, no new logging of sensitive content — a fixed flag string.

## 12. Observability Added

`EXPECTED_ACTIVITY_BASELINE_MISSING` makes a previously silent monitoring-capability gap
(a pattern that simply never fires) visible and traceable on the identity profile.

## 13. Compatibility Assessment

Fully additive. `/v1` untouched. `/v2` `IdentityProfile` schema unchanged (reusing
`risk_flags`). No existing test asserts an exhaustive flag list, so no existing test's
expectations changed — confirmed by the full regression suite.

## 14. Remaining Risks / Assumptions

- CH-05's core "normalize messy free text" problem remains unsolved because it doesn't
  exist in the current synthetic dataset — this is a data-fixture limitation, not a code
  gap, and no code change can meaningfully close it without messier synthetic input data to
  normalize.
- BL-007 (occupation unused) and BL-008 (counterparty-country baseline) both logged, neither
  blocking.

## 15. Production-Readiness Verdict

**READY WITH CONDITIONS** — the implemented fix is safe, tested, and backward-compatible.
Conditions: BL-007 and BL-008 represent real design/policy decisions for later prompts or a
change request; CH-05's deeper normalization problem is a data-fixture gap worth noting for
Prompt 15's eval-hardening work.
