# Data Contracts

## Legacy `/v1` contracts
`DocumentResult` and `CaseResult` remain unchanged for backward compatibility.

## IdentityProfile
- `case_id`
- `canonical_name`
- `date_of_birth`
- `residency_country`
- `nationality`
- `occupation`
- `expected_monthly_turnover`
- `identity_status = VERIFIED | REVIEW | REJECTED`
- `confidence`
- `risk_flags[]`
- `evidence_refs[]`

## TransactionEvent
- `transaction_id` — idempotency key
- `case_id`
- `timestamp` — event time
- `direction = CREDIT | DEBIT`
- `amount`, `currency`
- `counterparty_id`, `counterparty_country`
- `channel`, optional `device_id`

## MonitoringAlert
- `alert_id`, `case_id`, `pattern_code`
- `severity = LOW | MEDIUM | HIGH | CRITICAL`
- `score` — training prioritization score, not legal probability
- `reasons[]`
- `transaction_ids[]`
- `evidence_refs[]`
- `policy_version`

## ComplianceCaseResult
- `case_id`
- `disposition = CLEAR | REVIEW | ESCALATE`
- `reason_codes[]`
- embedded `IdentityProfile`
- embedded `MonitoringResult`
- `policy_version`
- `evidence_lineage[]`

## ReviewDecision (CH-13)
Append-only; never overwrites `ComplianceCaseResult` — layered on top of it.
- `decision_id`, `case_id`
- `reviewer_id`, `reviewer_role = ANALYST | SUPERVISOR` — currently self-declared by the
  caller, not authenticated (see `specs/09_change_requests/CR-002-review-authorization.md`)
- `timestamp`
- `prior_disposition`, `new_disposition` (both `CLEAR | REVIEW | ESCALATE`)
- `rationale`
- `case_policy_version`, `case_evidence_lineage[]` — the evidence version this decision was
  made against
