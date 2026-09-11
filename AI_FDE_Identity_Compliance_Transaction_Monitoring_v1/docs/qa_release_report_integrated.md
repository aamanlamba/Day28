# Integrated QA Release Report

Release candidate: `2.0.0-integrated` (pending Prompt 16's version bump)
Report updated: 2026-09-11, after Prompts 00–15 of the engineering-transformation prompt
series. Full per-prompt evidence lives under `../../results/00-*.md` through `15-*.md` in
the repo root's `results/` directory.

## Verification evidence (measured, this run)

| Check | Result |
| --- | --- |
| Full pytest suite | **82 passed**, 0 failed (`pytest -q`) |
| Integrated golden eval suite | **PASS** — 10 golden cases, plus outage/metamorphic/adversarial checks (`scripts/run_integrated_evals.py`) |
| Repository sanity check | **PASS** — 6 legacy cases, 12 integrated cases, 19 document artifacts, 15 challenge cards |
| Workshop dependency/path preflight | **PASS** (Python 3.13.15) |
| Live FastAPI smoke-server check | **PASS** |
| Legacy `/v1` catalog | preserved at exactly six cases; `tests/test_release_integrity.py`'s byte-for-byte snapshot equality against `data/expected_baseline_outputs/*.json` still holds, including the intentionally-preserved `CASE-005` brownfield gap on `/v1` |

## Eval coverage detail (CH-15)

`evals/golden_cases.json` now covers **10 of 12** integrated cases (added CASE-002 and
CASE-005 in this pass), checking disposition, monitoring alerts/warnings, identity status,
and risk flags — previously only disposition/alerts/warnings were checked, and CASE-005 was
entirely absent. `scripts/run_integrated_evals.py` adds three checks beyond golden-case
comparison, each closing a CLAUDE.md §17 category that had no representation at the
release-gate layer (each was already unit-tested by pytest, but not previously exercised as
part of the release-gate script an operator would actually run):

- **Outage/failure-recovery**: an unknown case ID fails in a controlled way (`FileNotFoundError`), not an unhandled crash.
- **Metamorphic**: replaying CASE-007 against its own recorded `policy_version` reproduces an identical result (CH-14).
- **Adversarial**: an unauthorized HITL downgrade attempt is rejected (CH-13).

## Challenge coverage summary (CH-01 .. CH-15)

| # | Challenge | Status | Evidence |
| --- | --- | --- | --- |
| 01 | Identity-to-transaction entity linkage | Implemented | `results/01-*.md` |
| 02 | Document-intelligence uncertainty propagation | Implemented | `results/02-*.md` |
| 03 | Cross-document identity resolution | Implemented (bounded gaps logged: BL-004, BL-005, BL-006) | `results/03-*.md` |
| 04 | KYC lifecycle drift vs live transactions | Implemented; underlying date policy deferred (CR-001) | `results/04-*.md` |
| 05 | Expected-activity profile normalization | Implemented (bounded gaps logged: BL-007, BL-008) | `results/05-*.md` |
| 06 | Transaction-hook idempotency | Implemented | `results/06-*.md` |
| 07 | Out-of-order and late events | Implemented; point-in-time KYC reconstruction deferred (BL-009) | `results/07-*.md` |
| 08 | Structuring / threshold avoidance | Implemented, boundary-tested | `results/08-*.md` |
| 09 | Rapid transaction velocity | Implemented, boundary-tested | `results/09-*.md` |
| 10 | High-risk corridor × identity-context fusion | Implemented | `results/10-*.md` |
| 11 | Pass-through / funnel-account behaviour | Implemented; fan-out/dispersal deferred (BL-010) | `results/11-*.md` |
| 12 | False-positive reduction vs explainability | Implemented | `results/12-*.md` |
| 13 | HITL workflow integrity | Implemented; real authentication deferred (CR-002) | `results/13-*.md` |
| 14 | Policy / rule / model version drift | Implemented | `results/14-*.md` |
| 15 | Evals, observability & production readiness | This report | `results/15-*.md` |

Open change requests (`specs/09_change_requests/`): `CR-001` (KYC refresh-date tracking),
`CR-002` (real authentication behind HITL `reviewer_role`). Open backlog items
(`../../backlog.md`): BL-001 through BL-010 (10 items — 2 Improvement, 8 Change Request) —
none blocking, all documented with rationale for deferral.

## Safety / scope

All identities, countries, transactions, thresholds and monitoring scenarios are fabricated
for engineering training. The repository is not a real KYC/AML decision engine and must not
be used for regulatory reporting or real customer decisions.
