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
| POST | `/v2/monitoring/cases/{case_id}/evaluate` | Replay/evaluate transaction hooks for one synthetic case |
| POST | `/v2/compliance/cases/{case_id}/evaluate` | Fuse identity and monitoring evidence into a governed disposition |

## Contract rules
- `/v1` response shapes and six-case catalog remain stable.
- `/v2` errors for unknown IDs are controlled client errors.
- transaction IDs are idempotency keys.
- alert outputs include policy version and evidence references.
- correlation IDs continue to be returned by middleware.
