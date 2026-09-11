# Results — Prompt 13: HITL Workflow Integrity (CH-13)

**Prompt run:** `prompts/13-hitl-workflow-integrity.md` (unmodified)
**Date:** 2026-09-11
**Requirements:** CH-13 (`docs/15_integrated_engineering_challenges.md` row 13) — a design
challenge with no seeded evidence case.
**Approved plan:** the design (new model, new module, role-gated transitions, self-declared
role documented via change request) was reported in-session and approved before any code
was written, per the prompt's own STOP gate for new-capability work.

## 1. Problem Diagnosed

`Disposition` had zero analyst-action model: no reviewer identity, no state-transition
rules, no override audit trail, and no endpoint to record a human decision at all.

## 2. Current-State Findings

- Confirmed via `grep`/inspection: no reviewer/authorization model existed anywhere in
  `src/`; `src/app.py` had no review-action endpoint.
- Confirmed `specs/04_security_privacy/SECURITY_PRIVACY.md` (KYC-SEC-001..005) defines no
  authorization/role mechanism — nothing to reuse, and per the prompt's own instruction, not
  something to invent as a full auth stack.
- Confirmed (again) this system has zero persistence anywhere — every `/v2` read recomputes
  from `data/*.json`. `docs/known_limitations.md` already explicitly accepts "no durable
  human-review queue" and "no durable audit datastore" as known conditions of this training
  repo.

## 3. Root Cause

The capability was never built — this is new-capability work, not a bug fix.

## 4. Architecture / Design Decision

- **New model** `ReviewDecision` (`src/models_v2.py`): `decision_id`, `case_id`,
  `reviewer_id`, `reviewer_role` (`ANALYST`|`SUPERVISOR`), `timestamp`,
  `prior_disposition`, `new_disposition`, `rationale`, `case_policy_version`,
  `case_evidence_lineage` — the last two captured from the `ComplianceCaseResult` at
  decision time as the "evidence version this decision was made against," without needing a
  full object-snapshot store.
- **New module** `src/review.py`: `submit_review_decision(...)` validates `reviewer_id`/
  `rationale` are non-empty (`ValueError`, already mapped to 400 by the existing handler),
  calls `evaluate_compliance_case(case_id)` to read the current governed disposition
  (**never mutated**), and enforces one real governance rule: downgrading disposition
  requires `reviewer_role == 'SUPERVISOR'` (`UnauthorizedReviewAction`, new 403 handler).
  Decisions are appended to an in-memory, per-case, append-only list (`list_review_decisions`
  for retrieval).
- **New endpoints** (`src/app.py`): `POST /v2/compliance/cases/{case_id}/review`,
  `GET /v2/compliance/cases/{case_id}/reviews`.
- **Explicit, documented limitation:** `reviewer_role` is self-declared, not authenticated —
  no auth mechanism exists to verify it. Filed `CR-002` rather than either inventing an auth
  stack (out of scope) or silently shipping an unguarded override channel.
- Updated `specs/06_api_contracts/API_CONTRACTS.md` and
  `specs/05_data_contracts/DATA_CONTRACTS.md` to document the new endpoints/model as living
  specs, per `DEFINITION_OF_DONE.md`'s "documentation reflects actual implemented behavior."

## 5. Files Changed

- `src/models_v2.py` — `ReviewDecision`, `ReviewerRole`, `ReviewDecisionRequest`.
- `src/app.py` — two new endpoints, one new exception handler.
- `specs/06_api_contracts/API_CONTRACTS.md`, `specs/05_data_contracts/DATA_CONTRACTS.md` —
  documented additively.

## 6. Files Added

- `src/review.py` — the review-decision module.
- `tests/test_review.py` — 12 new tests.
- `specs/09_change_requests/CR-002-review-authorization.md` (Proposed, not approved — the
  self-declared-role limitation, documented not hidden).

No `/v1` change. No existing `/v2` endpoint or model changed.

## 7. Data / Schema Changes

Additive only: new `ReviewDecision`/`ReviewDecisionRequest` models. No existing model
changed.

## 8. Tests Added (`tests/test_review.py`, 12 total)

- Upgrade recorded correctly (prior/new disposition, reviewer fields, rationale).
- Review does **not** mutate the underlying deterministic evaluation (re-running
  `evaluate_compliance_case` afterward returns the original disposition).
- Downgrade without `SUPERVISOR` role → `UnauthorizedReviewAction` (negative test).
- Downgrade with `SUPERVISOR` role → succeeds.
- Missing `reviewer_id` / missing `rationale` → `ValueError` (two tests).
- Append-only history, in order, correct `decision_id` sequencing.
- API-level: 200 on valid review, 403 on unauthorized downgrade, 422 on malformed body
  (empty `reviewer_id`), 404 on unknown case (reuses the existing `FileNotFoundError`
  handler), and the history-listing endpoint.
- An `autouse` fixture resets the in-memory `_REVIEW_LOG` before/after each test for
  isolation, since it's module-level shared state.

## 9. Test Results

| Command | Exit | Result |
| --- | --- | --- |
| `pytest -q tests/test_review.py` | 0 | `12 passed` — all passed on first implementation (this is new-capability work with no "before" state to demonstrate failing against) |
| `pytest -q` (full suite) | 0 | `77 passed, 1 warning in 0.20s` (was 65; +12 new tests, zero regressions) |
| `workshop_preflight.py` | 0 | `PREFLIGHT PASSED` |
| `sanity_check.py` | 0 | `SANITY CHECK PASSED` — counts unchanged |
| `run_integrated_evals.py` | 0 | `{"status": "PASS", "failures": []}` |
| `smoke_server.py` | 0 | `SMOKE SERVER PASSED` |

## 10. Edge Cases Covered

- Unauthorized state transition (downgrade without sufficient role) — a required negative
  test per CLAUDE.md's Test Engineering section.
- Missing required fields (`reviewer_id`, `rationale`).
- Unknown case ID (404, reusing existing infrastructure).
- Malformed request body (422, Pydantic validation).
- Append-only ordering across multiple decisions on the same case.

## 11. Security / Privacy Impact

**Significant limitation, documented not hidden:** `reviewer_role` is self-declared and
unauthenticated (see `CR-002`). This is a real, active gap if this endpoint were ever
exposed outside a training context — the module docstring, the CR, and this results file
all say so explicitly. No sensitive data is newly logged; the audit trail records only
already-non-sensitive categorical/reference fields.

## 12. Observability Added

A complete, append-only audit trail for every human review decision: who claimed to act,
when, why, against which prior disposition and evidence version.

## 13. Compatibility Assessment

Fully additive. No existing `/v1` or `/v2` endpoint, model, or behavior changed. Confirmed
by the full regression suite (65 pre-existing tests unchanged, 12 new tests added, all
green).

## 14. Remaining Risks / Assumptions

- **In-memory only** — review history does not survive a process restart. This matches the
  rest of the system's existing no-persistence design (not a new limitation introduced
  here) and demonstrates the governance *pattern*, not a durable audit datastore.
  `docs/known_limitations.md` already accepts this condition for the training repo.
- **`CR-002` (self-declared role) is the primary open risk** — filed, not resolved. Must be
  addressed before any non-training use of this endpoint.
- `GET .../reviews` for a case ID that isn't a real case returns an empty list rather than
  404 (it doesn't call `evaluate_compliance_case`, so it never validates the case exists) —
  a minor, deliberate design choice (a history query reasonably returns "no reviews found"
  rather than erroring), not treated as a defect.

## 15. Production-Readiness Verdict

**READY WITH CONDITIONS** — the implemented capability is safe, tested, additive, and
backward-compatible, and correctly demonstrates governed, auditable HITL structure.
Condition: `CR-002` (real authentication behind `reviewer_role`) must be resolved before this
endpoint could be considered production-ready outside a training context.
