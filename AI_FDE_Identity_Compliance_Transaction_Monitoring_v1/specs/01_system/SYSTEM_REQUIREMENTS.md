# System Requirements

## Identity requirements
- **KYC-FR-001 — Document verification:** Verify supported synthetic identity documents and return parsed evidence, deterministic validation results and reason codes.
- **KYC-FR-002 — Case verification:** Verify every document referenced by a synthetic identity case.
- **KYC-FR-003 — Evidence preservation:** No referenced identity evidence may disappear silently.
- **KYC-FR-004 — Cross-document identity consistency:** Material or uncertain identity conflicts shall prevent automatic VERIFIED status.
- **KYC-FR-005 — Explainability:** REVIEW/REJECT outcomes shall identify the principal reason and evidence.

## Monitoring requirements
- **CMP-FR-001 — Transaction hooks:** Accept/replay synthetic transaction-event collections linked to an identity case.
- **CMP-FR-002 — Idempotency:** Duplicate transaction IDs shall not be counted twice in monitoring patterns.
- **CMP-FR-003 — Event-time windows:** Temporal patterns shall use event timestamps and remain stable under input reordering.
- **CMP-FR-004 — Pattern detection:** Baseline structuring, velocity, corridor, expected-activity and pass-through patterns shall be testable independently.
- **CMP-FR-005 — Identity context fusion:** Identity status, KYC refresh state and expected activity may influence monitoring only via explicit rules with evidence lineage.
- **CMP-FR-006 — Policy versioning:** Alerts and integrated cases shall carry the policy version used to create them.
- **CMP-FR-007 — Evidence lineage:** Alerts shall identify contributing transaction IDs and linked identity/document evidence.
- **CMP-FR-008 — Integrated disposition:** Rejected identity or high/critical monitoring risk shall prevent a CLEAR integrated disposition.

## Compatibility requirements
- **KYC-COMP-001:** Existing `/health/live`, `/health/ready`, `/v1/cases`, `/v1/documents/verify`, and `/v1/cases/{case_id}/verify` remain available and preserve the six-case legacy catalog.
- **KYC-COMP-002:** Legacy regression snapshots for CASE-001..CASE-006 remain unchanged.
- **CMP-COMP-001:** New monitoring/integrated behavior is additive under `/v2`.

## Decision-authority boundary
The repository demonstrates engineering patterns, not real KYC/AML policy. Deterministic facts and policy gates remain explicit. Any future AI/LLM component must be schema-constrained, provenance-aware and unable to autonomously approve identity, close compliance cases or perform regulatory reporting.
