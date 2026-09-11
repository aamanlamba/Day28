# Results — Prompt 08: Structuring / Threshold-Avoidance Detection (CH-08)

**Prompt run:** `prompts/08-structuring-threshold-avoidance.md` (unmodified)
**Date:** 2026-09-11
**Requirements:** CH-08 (`docs/15_integrated_engineering_challenges.md` row 8)
**Approved plan:** current-state finding, root cause and design were reported in-session and
approved before any code was written.

## 1. Problem Diagnosed

The structuring pattern's thresholds were inline magic numbers with no boundary-condition
test coverage — not a logic defect (the detection was already correct), but a hygiene and
verification gap per this prompt's explicit asks.

## 2. Current-State Findings

- Confirmed the structuring pattern (3+ CREDIT transactions in `[8000, 10000)` within a
  24h window, order-independent since Prompt 07) is already correctly implemented and
  passes its one existing test (CASE-007).
- Confirmed via `grep`/inspection that `8000`, `10000`, `3`, and `timedelta(hours=24)` were
  inline literals, not named constants — unlike `HIGH_RISK_COUNTRIES`, which already follows
  the named-constant pattern.
- Confirmed **zero** existing tests exercised the boundary — CASE-007's amounts (9200,
  9400, 9600) and Prompt 07's synthetic tests (9000) all sit solidly mid-range.
- Checked `src/rules.py` for a shared/duplicated threshold per the grounding note: none
  exists — `/v1` has no transaction-amount logic at all. No reuse conflict.
- Confirmed the "verified ownership/linked-account identity" precondition this challenge
  calls for is already satisfied by Prompt 01's case-id-mismatch filtering, which runs
  before this pattern.

## 3. Root Cause

The pattern's logic was correct but untested at its edges, and its thresholds were
undocumented magic numbers rather than named, externally-visible constants.

## 4. Architecture / Design Decision

Extracted `STRUCTURING_MIN_AMOUNT`, `STRUCTURING_MAX_AMOUNT`, `STRUCTURING_MIN_COUNT`,
`STRUCTURING_WINDOW` as named module-level constants in `src/monitoring.py`, alongside the
existing `POLICY_VERSION`/`HIGH_RISK_COUNTRIES` pattern, with a comment explicitly flagging
that Prompt 14's general versioning mechanism should formalize these into a real versioned
policy source. **No change to the actual threshold values or detection semantics** — pure
naming/documentation refactor, verified behavior-preserving by the full regression suite.

## 5. Files Changed

- `src/monitoring.py` — 4 named constants added; Pattern 1 references them instead of
  literals.
- `tests/test_integrated_compliance.py` — 4 new boundary tests plus 2 shared helpers.

No files added. No schema, spec, or `/v1` change.

## 6. Implementation Summary

Structuring's policy values are now named and documented at the top of the module instead
of buried as inline literals in a boolean expression, and every boundary (count, both amount
edges, window edge) now has an explicit, passing test.

## 7. Data / Schema Changes

None.

## 8. Tests Added

- `test_structuring_count_boundary` — 2 near-threshold transactions → no alert; 3 → alert.
- `test_structuring_amount_lower_boundary` — `7999` × 3 → no alert; `8000` × 3 → alert
  (inclusive lower bound).
- `test_structuring_amount_upper_boundary` — `9999` × 3 → alert; `10000` × 3 → no alert
  (exclusive upper bound).
- `test_structuring_window_boundary` — transactions at 0h/12h/24h → alert (inclusive `<=`
  window); transactions each ~24h01m apart (no single 24h window covers all three from any
  anchor) → no alert.
- All four use new shared helpers `_structuring_batch`/`_has_structuring_alert`, reusing
  **CASE-001**'s real case id with only the transactions payload faked via `monkeypatch`.

## 9. Test Results

| Command | Exit | Result |
| --- | --- | --- |
| All 4 boundary tests (against pre-refactor code) | 0 | All passed immediately — confirms the existing detection logic was already correct at every edge before any change |
| Same 4 tests + `test_structuring_pattern_creates_alert` (after constant-extraction refactor) | 0 | All 5 passed — confirms the refactor is behavior-preserving |
| `pytest -q` (full suite) | 0 | `47 passed, 1 warning in 0.17s` (was 43; +4 new tests, zero regressions) |
| `workshop_preflight.py` | 0 | `PREFLIGHT PASSED` |
| `sanity_check.py` | 0 | `SANITY CHECK PASSED` — counts unchanged |
| `run_integrated_evals.py` | 0 | `{"status": "PASS", "failures": []}` |
| `smoke_server.py` | 0 | `SMOKE SERVER PASSED` |

## 10. Edge Cases Covered

- Count boundary (2 vs. 3 transactions).
- Amount lower boundary (7999 vs. 8000, inclusive).
- Amount upper boundary (9999 vs. 10000, exclusive).
- Window boundary (exactly 24h inclusive vs. spread beyond it).

Not covered (explicitly out of scope per the prompt): velocity/frequency-only detection
(Prompt 09), pass-through/funnel patterns (Prompt 11).

## 11. Security / Privacy Impact

None. Pure refactor plus additive boundary tests over already-validated numeric fields.

## 12. Observability Added

None new — the constants are now named/documented, which aids future maintainers reading
the code, but doesn't change runtime behavior or add a new signal.

## 13. Compatibility Assessment

Fully non-breaking. `/v1` untouched. `/v2` schemas and threshold *values* unchanged — only
their representation in code changed from literals to named constants. Confirmed
behavior-identical by the full regression suite (43 pre-existing tests unchanged, 4 new
tests added, all green).

## 14. Remaining Risks / Assumptions

- The constants are still plain Python module attributes, not yet sourced from
  `config/baseline.json` or stamped with a version history — intentionally deferred to
  Prompt 14 per this prompt's own instructions.
- No real fixture sits exactly on a boundary; all boundary tests use synthetic data via
  `monkeypatch`, consistent with this run's established pattern.

## 15. Production-Readiness Verdict

**READY** — the implemented change is a safe, fully-tested, behavior-preserving refactor
plus meaningful new boundary coverage. No conditions; Prompt 14 remains the natural home for
actually externalizing/versioning these constants.
