# Results — Prompt 10: High-Risk Corridor × Identity-Context Fusion (CH-10)

**Prompt run:** `prompts/10-high-risk-corridor-identity-context-fusion.md` (unmodified)
**Date:** 2026-09-11
**Requirements:** CH-10 (`docs/15_integrated_engineering_challenges.md` row 10)
**Approved plan:** current-state finding, root cause and design were reported in-session and
approved before any code was written.

## 1. Problem Diagnosed

Corridor/identity-context fusion already existed but had two gaps against the challenge's
explicit stated inputs: identity confidence wasn't independently fused, and escalation
reasons were one generic sentence regardless of which condition actually fired.

## 2. Current-State Findings

- Confirmed corridor detection and fusion were already real (not a bare geography denylist)
  — `src/monitoring.py` Pattern 3 already escalated severity based on `identity_status`,
  `residency_country`, and `KYC_REFRESH_DUE`. `HIGH_RISK_COUNTRIES` is already a defined
  synthetic set (`{'XQ','ZR'}`), so no change-request needed for an "undefined corridor
  list" per the prompt's stated out-of-scope condition.
- Checked the challenge's exact stated fusion inputs ("residency, nationality, address,
  identity confidence, KYC refresh state, unresolved-document discrepancies") against what
  was wired in: `DOCUMENT_QUALITY_DEGRADED` (Prompt 02's confidence-related flag) was never
  checked.
- **Important nuance found and documented:** in the *real* `/v1` rule engine
  (`src/rules.py`), any document warning forces the document decision to `REVIEW`
  (`if reasons or warnings: return 'REVIEW', ...`), which cascades to
  `identity_status != 'VERIFIED'` — meaning `DOCUMENT_QUALITY_DEGRADED` currently **cannot
  occur through real fixture data** while `identity_status == 'VERIFIED'`; that combination
  only arises from a hand-constructed `IdentityProfile` (as used in this pass's tests, and
  in Prompt 02's design discussion). I judged the new check worth adding anyway, as a
  defense against `monitoring.py` implicitly depending on `rules.py`'s current coupling
  between "has a warning" and "decision is REVIEW" — a coupling that could reasonably change
  in the future (e.g. if a minor warning is later allowed to coexist with APPROVE).
- Confirmed the reason-text gap: `test_high_risk_corridor_is_strengthened_by_identity_context`
  only ever asserted a substring match (`'IDENTITY_CONTEXT' in reason`), never which
  specific condition fired — consistent with the change boundary's explicit ask.

## 3. Root Cause

A single boolean OR across three conditions, with one shared generic reason string, and no
check against Prompt 02's confidence-related flag.

## 4. Architecture / Design Decision

Decomposed the fusion check into four independent, named conditions, each appending its own
specific `IDENTITY_CONTEXT:`-prefixed reason (citing the actual identity field/value) only
when it fires: `identity_status != 'VERIFIED'` (cites the value), `residency_country` in the
high-risk set (cites the country), `KYC_REFRESH_DUE`, and the new
`DOCUMENT_QUALITY_DEGRADED`. Severity still escalates to HIGH if any condition fires
(threshold logic unchanged) — deterministic throughout, no probabilistic component, per
STOP condition 2.

## 5. Files Changed

- `src/monitoring.py` — Pattern 3 restructured as described (12 lines changed/added).
- `tests/test_integrated_compliance.py` — 4 new tests plus 3 shared helpers.

No files added. No schema, spec, or `/v1` change.

## 6. Implementation Summary

Every `TM_HIGH_RISK_CORRIDOR` alert now cites exactly which identity condition(s) drove its
escalation to HIGH, and a case with weak evidence confidence (but an otherwise-VERIFIED
status) now independently escalates corridor severity, closing the "identity confidence"
fusion gap the challenge specifically named.

## 7. Data / Schema Changes

None.

## 8. Tests Added

- `test_corridor_baseline_stays_medium_with_clean_identity` — no escalation conditions →
  `MEDIUM`, no `IDENTITY_CONTEXT` reason (regression guard).
- `test_corridor_escalates_and_cites_identity_status` — isolates `identity_status='REVIEW'`;
  asserts the specific reason text and that no other condition's text appears.
- `test_corridor_escalates_and_cites_kyc_refresh_due` — isolates `KYC_REFRESH_DUE`.
- `test_corridor_escalates_and_cites_document_quality_degraded` — isolates
  `DOCUMENT_QUALITY_DEGRADED` with an otherwise-clean, `VERIFIED` profile — **this is the
  test that failed before the fix** (severity stayed `MEDIUM`), directly demonstrating the
  gap.
- All four use a new `_corridor_alert`/`_clean_identity_profile` helper pair that
  `monkeypatch`es `src.monitoring.build_identity_profile` directly to construct an isolated
  `IdentityProfile`, since the quality-degraded-but-VERIFIED combination isn't reachable
  through the real rule engine (see finding above).

## 9. Test Results

| Command | Exit | Result |
| --- | --- | --- |
| Baseline test (before fix) | 0 | Already passed |
| `identity_status`/`KYC_REFRESH_DUE` reason-text tests (before fix) | 1 | Failed as expected: severity already `HIGH` but specific reason text absent (only the old generic sentence existed) |
| `DOCUMENT_QUALITY_DEGRADED` test (before fix) | 1 | Failed as expected: severity stayed `MEDIUM` — no escalation at all |
| All 4 new tests + existing `test_high_risk_corridor_is_strengthened_by_identity_context` (after fix) | 0 | All 5 passed |
| `pytest -q` (full suite) | 0 | `55 passed, 1 warning in 0.18s` (was 51; +4 new tests, zero regressions) |
| `workshop_preflight.py` | 0 | `PREFLIGHT PASSED` |
| `sanity_check.py` | 0 | `SANITY CHECK PASSED` — counts unchanged |
| `run_integrated_evals.py` | 0 | `{"status": "PASS", "failures": []}` |
| `smoke_server.py` | 0 | `SMOKE SERVER PASSED` |

## 10. Edge Cases Covered

- Clean identity (no escalation) baseline.
- Each of the four escalation conditions isolated independently, confirming no
  cross-contamination of reason text between conditions.
- CASE-008's real, multi-condition (residency + KYC refresh) scenario verified unchanged.

Not covered (explicitly out of scope per the prompt): defining a real-world corridor risk
list (not needed — one already existed); Prompt 12's broader explainability work at the
disposition level (this prompt only addresses alert-level reason granularity for this one
pattern).

## 11. Security / Privacy Impact

None. Reason strings cite already-non-sensitive categorical fields (status enum, country
code, flag names) — no raw document content or PII newly exposed.

## 12. Observability Added

`TM_HIGH_RISK_CORRIDOR` alerts are now independently explainable per triggering condition,
and a previously-invisible fusion input (evidence-quality/confidence) is now load-bearing.

## 13. Compatibility Assessment

Fully additive/corrective. `/v1` untouched. `/v2` `MonitoringAlert.reasons` still a
`list[str]` — content is richer, not restructured. CASE-008's existing substring-based
assertion still holds. Confirmed by the full regression suite (51 pre-existing tests
unchanged, 4 new tests added, all green).

## 14. Remaining Risks / Assumptions

- The `DOCUMENT_QUALITY_DEGRADED` condition is currently unreachable via real fixture data
  (see finding above) — it's correct, tested, and forward-looking defensive logic, but has
  no observable effect on any of the 12 real integrated cases today.
- No new backlog items from this pass — the corridor-list-definition question the prompt
  anticipated turned out not to apply (the list already exists).

## 15. Production-Readiness Verdict

**READY** — the implemented change is safe, tested, deterministic, and backward-compatible.
No conditions.
