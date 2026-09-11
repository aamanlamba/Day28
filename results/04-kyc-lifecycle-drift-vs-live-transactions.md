# Results — Prompt 04: KYC Lifecycle Drift vs Live Transactions (CH-04)

**Prompt run:** `prompts/04-kyc-lifecycle-drift-vs-live-transactions.md` (unmodified)
**Date:** 2026-09-11
**Requirements:** CH-04 (`docs/15_integrated_engineering_challenges.md` row 4)
**Approved plan:** current-state finding, root cause, design, and the decision to file
CR-001 were reported in-session and approved before any file was written.

## 1. Problem Diagnosed

Two different staleness mechanisms exist in the codebase: document expiry (real, date-driven,
already correct) and KYC refresh due-ness (a static boolean with no underlying date, and no
specific reason code surfaced when it drives a disposition).

## 2. Current-State Findings

- **Document expiry** (`src/rules.py`'s `REFERENCE_DATE` comparison) is genuinely date-driven
  and already flows correctly end-to-end: CASE-004's expired document → `DOCUMENT_EXPIRED` →
  `REJECT` → `identity_status='REJECTED'` → `disposition='ESCALATE'`. Confirmed via the
  existing, passing `test_stale_or_rejected_identity_forces_review_even_when_transactions_normal`.
  Not touched in this pass.
- **KYC refresh due** (`ctx.get('kyc_refresh_due')` in `src/identity.py`) is a **static
  boolean** with no supporting date field anywhere — not in
  `data/customer_context/*.json` (checked all 9 files), not in
  `specs/05_data_contracts/DATA_CONTRACTS.md`, not on `IdentityProfile`. Only **CASE-008**
  has it set `true`, and that fixture is entangled with Prompt 10's high-risk-corridor
  scenario.
- The escalation *behavior* the challenge wants already existed: `KYC_REFRESH_DUE` already
  bumps `identity_status` to `REVIEW` (`src/identity.py`), which already forces
  `disposition` to at least `REVIEW` in `src/compliance.py`, independent of monitoring
  results. What was missing was **explainability**: `reason_codes` only ever showed the
  generic `IDENTITY_REQUIRES_REVIEW`, never the specific `KYC_REFRESH_DUE` cause, even
  though that fact already existed in `identity.risk_flags`.
- Per the prompt's STOP condition 2 (no expiry/refresh semantics exist in the data
  contract), the underlying "what date, what cycle" policy question was **not** guessed at
  — filed as `CR-001` instead.

## 3. Root Cause

`src/compliance.py`'s `reason_codes` construction only checked `identity_status`, never the
more granular `identity.risk_flags`, so a specific, already-available signal
(`KYC_REFRESH_DUE`) was collapsed into a generic reason.

## 4. Architecture / Design Decision

Exactly the suggested change boundary given in the prompt: added a reason code, changed
nothing about scoring or disposition logic. `src/compliance.py` now appends `KYC_REFRESH_DUE`
to `reason_codes` whenever that flag is present on the identity profile, in addition to
whatever generic reason already applies.

Separately, filed `specs/09_change_requests/CR-001-kyc-refresh-date-tracking.md` (status
`Proposed`) proposing a real `kyc_refresh_due_date` field and a documented refresh-cycle
policy — explicitly not implemented, pending a business-policy decision.

## 5. Files Changed

- `src/compliance.py` — 3 lines added.
- `tests/test_integrated_compliance.py` — one new test.

## 6. Files Added

- `specs/09_change_requests/CR-001-kyc-refresh-date-tracking.md` (Proposed, not approved,
  no code implements it).

No schema or `/v1` change.

## 7. Data / Schema Changes

None implemented. CR-001 proposes one for future consideration.

## 8. Tests Added

`test_kyc_refresh_due_surfaces_a_specific_reason_code` — synthetic case (via `monkeypatch`
on `src.identity.verify_case`/`load_json` and `src.monitoring.load_json`, since CASE-008 is
shared with Prompt 10) with `kyc_refresh_due: true`, otherwise clean documents and zero
transactions; asserts `identity_status == 'REVIEW'`, `disposition == 'REVIEW'`, and —
the new behavior — `'KYC_REFRESH_DUE' in reason_codes`.

## 9. Test Results

| Command | Exit | Result |
| --- | --- | --- |
| New test (before fix) | 1 | Failed as expected: `KYC_REFRESH_DUE` absent, only `IDENTITY_REQUIRES_REVIEW` present |
| New test + `test_stale_or_rejected_identity_forces_review_even_when_transactions_normal` + `test_high_risk_corridor_is_strengthened_by_identity_context` (after fix) | 0 | All 3 passed — confirms no entanglement with the CASE-008/Prompt-10 corridor test |
| `pytest -q` (full suite) | 0 | `38 passed, 1 warning in 0.16s` (was 37; +1 new test, zero regressions) |
| `workshop_preflight.py` | 0 | `PREFLIGHT PASSED` |
| `sanity_check.py` | 0 | `SANITY CHECK PASSED` — counts unchanged |
| `run_integrated_evals.py` | 0 | `{"status": "PASS", "failures": []}` |
| `smoke_server.py` | 0 | `SMOKE SERVER PASSED` |

## 10. Edge Cases Covered

- KYC-refresh-due as the sole issue (no document problems, no transaction alerts) still
  produces a specific, traceable reason code.
- Confirmed no interaction with the only real fixture sharing this flag (CASE-008), which
  also exercises high-risk-corridor severity escalation — both pass independently.

Not covered (explicitly deferred to CR-001): actual date-based refresh-due computation.

## 11. Security / Privacy Impact

None. Reuses an already-computed, already-non-sensitive boolean-derived flag as a reason
code string; no new data exposed.

## 12. Observability Added

`KYC_REFRESH_DUE` is now a distinct, traceable top-level reason code on
`ComplianceCaseResult`, rather than being indistinguishable from any other cause of an
identity-driven REVIEW.

## 13. Compatibility Assessment

Fully additive. `/v1` untouched. `/v2` `ComplianceCaseResult.reason_codes` gains a possible
new value; no existing test asserts an exact/exhaustive reason-code list (all checks use
`in`), so no existing test's expectations changed — confirmed by the full regression suite.

## 14. Remaining Risks / Assumptions

- CR-001 is filed but not approved — no code depends on it. The underlying "when is KYC
  refresh actually due" policy remains a business decision, not an engineering one.
- CASE-008 is the only fixture exercising `KYC_REFRESH_DUE` at all; broader coverage would
  benefit from Prompt 15's eval-hardening work.

## 15. Production-Readiness Verdict

**READY WITH CONDITIONS** — the implemented fix is safe, tested, and backward-compatible.
Condition: CR-001 needs a business-policy decision and approval before KYC lifecycle
staleness can be considered fully engineered (versus explainable, which this pass achieved).
