# API Contracts

## Legacy routes — compatibility protected
| Method | Path | Purpose |
|---|---|---|
| GET | `/health/live` | Liveness |
| GET | `/health/ready` | Legacy dataset/offline readiness |
| GET | `/v1/cases` | Original six-case synthetic catalog |
| POST | `/v1/documents/verify` | Legacy document verification |
| POST | `/v1/cases/{case_id}/verify` | Legacy case verification |

## Integrated routes
| Method | Path | Purpose |
|---|---|---|
| POST | `/v2/identity/cases/{case_id}/profile` | Resolve identity profile from document evidence + KYC context |
| POST | `/v2/monitoring/cases/{case_id}/evaluate` | Replay/evaluate transaction hooks for one synthetic case. Optional `?policy_version=` query param (CH-14) re-evaluates against a specific past policy version instead of the current one. |
| POST | `/v2/compliance/cases/{case_id}/evaluate` | Fuse identity and monitoring evidence into a governed disposition. Accepts the same optional `?policy_version=` param. |
| POST | `/v2/compliance/cases/{case_id}/review` | Record a governed, append-only human-review decision (CH-13); never mutates the evaluation above |
| GET | `/v2/compliance/cases/{case_id}/reviews` | List the append-only review-decision history for a case |

## Contract rules
- `/v1` response shapes and six-case catalog remain stable.
- `/v2` errors for unknown IDs are controlled client errors.
- transaction IDs are idempotency keys.
- alert outputs include policy version and evidence references.
- policy versions are looked up from `src/policy.py`'s versioned table (CH-14); an unknown
  `policy_version` value is a controlled 400, not a 500 or a silent fallback.
- correlation IDs continue to be returned by middleware.
- review decisions are append-only and never rewrite `evaluate_compliance_case`'s
  deterministic output; downgrading a disposition requires `reviewer_role: SUPERVISOR`.
  `reviewer_id`/`reviewer_role` are currently self-declared, not authenticated — see
  `specs/09_change_requests/CR-002-review-authorization.md`.
