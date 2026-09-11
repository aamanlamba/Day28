# 15 Integrated AI-FDE Engineering Challenges

These are intentionally embedded across code seams, synthetic data, APIs and tests. The challenge is not to bolt transaction monitoring onto KYC; it is to engineer a single evidence-aware compliance workflow.

| # | Challenge / friction | Embedded engineering issue | Why the connection matters | Repo evidence |
|---:|---|---|---|---|
| 1 | **Identity-to-transaction entity linkage** | Customer IDs, document IDs and transaction owners live in different identifier domains. | False linkage contaminates every downstream monitoring result. | CASE-005, CASE-009 |
| 2 | **Document-intelligence uncertainty propagation** | OCR/extraction confidence and missing evidence are not naturally represented in transaction engines. | Monitoring must know whether KYC facts are trusted, stale or disputed. | CASE-002, CASE-005 |
| 3 | **Cross-document identity resolution** | Name variants, initials, OCR corruption and transliteration can split one identity or merge two. | Entity resolution is a prerequisite for trustworthy monitoring. | CASE-005 |
| 4 | **KYC lifecycle drift vs live transactions** | Identity may become stale or invalid after onboarding while transactions continue. | Ongoing monitoring needs dynamic KYC/refresh hooks. | CASE-004, CASE-008 |
| 5 | **Expected-activity profile normalization** | Occupation, source-of-funds and expected turnover emerge from heterogeneous documents/forms. | Poor normalization makes deviation alerts meaningless. | CASE-011 |
| 6 | **Event-hook idempotency and duplicate delivery** | Transaction streams may redeliver events. | Duplicates can manufacture false velocity/structuring alerts. | CASE-009 |
| 7 | **Out-of-order and late-arriving events** | Streaming order is not guaranteed. | Sliding-window rules must use event time, not arrival order. | CASE-010 |
| 8 | **Structuring / threshold-avoidance detection** | Single transactions can look benign while a 24h aggregate is suspicious. | Requires temporal aggregation and explainable evidence sets. | CASE-007 |
| 9 | **Rapid velocity monitoring** | Burst activity can cross channels and counterparties. | Point-in-time rules miss sequence behavior. | CASE-010 |
| 10 | **High-risk corridor + identity context fusion** | Geographic risk alone is noisy; identity residency/status changes interpretation. | Risk should combine transaction and identity evidence without opaque scoring. | CASE-008 |
| 11 | **Pass-through / funnel behavior** | Credits and debits individually pass basic checks. | Pattern emerges only from temporal pairing and amount similarity. | CASE-012 |
| 12 | **False positives vs explainability** | Aggressive rules increase analyst workload. | Every alert needs reason codes, evidence refs and policy version. | all monitoring cases |
| 13 | **HITL state and feedback integrity** | Review outcomes can become hidden labels or unsafe overrides. | Human decisions must be authorized, traceable and separated from model/rule facts. | design challenge |
| 14 | **Policy/rule/model version drift** | A decision cannot be reproduced if thresholds/providers change silently. | Audit and TEVV require versioned policy/evidence lineage. | all cases |
| 15 | **Evaluation, observability and production readiness** | Unit tests do not prove data quality, drift resilience, throughput or safe failure. | AI FDE must prove correctness, security, operability and rollback readiness. | evals + tests |

## Connection logic

```text
Document Image / PDF
  → Document Intelligence / OCR
  → Normalized Identity Evidence
  → Cross-document Identity Resolution
  → Identity Confidence + KYC Risk Context
  → Transaction Event Hooks
  → Temporal / Behavioral Monitoring Patterns
  → Context Fusion (identity × transaction × policy)
  → Alert / Case Disposition
  → Human Review
  → Audit / Evals / Observability
```

**Design constraint:** deterministic facts and policy gates remain authoritative. AI/LLM components may assist extraction, triage, explanation or investigation behind interfaces, but must not silently invent identity evidence or autonomously file/close compliance cases.
