# Traceability Matrix

| Requirement | Acceptance | Implementation / evidence | Status |
|---|---|---|---|
| KYC-COMP-001/002 | AC-KYC-001..004 | `src/app.py`, `src/repository.py`, legacy snapshots, `tests/test_api.py`, `tests/test_service.py` | PASS |
| KYC-FR-004 | AC-ID-001 | `src/identity.py`, `tests/test_integrated_compliance.py` | PASS |
| CMP-FR-001 | AC-CMP-001..006 | `data/transactions/`, `src/monitoring.py` | PASS |
| CMP-FR-002 | AC-CMP-003 | `_dedupe`, CASE-009 | PASS |
| CMP-FR-003 | AC-CMP-004 | event-time sorting/window logic, CASE-010 | PASS |
| CMP-FR-004 | AC-CMP-001/002/004/005/006 | pattern functions in `src/monitoring.py` | PASS |
| CMP-FR-005 | AC-CMP-002/005 | `src/identity.py` + `src/monitoring.py` | PASS |
| CMP-FR-006 | AC-INT-003 | `POLICY_VERSION`, alert/integrated models | PASS |
| CMP-FR-007 | AC-INT-003/004 | `evidence_refs`, `evidence_lineage` | PASS |
| CMP-FR-008 | AC-INT-001/002 | `src/compliance.py` | PASS |
| Training challenge coverage | all | `docs/15_integrated_engineering_challenges.md`, `challenges/CH-01..15.md` | PASS |
| Evaluation gate | all | `evals/golden_cases.json`, `scripts/run_integrated_evals.py`, pytest | PASS |
