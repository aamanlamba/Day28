# Integrated QA Release Report

Release candidate: **`2.0.0-integrated`** (see `CURRENT_VERSION.md`)
Report finalized: 2026-09-11, at the close of Prompt 16 (the release-evidence pack), after
Prompts 00–15 of the engineering-transformation prompt series. Full per-prompt evidence
lives under `../../results/00-*.md` through `16-*.md` in the repo root's `results/`
directory; the prompts themselves (unmodified, reusable) are under `../../prompts/`.

## Verification evidence (measured at release time)

| Check | Result |
| --- | --- |
| Full pytest suite | **82 passed**, 0 failed (`pytest -q`) |
| Integrated golden eval suite | **PASS** — 10 golden cases, plus outage/metamorphic/adversarial checks (`scripts/run_integrated_evals.py`) |
| Repository sanity check | **PASS** — 6 legacy cases, 12 integrated cases, 19 document artifacts, 15 challenge cards |
| Workshop dependency/path preflight | **PASS** (Python 3.13.15) |
| Live FastAPI smoke-server check | **PASS** |
| Legacy `/v1` catalog | preserved at exactly six cases; `tests/test_release_integrity.py`'s byte-for-byte snapshot equality against `data/expected_baseline_outputs/*.json` still holds, including the intentionally-preserved `CASE-005` brownfield gap on `/v1` |

All five commands were re-run at release time (not merely cited from earlier prompts) and
all exited 0. No failure required classification.

## Rollback / backward-compatibility demonstration

Live-checked at release time, not merely asserted:

1. **`/v1` unchanged**: `GET /v1/cases` → 6 cases; `POST /v1/documents/verify` on
   `CASE-001-PASSPORT` → `APPROVE`; `POST /v1/cases/CASE-005/verify` → `APPROVE` (the
   intentionally-preserved brownfield gap — `/v2`'s hardened identity resolution in Prompts
   02–03 never touched `/v1`'s behavior for this case).
2. **Policy-version rollback without a code change** (the representative mechanism from
   Prompt 14): ran CASE-007 under the current policy (`tm-policy-2026.09-synthetic`,
   `TM_STRUCTURING` fires). Added a new, stricter policy entry in-process
   (`structuring_min_count: 5`) and repointed `CURRENT_POLICY_VERSION` to it — no file
   edited, no redeploy — and confirmed the alert stops firing under the new default. Then
   explicitly requested the *original* `policy_version` and got a byte-for-byte identical
   result to the pre-change baseline. This is the exact mechanism a real rollback would use:
   add a new policy entry (or point back at an old one) rather than editing code.

## Eval coverage detail (CH-15)

`evals/golden_cases.json` covers **10 of 12** integrated cases, checking disposition,
monitoring alerts/warnings, identity status, and risk flags. `scripts/run_integrated_evals.py`
adds three checks beyond golden-case comparison, each representing a CLAUDE.md §17 category
at the release-gate layer (each was already unit-tested by pytest, now also exercised by the
script an operator actually runs): outage/failure-recovery, metamorphic (policy replay), and
adversarial (unauthorized HITL downgrade rejection).

## Threat model summary (Prompts 01–15, against `specs/04_security_privacy/SECURITY_PRIVACY.md`)

| Control | Status | Evidence |
| --- | --- | --- |
| KYC-SEC-001 (path safety) | Unaffected, still enforced | `safe_id()` in `src/repository.py`; `test_path_traversal_blocked` |
| KYC-SEC-002 (data minimization) | Held throughout | Every new log line (Prompt 15) cites only synthetic case IDs, categorical codes, and policy versions — no raw identity/document content. `ReviewDecision.rationale` (Prompt 13) is free text supplied by a reviewer; low risk today since storage is in-memory only, but would need a retention/redaction policy if this became durable — noted here, not separately backlogged since it's speculative until persistence exists |
| KYC-SEC-003 (input validation) | Extended, held | New `/v2` review endpoint uses Pydantic `Field` constraints and `Literal` enums; `test_api_review_endpoint_validation_error_is_422` |
| KYC-SEC-004 (evidence integrity) | Extended, held | `ReviewDecision` captures `case_policy_version`/`case_evidence_lineage` rather than silently substituting evidence |
| KYC-SEC-005 (new integrations need a security review) | Followed | The HITL endpoint (a new integration surface) was not shipped without one — `CR-002` **is** that required security-design update, filed explicitly rather than skipped |
| **Primary open finding** | **Not resolved — `CR-002`** | `reviewer_id`/`reviewer_role` on the HITL review endpoint are self-declared, not authenticated (no auth mechanism exists anywhere in this repo to verify them). **Must not be treated as a real access control outside a training context.** |

## Residual risks (open `specs/09_change_requests/` items)

- **`CR-001`** — KYC refresh-due is a static boolean with no supporting date field; the
  actual refresh-cycle policy (what date, what cadence) is a business decision, not
  resolved by this series.
- **`CR-002`** — see threat model above; the more significant of the two.

Both are `Proposed`, unapproved, and explicitly documented rather than silently shipped.

## Challenge coverage summary (CH-01 .. CH-15)

Full per-challenge requirement/file/test mapping: `TRACEABILITY_MATRIX.md`.

| # | Challenge | Status | Evidence |
| --- | --- | --- | --- |
| 01 | Identity-to-transaction entity linkage | RESOLVED | `results/01-*.md` |
| 02 | Document-intelligence uncertainty propagation | RESOLVED | `results/02-*.md` |
| 03 | Cross-document identity resolution | RESOLVED (bounded gaps: BL-004, BL-005, BL-006) | `results/03-*.md` |
| 04 | KYC lifecycle drift vs live transactions | RESOLVED (explainability); underlying date policy DEFERRED (`CR-001`) | `results/04-*.md` |
| 05 | Expected-activity profile normalization | RESOLVED (bounded gaps: BL-007, BL-008) | `results/05-*.md` |
| 06 | Transaction-hook idempotency | RESOLVED | `results/06-*.md` |
| 07 | Out-of-order and late events | RESOLVED (windowing); point-in-time KYC reconstruction DEFERRED (`BL-009`) | `results/07-*.md` |
| 08 | Structuring / threshold avoidance | RESOLVED, boundary-tested | `results/08-*.md` |
| 09 | Rapid transaction velocity | RESOLVED, boundary-tested | `results/09-*.md` |
| 10 | High-risk corridor × identity-context fusion | RESOLVED | `results/10-*.md` |
| 11 | Pass-through / funnel-account behaviour | RESOLVED; fan-out/dispersal detection DEFERRED (`BL-010`) | `results/11-*.md` |
| 12 | False-positive reduction vs explainability | RESOLVED | `results/12-*.md` |
| 13 | HITL workflow integrity | RESOLVED (governance structure); authentication DEFERRED (`CR-002`) | `results/13-*.md` |
| 14 | Policy / rule / model version drift | RESOLVED | `results/14-*.md` |
| 15 | Evals, observability & production readiness | RESOLVED | `results/15-*.md` |

No challenge is unimplemented. "DEFERRED" items are explicitly scoped, non-blocking gaps
with a named change request or backlog item — never a silent omission.

## Definition of Done (`../../DEFINITION_OF_DONE.md`)

- [x] Approved requirements and acceptance criteria satisfied — see `TRACEABILITY_MATRIX.md`.
- [x] Targeted tests pass — every prompt's new tests confirmed individually before merging (see each `results/NN-*.md`).
- [x] Full legacy regression suite passes — 82/82, re-run at release time.
- [x] Security/privacy checks relevant to the change pass — see threat model above; one open finding (`CR-002`) documented, not hidden.
- [x] API/data contract impact documented — `specs/06_api_contracts/API_CONTRACTS.md`, `specs/05_data_contracts/DATA_CONTRACTS.md` updated in Prompts 13/14.
- [x] Traceability matrix updated — `TRACEABILITY_MATRIX.md`, this prompt.
- [x] Evidence record contains commands, results and residual risks — this report plus 16 `results/*.md` files.
- [x] No unresolved high-severity ambiguity remains — all identified ambiguities were resolved into either an implementation or an explicit, named change request/backlog item.
- [x] Documentation reflects actual implemented behavior — specs updated additively alongside each capability throughout the series.

## Safety / scope

All identities, countries, transactions, thresholds and monitoring scenarios are fabricated
for engineering training. The repository is not a real KYC/AML decision engine and must not
be used for regulatory reporting or real customer decisions.
