# Acceptance Criteria

## Legacy compatibility
- **AC-KYC-001:** CASE-001 remains APPROVE on `/v1`.
- **AC-KYC-002:** CASE-004 remains REJECT with `DOCUMENT_EXPIRED` on `/v1`.
- **AC-KYC-003:** CASE-006 remains REJECT with `SUSPECTED_TAMPERING` on `/v1`.
- **AC-KYC-004:** `/v1/cases` continues to expose exactly the original six cases.

## Integrated identity
- **AC-ID-001:** CASE-005 resolves to identity REVIEW with `CROSS_DOCUMENT_NAME_MISMATCH`.
- **AC-ID-002:** CASE-004 resolves to identity REJECTED.

## Monitoring hooks/patterns
- **AC-CMP-001:** CASE-007 produces `TM_STRUCTURING`.
- **AC-CMP-002:** CASE-008 produces `TM_HIGH_RISK_CORRIDOR` and records an `IDENTITY_CONTEXT` reason.
- **AC-CMP-003:** CASE-009 suppresses a duplicate event and reports `DUPLICATE_EVENT_SUPPRESSED`.
- **AC-CMP-004:** CASE-010 produces `TM_RAPID_VELOCITY` using event-time ordering.
- **AC-CMP-005:** CASE-011 produces `TM_EXPECTED_ACTIVITY_DEVIATION` from KYC expected turnover.
- **AC-CMP-006:** CASE-012 produces `TM_PASS_THROUGH`.

## Integrated disposition & auditability
- **AC-INT-001:** CASE-001 is CLEAR with no high-risk monitoring pattern.
- **AC-INT-002:** CASE-004 is ESCALATE even with benign transaction activity because identity is rejected.
- **AC-INT-003:** Every monitoring alert has `policy_version` and non-empty `evidence_refs`.
- **AC-INT-004:** Integrated outputs contain evidence lineage sufficient to replay the decision.
