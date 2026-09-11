# Results — Prompt 14: Policy / Rule / Model Version Drift (CH-14)

**Prompt run:** `prompts/14-policy-rule-model-version-drift.md` (unmodified)
**Date:** 2026-09-11
**Requirements:** CH-14 (`docs/15_integrated_engineering_challenges.md` row 14); CMP-FR-006
**Approved plan:** the design (new `src/policy.py` module, `MonitoringResult.policy_version`
schema addition, optional replay parameter) was reported in-session and approved before any
code was written.

## 1. Problem Diagnosed

`POLICY_VERSION` was a bare string constant with no connection to the actual threshold
values it was supposedly versioning — a decorative label, not a real version.

## 2. Current-State Findings

- Confirmed `POLICY_VERSION='tm-policy-2026.09-synthetic'` in `src/monitoring.py` had no
  link to `STRUCTURING_*`/`VELOCITY_*`/`PASS_THROUGH_*`/`HIGH_RISK_COUNTRIES` — changing a
  threshold would never force the version string to change, and there was no way to recover
  which threshold values were active for a past decision after a future change.
- Confirmed `config/baseline.json` is read by nothing at runtime (a pre-existing, separately
  documented limitation) and holds unrelated `/v1` settings — retrofitting it for `/v2`
  policy versions would conflate concerns and require inventing JSON encodings for
  `timedelta`/`set` values. Per the prompt's own allowance, used a dedicated Python module
  instead.
- `grep` confirmed only `src/compliance.py` imported `POLICY_VERSION` and only
  `src/monitoring.py`'s `_alert()` read it — a small, fully-traceable migration surface.

## 3. Root Cause

Thresholds and the version tag were never linked — versioning was a label, not a lookup.

## 4. Architecture / Design Decision

- **New module** `src/policy.py`: `POLICY_VERSIONS` — a dict mapping version string to the
  full threshold bundle from Prompts 08–11 (`high_risk_countries` plus every
  `structuring_*`/`velocity_*`/`pass_through_*` value); `CURRENT_POLICY_VERSION` unchanged
  in value so default behavior is identical; `get_policy(version=None)` resolves a bundle or
  raises `UnknownPolicyVersion(ValueError)` (reuses the existing 400 handler).
- `evaluate_transactions(case_id, policy_version=None)` now looks up the policy once and
  every pattern reads thresholds from that bundle instead of module constants.
- **New field** `MonitoringResult.policy_version` — previously only individual alerts
  carried a version, so a zero-alert case had no way to report which policy evaluated it.
- `evaluate_compliance_case(case_id, policy_version=None)` forwards the parameter and reads
  `monitoring.policy_version` instead of importing a constant.
- Both `/v2` evaluate endpoints gained an optional `?policy_version=` query parameter,
  enabling exactly the replay scenario the challenge describes.
- Updated `specs/05_data_contracts/DATA_CONTRACTS.md` (added the missing `MonitoringResult`
  section plus a policy-versioning note), `specs/06_api_contracts/API_CONTRACTS.md` (new
  query param), and `specs/08_traceability/TRACEABILITY_MATRIX.md` (CMP-FR-006 now points at
  `src/policy.py` and its replay test) as living specs.

## 5. Files Changed

- `src/monitoring.py` — refactored to consume `get_policy()`; `_alert()` takes an explicit
  `policy_version` parameter.
- `src/compliance.py` — forwards `policy_version`, drops the stale constant import.
- `src/models_v2.py` — `MonitoringResult.policy_version`.
- `src/app.py` — optional query parameter on both evaluate endpoints.
- `specs/05_data_contracts/DATA_CONTRACTS.md`, `specs/06_api_contracts/API_CONTRACTS.md`,
  `specs/08_traceability/TRACEABILITY_MATRIX.md` — documented additively.

## 6. Files Added

- `src/policy.py` — the versioned policy registry.
- `tests/test_policy.py` — 5 new tests.

No `/v1` change.

## 7. Data / Schema Changes

Additive: `MonitoringResult` gains a required `policy_version` field. Safe because
`MonitoringResult` is only ever constructed by `evaluate_transactions` itself — no external
deserialization of this type exists anywhere in the codebase.

## 8. Tests Added (`tests/test_policy.py`)

- `get_policy()` returns the current version by default.
- `get_policy()` raises `UnknownPolicyVersion` for an unrecognized version.
- `MonitoringResult.policy_version` is populated even for a zero-alert case (CASE-001).
- `ComplianceCaseResult.policy_version` matches `monitoring.policy_version`.
- **The replay test the prompt specifically asks for:**
  `test_replay_reproduces_original_decision_after_policy_changes` — runs CASE-007 today
  (produces a `TM_STRUCTURING` alert under the current policy), `monkeypatch`s in a *new*
  policy version with a stricter structuring threshold and makes it current, confirms the
  default (current-policy) result changes (no more `TM_STRUCTURING`), then explicitly
  re-runs CASE-007 passing the *original* policy version and confirms it reproduces the
  exact original result (`model_dump()` equality) even though "current" has moved on.

## 9. Test Results

| Command | Exit | Result |
| --- | --- | --- |
| `pytest -q` (immediately after the monitoring.py/compliance.py refactor, before new tests) | 0 | `77 passed` — confirms the refactor is fully behavior-preserving for every existing test |
| `pytest -q tests/test_policy.py` | 0 | `5 passed` |
| `pytest -q` (full suite) | 0 | `82 passed, 1 warning in 0.23s` (was 77; +5 new tests, zero regressions) |
| `workshop_preflight.py` | 0 | `PREFLIGHT PASSED` |
| `sanity_check.py` | 0 | `SANITY CHECK PASSED` — counts unchanged |
| `run_integrated_evals.py` | 0 | `{"status": "PASS", "failures": []}` |
| `smoke_server.py` | 0 | `SMOKE SERVER PASSED` |

## 10. Edge Cases Covered

- Unknown policy version requested (controlled 400 via `ValueError` subclass).
- Zero-alert case still reports a policy version.
- The full replay scenario: decision reproducibility across a policy change.

## 11. Security / Privacy Impact

None. No new external input surface beyond an optional, validated version-string lookup; no
new sensitive data exposed.

## 12. Observability Added

Every monitoring/compliance result — including zero-alert cases — now carries a policy
version that is genuinely traceable to a specific, inspectable threshold bundle, and that
bundle can be explicitly re-requested to reproduce a historical decision.

## 13. Compatibility Assessment

Fully additive. `/v1` untouched. Default behavior for every existing case is identical
(same threshold values, same version string) — confirmed by the full regression suite (77
pre-existing tests unchanged, 5 new tests added, all green) run both immediately after the
refactor (before any new tests existed) and again at the end.

## 14. Remaining Risks / Assumptions

- The registry is in-process Python data, not an external/durable config store — consistent
  with this system's existing no-persistence design and within the prompt's explicit
  "smallest coherent mechanism... do not add a database" guidance.
- `config/baseline.json`'s pre-existing non-consumption by `/v1`'s rule engine
  (`docs/known_limitations.md`) was left untouched — out of this challenge's scope, which is
  specifically about `/v2` monitoring policy versioning.
- No new backlog items from this pass.

## 15. Production-Readiness Verdict

**READY** — the implemented mechanism is safe, tested, additive, and backward-compatible,
and directly satisfies the challenge's replay requirement with a passing test. No
conditions.
