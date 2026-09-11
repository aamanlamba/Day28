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

## MonitoringResult
- `case_id`, `overall_risk = LOW | MEDIUM | HIGH | CRITICAL`
- `alerts[]` (`MonitoringAlert`)
- `received_transaction_count`, `processed_transaction_count`, `hook_warnings[]`
- `policy_version` — populated even when `alerts` is empty (CH-14)

## ComplianceCaseResult
- `case_id`
- `disposition = CLEAR | REVIEW | ESCALATE`
- `reason_codes[]`
- embedded `IdentityProfile`
- embedded `MonitoringResult`
- `policy_version`
- `evidence_lineage[]`

`policy_version` on `MonitoringAlert`/`MonitoringResult`/`ComplianceCaseResult` is resolved
from `src/policy.py`'s versioned threshold table (CH-14), not a bare constant — a past
decision can be reproduced by passing the same `policy_version` back in, even after the
current policy has changed. See `specs/09_change_requests/` for any proposed changes to
threshold values, which should always add a new version rather than editing an existing one.

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
