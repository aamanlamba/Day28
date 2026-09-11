# Results — Prompt 15: Evals, Observability & Production Readiness (CH-15)

**Prompt run:** `prompts/15-evals-observability-production-readiness.md` (unmodified)
**Date:** 2026-09-11
**Requirements:** CH-15 (`docs/15_integrated_engineering_challenges.md` row 15). This
prompt evaluates the cumulative result of Prompts 00–14 and runs last among the challenge
prompts, immediately before Prompt 16's release pack.
**Approved plan:** the eval/logging/documentation plan was reported in-session and approved
before any file was written.

## 1. Problem Diagnosed

The eval harness (`evals/golden_cases.json` + `scripts/run_integrated_evals.py`) had not
grown alongside the capabilities added in Prompts 01–14: 4 of 12 integrated cases were
uncovered (including CASE-005, actively unit-tested since Prompt 03), no adversarial/
metamorphic/outage-style check existed anywhere in the release-gate layer, no log line
identified which case was decided or why, and the QA report was stale from before this
entire prompt series began.

## 2. Current-State Findings

- `evals/golden_cases.json` covered 8/12 cases with only `expected_disposition`/
  `must_alert`/`must_warn` checks — no `identity_status`/`risk_flags` checking existed at
  this layer at all.
- Confirmed the 82-test pytest suite already covers reordering-invariance, replay,
  idempotency, and authorization edge cases *as unit tests* — but nothing represented these
  at the separate release-gate/eval layer an operator would actually run per
  `WORKSHOP_RUNBOOK.md`.
- Confirmed correlation IDs were already logged for every request, but no log line cited
  which case was decided, its outcome, or why — a real observability gap per CLAUDE.md §18.
- `docs/qa_release_report_integrated.md` reported "Full pytest suite: 32 passed" — stale
  from before Prompts 01–14 ran.

## 3. Root Cause

The eval harness and QA report were built once early in this repo's history and never
extended as new capabilities landed; logging was never extended past the generic
request-level line.

## 4. Architecture / Design Decision

- Restructured `evals/golden_cases.json` under a `"cases"` key (internal fixture, no
  external contract, safe to reshape) and added `expected_identity_status`/
  `must_have_risk_flag` check types.
- Added **CASE-005** (identity `REVIEW` + `CROSS_DOCUMENT_NAME_MISMATCH`) and **CASE-002**
  (no `customer_context` — must not crash, must flag `EXPECTED_ACTIVITY_BASELINE_MISSING`)
  as golden cases, closing real coverage gaps.
- Added three non-golden-case checks to `scripts/run_integrated_evals.py`, each targeting a
  CLAUDE.md §17 category with no prior eval-layer representation: an outage/
  failure-recovery check (unknown case → controlled `FileNotFoundError`, not a crash), a
  metamorphic check (CASE-007 replayed against its own recorded `policy_version` reproduces
  an identical result — re-verifying CH-14's core property at the release-gate layer), and
  an adversarial check (an unauthorized HITL downgrade on CASE-004 is rejected — re-verifying
  CH-13's authorization boundary is active in this build).
- Added decision-level logging in `src/app.py`'s compliance-evaluate and review endpoints:
  `case_id`, `disposition`/decision outcome, `policy_version`, `reason_codes` (evaluate) and
  `decision_id`/`reviewer_id`/`reviewer_role`/prior→new disposition (review) — using the
  existing `log` object, no new framework, no PII (only synthetic IDs and categorical codes).
- Rewrote `docs/qa_release_report_integrated.md` with actual measured results from this run,
  a per-challenge (CH-01..15) coverage summary table, and pointers to every `results/*.md`
  file and open change request/backlog item.

## 5. Files Changed

- `evals/golden_cases.json` — restructured, +2 cases, new check types.
- `scripts/run_integrated_evals.py` — +3 non-golden-case checks.
- `src/app.py` — decision-level logging on 2 endpoints.
- `docs/qa_release_report_integrated.md` — rewritten with measured results.

No files added. No test-suite (`tests/`) changes — this prompt strengthens the eval layer,
which is distinct from and already-covered by the pytest suite.

## 6. Implementation Summary

The release-gate eval script now exercises 10 golden cases (was 8) plus three checks
representing outage, metamorphic, and adversarial categories that previously existed only
as pytest unit tests, not at the release-gate layer. Every compliance decision and review
action now produces an identifiable, reason-bearing log line.

## 7. Data / Schema Changes

None to any Pydantic model. `evals/golden_cases.json`'s internal shape changed (added a
`"cases"` wrapper key) — safe since it has exactly one reader, updated in the same change.

## 8. Tests Added

None in `tests/` — verification for this prompt is the eval script and manual log-output
confirmation (below), consistent with this prompt strengthening the eval/observability
layer rather than the unit-test layer.

## 9. Test Results (measured, per STOP condition 2)

| Command | Exit | Result |
| --- | --- | --- |
| `run_integrated_evals.py` (after golden_cases.json + script changes) | 0 | `{"status": "PASS", "failures": []}` — 10 golden cases + 3 new checks, all passing |
| `pytest -q` (full suite, after eval changes) | 0 | `82 passed` — confirms no interference with existing behavior |
| Manual check: `compliance_case('CASE-004')` invoked directly with logging enabled | — | Confirmed actual log output: `INFO:kyc-v1:compliance_evaluated case_id=CASE-004 disposition=ESCALATE policy_version=tm-policy-2026.09-synthetic reason_codes=IDENTITY_NOT_VERIFIED` |
| `pytest -q` (full suite, after `app.py` logging change) | 0 | `82 passed` |
| `workshop_preflight.py` | 0 | `PREFLIGHT PASSED` |
| `sanity_check.py` | 0 | `SANITY CHECK PASSED` — counts unchanged |
| `run_integrated_evals.py` (final) | 0 | `{"status": "PASS", "failures": []}` |
| `smoke_server.py` | 0 | `SMOKE SERVER PASSED` |

## 10. Edge Cases Covered

- Outage: unknown case ID → controlled failure, not a crash.
- Metamorphic: policy-version replay reproduces an identical result.
- Adversarial: unauthorized HITL state transition is rejected.
- Golden: CASE-002 (missing customer context, must not crash) and CASE-005 (cross-document
  identity conflict) added to the eval layer.

## 11. Security / Privacy Impact

None. New log lines cite only synthetic case IDs, categorical disposition/reason codes, and
self-declared reviewer IDs/roles already accepted by the Prompt 13 endpoints — no raw
identity fields, document content, or new sensitive data.

## 12. Observability Added

Every `/v2` compliance evaluation and review decision now produces a structured,
case-identifiable log line stating the outcome and why — closing the "decision reason" and
"entity id" gaps named in CLAUDE.md §18 that the generic correlation-ID line didn't cover.

## 13. Compatibility Assessment

Fully additive/corrective. `/v1` untouched. No `/v2` API or schema changed — only the
internal eval fixture shape and the eval script that reads it (updated together), plus new
log output (observability, not a contract). Confirmed by the full regression suite (82
tests, unchanged) run at each step of this prompt.

## 14. Remaining Risks / Assumptions

- Per the prompt's explicit out-of-scope guidance, no new metrics/tracing infrastructure
  (Prometheus, OpenTelemetry) was introduced — this remains a synthetic, offline workshop
  repo per `WORKSHOP_RUNBOOK.md` §7, not a live production deployment.
- The eval layer still duplicates some coverage already in pytest (by design — it serves a
  different audience, an operator running the release-gate script, not a developer running
  the test suite).
- All 10 backlog items and both open change requests (CR-001, CR-002) remain open — none
  newly introduced by this prompt, all summarized in the rewritten QA report for visibility.

## 15. Production-Readiness Verdict

**READY WITH CONDITIONS** for the accumulated v1→v2 work across Prompts 00–15:
- **READY:** every one of the 15 engineering challenges has a working, tested, documented
  implementation or an explicitly-scoped, non-blocking deferral; `/v1` compatibility is
  fully preserved (verified by byte-for-byte snapshot tests); the full regression suite (82
  tests), preflight, sanity check, golden+adversarial+metamorphic+outage evals, and smoke
  server are all green as measured in this session.
- **Conditions:** `CR-001` (KYC refresh-date policy) and `CR-002` (real authentication
  behind HITL `reviewer_role`) are real, documented gaps that should be resolved before any
  non-training deployment; `CR-002` in particular means the HITL override endpoint from
  Prompt 13 must not be treated as a real access control today. The 10 open backlog items
  are lower-severity and explicitly non-blocking.

This verdict and its evidence feed directly into Prompt 16's release-evidence pack.
