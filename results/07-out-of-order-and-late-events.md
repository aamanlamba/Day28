# Results — Prompt 07: Out-of-Order and Late Events (CH-07)

**Prompt run:** `prompts/07-out-of-order-and-late-events.md` (unmodified)
**Date:** 2026-09-11
**Requirements:** CH-07 (`docs/15_integrated_engineering_challenges.md` row 7); CMP-FR-003
**Approved plan:** current-state finding, root cause and design were reported in-session and
approved before any code was written.

## 1. Problem Diagnosed

The structuring pattern's window selection depended on delivery order, not event time: with
two non-overlapping qualifying clusters of transactions, which cluster got reported in the
single emitted alert was an artifact of array position, not chronology.

## 2. Current-State Findings

- Checked every pattern in `src/monitoring.py` for order-dependence: velocity already
  explicitly sorted by event time (correct, untouched); corridor and expected-activity are
  filter/sum operations invariant to order by construction; pass-through's exhaustive
  cartesian-product comparison is also order-invariant in its matched-set content (out of
  scope here regardless, per Prompt 11).
- **Structuring was the one real bug:** constructed a scenario with two clusters of 3
  near-threshold credits each, >24h apart. Traced by hand and confirmed with a test that
  delivery order determined which cluster's `transaction_ids` ended up in the single
  `TM_STRUCTURING` alert (`break` after the first qualifying window).
- No existing fixture exposes this — CASE-007 has only 3 transactions in a single 22.5-hour
  cluster, so a single-cluster case is already order-independent by construction (the fix's
  behavior is unchanged for it).
- Did **not** attempt point-in-time KYC-context reconstruction for late events (the other
  half of this challenge's desired outcome) — logged as `BL-009`, since it requires a
  versioned identity-history store that doesn't exist anywhere in this system.

## 3. Root Cause

`near` (the candidate list for the structuring window) was windowed in whatever order `txs`
arrived in, rather than event-time order, so the `break`-selected cluster was positional,
not chronological.

## 4. Architecture / Design Decision

Sort `txs` by event time **once**, immediately after `_dedupe`, before any pattern runs —
a substrate-level fix rather than a per-pattern one. This makes structuring's windowing
deterministic regardless of arrival order, without changing detection policy (still one
alert via `break`, still the same threshold logic) — that policy question belongs to
Prompt 08, which owns the structuring pattern itself. Velocity's existing local sort becomes
a harmless no-op on an already-sorted list; left untouched to keep the diff minimal.

## 5. Files Changed

- `src/monitoring.py` — 3 lines (rename `_dedupe`'s output, add the global sort).
- `tests/test_integrated_compliance.py` — two new tests plus two small helpers.

No files added. No schema, spec, or `/v1` change.

## 6. Implementation Summary

Transactions are now processed by every pattern in event-time order regardless of the order
they were listed in the source file/hook payload. The chronologically-earliest qualifying
structuring cluster is now always the one reported, independent of delivery order.

## 7. Data / Schema Changes

None.

## 8. Tests Added

- `test_structuring_window_is_independent_of_delivery_order` — forward vs. full-reverse of
  a two-cluster batch; asserts identical reported `transaction_ids`. (Passed even before the
  fix for this particular reversal, since a cluster-A element happened to land first in the
  reversed list — kept as a broader invariance check, not the primary gap-proof.)
- `test_structuring_window_handles_late_arriving_events` — cluster A (chronologically
  earliest) delivered *last* in the list; asserts it's still the one reported. **This is the
  test that failed before the fix** (reported cluster B instead), directly demonstrating the
  bug per the prompt's STOP condition 1.
- Both use a shared `_two_cluster_structuring_events`/`_structuring_alert_ids` helper pair,
  reusing **CASE-001**'s real case id (so `build_identity_profile` resolves against real
  fixtures) with only the transactions payload faked via `monkeypatch`.

## 9. Test Results

| Command | Exit | Result |
| --- | --- | --- |
| `test_structuring_window_handles_late_arriving_events` (before fix) | 1 | Failed as expected: reported `{'TB1','TB2','TB3'}` instead of `{'TA1','TA2','TA3'}` |
| `test_structuring_window_is_independent_of_delivery_order` (before fix) | 0 | Already passed for this specific reversal (documented as a coincidence, not evidence the bug didn't exist) |
| Both new tests + `test_structuring_pattern_creates_alert` + `test_velocity_pattern_detected_over_sliding_window` (after fix) | 0 | All 4 passed |
| `pytest -q` (full suite) | 0 | `43 passed, 1 warning in 0.16s` (was 41; +2 new tests, zero regressions) |
| `workshop_preflight.py` | 0 | `PREFLIGHT PASSED` |
| `sanity_check.py` | 0 | `SANITY CHECK PASSED` — counts unchanged |
| `run_integrated_evals.py` | 0 | `{"status": "PASS", "failures": []}` |
| `smoke_server.py` | 0 | `SMOKE SERVER PASSED` |

## 10. Edge Cases Covered

- Out-of-order delivery (full reversal) — covered, per STOP condition 2.
- Late-arriving events (chronologically-earliest cluster delivered last) — covered
  separately, per STOP condition 2's requirement to treat these as distinct cases.
- Existing single-cluster real fixtures (CASE-007, CASE-010) verified unchanged.

Not covered (explicitly deferred): point-in-time KYC-context reconstruction (BL-009);
which/how-many clusters should alert when multiple qualify (Prompt 08's structuring-policy
territory, unchanged by this prompt).

## 11. Security / Privacy Impact

None. Pure sort by an already-validated timestamp field; no new external input surface.

## 12. Observability Added

None new — this is a correctness fix to existing windowing, not a new signal.

## 13. Compatibility Assessment

Fully additive/corrective. `/v1` untouched. `/v2` `MonitoringResult`/`MonitoringAlert`
schemas unchanged. No existing fixture has multiple clusters, so no existing test's expected
output changed — confirmed by the full regression suite (41 pre-existing tests unchanged, 2
new tests added, all green).

## 14. Remaining Risks / Assumptions

- Whether multiple qualifying clusters should each generate their own alert (vs. today's
  single `break`-selected one) is a detection-policy question left to Prompt 08, which owns
  the structuring pattern's actual rule design.
- BL-009 (point-in-time KYC-context reconstruction) remains open — a real architecture gap,
  not addressed here.

## 15. Production-Readiness Verdict

**READY** — the implemented fix is safe, tested, deterministic, and backward-compatible.
No conditions on this specific fix; BL-009 is a separate, larger, already-tracked item.
