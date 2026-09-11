# Integrated Data Dictionary

## IdentityProfile
- `case_id`: synthetic case key
- `canonical_name`: normalized working identity label
- `identity_status`: VERIFIED / REVIEW / REJECTED
- `confidence`: engineering confidence indicator, not legal proof
- `risk_flags`: cross-document or lifecycle concerns
- `evidence_refs`: document lineage pointers
- `expected_monthly_turnover`: synthetic KYC expectation used only for exercises

## TransactionEvent
- event-time timestamp
- direction and amount
- counterparty + country
- channel + device identifier
- transaction ID is the idempotency key

## MonitoringAlert
- pattern code and severity
- score for prioritization
- human-readable reasons
- exact transaction IDs contributing to the pattern
- identity/document evidence references
- policy version

All records are fabricated and must not be used for real compliance decisions.
