# Results — Prompt 11: Pass-Through / Funnel-Account Behaviour (CH-11)

**Prompt run:** `prompts/11-pass-through-funnel-account-behaviour.md` (unmodified)
**Date:** 2026-09-11
**Requirements:** CH-11 (`docs/15_integrated_engineering_challenges.md` row 11)
**Approved plan:** current-state finding, root cause and design were reported in-session and
approved before any code was written. This closes out the transaction/monitoring-side
prompts (06–11).

## 1. Problem Diagnosed

Same shape of gap as Prompts 08/09: pass-through detection (credit matched by a near-equal
debit within 6h) was already correctly implemented, but its thresholds were inline magic
numbers with no boundary-condition test coverage.

## 2. Current-State Findings

- Confirmed the pattern already pairs every CREDIT against every DEBIT on amount similarity
  (≤8%), time proximity (0–6h), and a minimum credit amount (≥5000), alerting at ≥2 matched
  pairs. CASE-012's real fixture demonstrates exactly two such pairs to two different
  counterparties.
- Confirmed `timedelta(hours=6)`, `.08`, `5000`, `4` were inline literals, not named
  constants.
- Checked whether "dispersal to multiple beneficiaries" (mentioned in
  `docs/15_integrated_engineering_challenges.md` row 11) means genuine fan-out — one credit
  split across several smaller debits. It doesn't exist: the tolerance check compares each
  debit directly against the *full* credit amount, so a split credit's partial debits would
  never individually match. What's implemented and working is multiple *separate* 1:1
  funnel pairs (which already naturally supports different counterparties per pair, as
  CASE-012 shows) — a related but distinct capability. Logged as `BL-010` rather than
  building fan-out detection, since it needs new policy (a sum-tolerance across N debits, a
  minimum dispersal count) with no spec backing.

## 3. Root Cause

Same as Prompts 08/09: correct logic, undocumented magic-number thresholds, untested edges.

## 4. Architecture / Design Decision

Extracted `PASS_THROUGH_WINDOW`, `PASS_THROUGH_AMOUNT_TOLERANCE`,
`PASS_THROUGH_MIN_CREDIT_AMOUNT`, `PASS_THROUGH_MIN_MATCHED_COUNT` as named module-level
constants, same pattern and Prompt-14 deferral note as Prompts 08/09. No change to detection
semantics.

## 5. Files Changed

- `src/monitoring.py` — 4 named constants added; Pattern 5 references them instead of
  literals.
- `tests/test_integrated_compliance.py` — 5 new tests plus 2 shared helpers.

No files added. No schema, spec, or `/v1` change.

## 6. Implementation Summary

Pass-through's policy values are now named and documented, and every boundary (zero-result,
count, amount-tolerance, window, minimum-credit-amount) now has an explicit, passing test.

## 7. Data / Schema Changes

None.

## 8. Tests Added

- `test_pass_through_zero_result_no_matching_debit` — a qualifying credit with no matching
  debit at all → no alert.
- `test_pass_through_count_boundary` — 1 qualifying pair → no alert; 2 → alert.
- `test_pass_through_amount_tolerance_boundary` — a control pair plus a second pair at
  exactly 8% deviation → alert; at 8.01% → no alert.
- `test_pass_through_window_boundary` — control pair plus a second pair's debit at exactly
  6h → alert; at 6h01m → no alert.
- `test_pass_through_min_credit_amount_boundary` — control pair plus a second pair's credit
  at exactly 5000 → alert; at 4999 → no alert.
- All via new shared helpers `_pass_through_pairs`/`_has_pass_through_alert`, each pair
  placed a full day apart to prevent cross-pair matching, reusing CASE-001's real case id
  with only the transactions payload faked via `monkeypatch`.

## 9. Test Results

| Command | Exit | Result |
| --- | --- | --- |
| All 5 tests (against pre-refactor code) | 0 | All passed immediately — confirms the existing detection logic was already correct at every edge |
| Same 5 tests + `test_pass_through_pattern_detected` (after constant-extraction refactor) | 0 | All 6 passed |
| `pytest -q` (full suite) | 0 | `60 passed, 1 warning in 0.20s` (was 55; +5 new tests, zero regressions) |
| `workshop_preflight.py` | 0 | `PREFLIGHT PASSED` |
| `sanity_check.py` | 0 | `SANITY CHECK PASSED` — counts unchanged |
| `run_integrated_evals.py` | 0 | `{"status": "PASS", "failures": []}` |
| `smoke_server.py` | 0 | `SMOKE SERVER PASSED` |

## 10. Edge Cases Covered

- Zero-result (no matching debit).
- Count boundary (1 vs. 2 pairs).
- Amount-tolerance boundary (8% inclusive vs. 8.01%).
- Window boundary (6h inclusive vs. 6h01m).
- Minimum-credit-amount boundary (5000 inclusive vs. 4999).

Not covered (explicitly deferred to `BL-010`): genuine fan-out/dispersal detection.

## 11. Security / Privacy Impact

None. Pure refactor plus additive boundary tests over already-validated numeric fields.

## 12. Observability Added

None new — naming/documentation and test-rigor improvement, consistent with Prompts 08/09.

## 13. Compatibility Assessment

Fully non-breaking. `/v1` untouched. `/v2` schemas and threshold values unchanged. Confirmed
behavior-identical by the full regression suite (55 pre-existing tests unchanged, 5 new
tests added, all green).

## 14. Remaining Risks / Assumptions

- Constants remain plain Python module attributes pending Prompt 14's versioning mechanism.
- `BL-010` (fan-out/dispersal detection) remains open — a real capability gap relative to
  the challenge's descriptive text, not addressed here pending a policy decision.

## 15. Production-Readiness Verdict

**READY** — the implemented change is a safe, fully-tested, behavior-preserving refactor
plus meaningful new boundary coverage. No conditions on this specific change; `BL-010` is a
separate, already-tracked item.

---

**This closes out Prompts 06–11 (transaction/monitoring-side).** All six monitoring
patterns (idempotency, temporal ordering, structuring, velocity, corridor fusion,
pass-through) are now implemented, boundary-tested, and have their thresholds named.
Prompts 12–15 (cross-cutting governance: explainability, HITL, versioning, evals) are next.
