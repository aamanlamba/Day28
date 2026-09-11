# Compliance Monitoring Patterns & Transaction Monitoring Hooks

The implemented baseline patterns are deliberately simple and explainable. They are workshop seams, not production AML rules.

| Pattern | Baseline implementation | Identity connection |
|---|---|---|
| TM_STRUCTURING | 3+ credits in 8k–9,999 range within 24h | verified owner + evidence lineage |
| TM_RAPID_VELOCITY | 5+ events within 60 minutes | customer/case linkage |
| TM_HIGH_RISK_CORRIDOR | transaction to synthetic high-risk country set | severity strengthened by stale/unresolved/high-risk identity context |
| TM_EXPECTED_ACTIVITY_DEVIATION | period amount >1.75× expected KYC turnover | directly depends on KYC profile |
| TM_PASS_THROUGH | large credits followed by near-equal debits within 6h | customer identity anchors the sequence |

## Hook engineering concerns
- duplicate suppression by transaction ID
- event-time windows rather than arrival order
- schema validation
- deterministic replay
- versioned policy
- evidence refs for every alert
- no raw unrestricted PII in telemetry
