# Results — Prompt 16: Release / v2 Evidence Pack (wrap-up)

**Prompt run:** `prompts/16-release-v2-evidence-pack.md` (unmodified)
**Date:** 2026-09-11
**Purpose:** close out the 15-challenge prompt series; this prompt introduces no new
engineering transformation, only evidence and versioning, per its own STOP condition 3.

## 1. Full regression + preflight (Task 1)

Re-run at release time, not cited from earlier prompts:

| Command | Exit | Output |
| --- | --- | --- |
| `workshop_preflight.py` | 0 | `PREFLIGHT PASSED` (Python 3.13.15) |
| `sanity_check.py` | 0 | `SANITY CHECK PASSED: 6 legacy cases preserved, 12 integrated cases executable, 19 document artifacts validated, 15 challenge cards present` |
| `pytest -q` | 0 | `82 passed, 1 warning in 0.16s` |
| `smoke_server.py` | 0 | `SMOKE SERVER PASSED` |
| `run_integrated_evals.py` | 0 | `{"status": "PASS", "failures": []}` |

No failure occurred; no classification needed.

## 2. Rollback and backward-compatibility demonstration (Task 2)

**`/v1` unchanged**, live-checked via `TestClient`:
```
GET /v1/cases -> 200, 6 cases
POST /v1/documents/verify {CASE-001-PASSPORT} -> 200, decision=APPROVE
POST /v1/cases/CASE-005/verify -> 200, decision=APPROVE
```
CASE-005 still `APPROVE`s on `/v1` — the intentionally-preserved brownfield gap
(`test_name_variation_exposes_brownfield_gap`) — confirming `/v2`'s hardened identity
resolution (Prompts 02–03) never touched `/v1` behavior.

**Representative change reverted via policy version, no code rollback** (Prompt 14's
mechanism, chosen as the representative change since it's the general-purpose rollback
tool this series built):
```
Baseline: CASE-007 under tm-policy-2026.09-synthetic -> alerts=['TM_STRUCTURING']
Simulated forward change: new policy entry, structuring_min_count 3->5, made current
  -> alerts=[] (structuring no longer fires)
Explicit rollback: re-run with policy_version='tm-policy-2026.09-synthetic'
  -> alerts=['TM_STRUCTURING']
  -> byte-for-byte identical to the original baseline (model_dump() equality: True)
```
This is exactly the mechanism a real rollback would use — add/point to a policy entry,
never edit code — proving Prompt 14's versioning actually works, not just that it compiles.

## 3. Release-evidence pack (Task 3)

- **Tests**: full per-prompt test list compiled into `TRACEABILITY_MATRIX.md`'s new
  per-challenge table (test file + test names for every CH-01..15 row). Aggregate: 82
  tests across 7 files (`test_api.py` 10, `test_integrated_compliance.py` 43,
  `test_policy.py` 5, `test_release_integrity.py` 2, `test_review.py` 12, `test_rules.py`
  3, `test_service.py` 7) — counts independently reconciled to sum to 82.
- **Evals**: `run_integrated_evals.py` output above — 10 golden cases plus outage/
  metamorphic/adversarial checks, all PASS.
- **Threat model**: compiled into `docs/qa_release_report_integrated.md`'s new "Threat
  model summary" section, mapped against `specs/04_security_privacy/SECURITY_PRIVACY.md`'s
  five controls (KYC-SEC-001..005). One open finding: `CR-002` (self-declared, unauthenticated
  `reviewer_role` on the HITL endpoint) — flagged as the primary residual security gap.
- **Residual risks**: `CR-001` and `CR-002`, both `Proposed`/unapproved, summarized with
  their status in the QA report.
- **Traceability**: `TRACEABILITY_MATRIX.md` extended with an explicit 15-row per-challenge
  table (challenge → requirement → files → tests → status), replacing the previous single
  coarse "Training challenge coverage | all | ... | PASS" row.

## 4. Versioning (Task 4)

- `CURRENT_VERSION.md` updated: `1.0.0-integrated` → `2.0.0-integrated`, with a pointer to
  the QA report and traceability matrix.
- `docs/qa_release_report_integrated.md` rewritten with an explicit RESOLVED/DEFERRED status
  per challenge (no challenge left unlabeled), a Definition-of-Done checklist with evidence
  per line, and the rollback demonstration above.

## Files Changed

- `CURRENT_VERSION.md` — version bump.
- `specs/08_traceability/TRACEABILITY_MATRIX.md` — per-challenge traceability table added.
- `docs/qa_release_report_integrated.md` — finalized release report.

No `src/` file touched — no regression was found in step 1, so none needed fixing, per this
prompt's own STOP condition 3.

## Test Results

| Command | Exit | Result |
| --- | --- | --- |
| `pytest -q` (before doc changes) | 0 | `82 passed` |
| `pytest -q` (after all doc changes) | 0 | `82 passed` — confirms documentation-only changes, zero behavior impact |

## Definition of Done

Checked explicitly, with evidence, in `docs/qa_release_report_integrated.md`'s new
"Definition of Done" section — all nine items from `DEFINITION_OF_DONE.md` checked with a
citation, none merely asserted.

## Production-Readiness Verdict

**READY WITH CONDITIONS** — final verdict for the complete v1→v2 transformation
(Prompts 00–16):

- All 15 engineering challenges have a working, tested, traced implementation. None are
  unimplemented or silently skipped.
- `/v1` compatibility fully preserved and re-verified live at release time.
- Full regression (82 tests), preflight, sanity, evals (including new outage/metamorphic/
  adversarial checks), and smoke server are all green, measured at release time.
- The versioning mechanism built in Prompt 14 was proven to actually enable rollback
  without a code change — not just asserted to exist.
- **Conditions or non-training deployment:** `CR-002` (HITL `reviewer_role` is
  unauthenticated) must be resolved before the review endpoint could be treated as a real
  access control; `CR-001` (KYC refresh-date policy) needs a business decision. Ten
  backlog items remain open, all non-blocking and individually documented with rationale
  for deferral.

This closes the 15-challenge engineering-transformation series. Backlog items (`backlog.md`)
are the natural next body of work, at the user's discretion.
