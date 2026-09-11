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
