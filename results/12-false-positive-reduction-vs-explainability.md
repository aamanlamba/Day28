# Results — Prompt 12: False-Positive Reduction vs Explainability (CH-12)

**Prompt run:** `prompts/12-false-positive-reduction-vs-explainability.md` (unmodified)
**Date:** 2026-09-11
**Requirements:** CH-12 (`docs/15_integrated_engineering_challenges.md` row 12)
**Approved plan:** the audit findings and proposed fixes were reported in-session and
approved before any code was written. This is the first of the cross-cutting governance
prompts (12–15).

## 1. Problem Diagnosed

Four of five monitoring patterns justified their alerts with a static rule-description
string instead of the actual observed values for that specific instance, and the
disposition layer never named which pattern(s) actually drove an escalation.

## 2. Current-State Findings — audit of every pattern

| Pattern | `transaction_ids` / `evidence_refs` | `reasons` (before this pass) |
| --- | --- | --- |
| 1 Structuring | Already specific | Static: `'3+ credits between 8,000 and 9,999 within 24h'` — **generic** |
| 2 Velocity | Already specific | Static: `'5+ transactions...'` — **generic** |
| 3 Corridor | Already specific | Base reason static: `'...in synthetic high-risk corridor set'` — **generic** (the `IDENTITY_CONTEXT` reasons from Prompt 10 were already specific) |
| 4 Expected-activity | Already specific | Already interpolates actual observed/expected values — **no fix needed**, used as the reference shape |
| 5 Pass-through | Already specific | Static: `'multiple large credits...'` — **generic** |

`transaction_ids` and `evidence_refs` were already fully specific on every alert via
`_alert()`'s construction from the actual matched transactions and the identity's evidence
refs — no gap there on this axis.

Also audited `src/compliance.py`'s disposition-level `reason_codes` per the prompt's
grounding list: `TRANSACTION_MONITORING_HIGH_RISK`/`_MEDIUM_RISK` never named which
`pattern_code`(s) actually fired — matching gap #10 already identified in Prompt 00's
ranked findings.

## 3. Root Cause

Four patterns were written with a static rule-description string instead of interpolating
values already in scope (`len(window)`, matched countries, matched pair count). The
disposition layer never cross-referenced `monitoring.alerts` when citing an escalation.

## 4. Architecture / Design Decision

Per pattern, replaced the static string with one that interpolates the real observed values
alongside the existing rule-description context — no trigger condition changed anywhere. In
`compliance.py`, added `TRIGGERING_PATTERN:{code}` reasons (one per distinct pattern code
present in `monitoring.alerts`) whenever a transaction-monitoring escalation fires.

## 5. Files Changed

- `src/monitoring.py` — reason text in Patterns 1, 2, 3, 5 (Pattern 4 untouched, already
  correct).
- `src/compliance.py` — cites triggering pattern codes on escalation.
- `tests/test_integrated_compliance.py` — 6 new tests (one per pattern plus one for
  compliance-level citation).

No files added. No schema, spec, or `/v1` change.

## 6. Implementation Summary

Every alert's `reasons` now states the actual count/values observed for that specific
instance (e.g. "3 credits between 8000 and 9999... (rule threshold: 3+)" instead of
"3+ credits..."), and every `ComplianceCaseResult.reason_codes` escalation now names exactly
which monitoring pattern(s) triggered it.

## 7. Data / Schema Changes

None. `reasons`/`reason_codes` already `list[str]`; content is richer, not restructured.

## 8. Tests Added

- `test_structuring_reason_cites_actual_observed_count` (CASE-007, expects "3 credits").
- `test_corridor_base_reason_cites_actual_countries_matched` (CASE-008, expects both "XQ"
  and "ZR" named).
- `test_compliance_reason_codes_cite_triggering_pattern` (CASE-008, expects
  `TM_HIGH_RISK_CORRIDOR` in `reason_codes`).
- `test_velocity_reason_cites_actual_observed_count` (CASE-010, expects "6 transactions").
- `test_pass_through_reason_cites_actual_pair_count` (CASE-012, expects "2 credit/debit
  pair").
- All use real fixtures directly (CASE-007/008/010/012) — no synthetic data needed, since
  each already has a known, fixed observed count to assert against.

## 9. Test Results

| Command | Exit | Result |
| --- | --- | --- |
| All 5 new tests (4 pattern-level + 1 disposition-level) (before fix) | 1 | Failed as expected — confirmed each pattern's reason text was static/generic, and the disposition never cited a pattern code |
| Same 5 new tests + 5 pre-existing pattern tests (after fix) | 0 | All 10 passed |
| `pytest -q` (full suite) | 0 | `65 passed, 1 warning in 0.19s` (was 60; +5 new tests, zero regressions) |
| `workshop_preflight.py` | 0 | `PREFLIGHT PASSED` |
| `sanity_check.py` | 0 | `SANITY CHECK PASSED` — counts unchanged |
| `run_integrated_evals.py` | 0 | `{"status": "PASS", "failures": []}` |
| `smoke_server.py` | 0 | `SMOKE SERVER PASSED` |

## 10. Edge Cases Covered

- One test per pattern rule, per the change boundary's explicit requirement.
- Disposition-level citation verified against a real multi-condition case (CASE-008).

Not covered (explicitly out of scope per the prompt): adding new detection patterns or
changing any trigger condition — verified no threshold/logic changed, only reason text.

## 11. Security / Privacy Impact

None. All interpolated values are already-non-sensitive categorical/numeric fields (counts,
country codes, amounts already present in the transaction data) — no new PII exposure.

## 12. Observability Added

Every alert and every escalation reason is now self-explanatory from its own text, directly
serving this challenge's stated outcome: "an investigator can reconstruct why it fired
without reading source code."

## 13. Compatibility Assessment

Fully additive/corrective. `/v1` untouched. `/v2` schemas unchanged (`reasons`/
`reason_codes` remain `list[str]`). No existing test asserted exact reason-string content
(confirmed by `grep` before starting) — all existing tests use substring/membership checks,
so no existing test broke. Confirmed by the full regression suite.

## 14. Remaining Risks / Assumptions

- Pattern 4 (expected-activity) was already correct and used as the reference shape for the
  other four — no changes made there.
- No new backlog items from this pass — this was a self-contained explainability audit and
  fix with no deferred policy questions.

## 15. Production-Readiness Verdict

**READY** — the implemented changes are safe, tested, additive, and backward-compatible.
No conditions.
