# AI FDE — Identity Verification + Compliance Monitoring Brownfield Repo

A self-contained, synthetic, offline-capable engineering repository that tightly connects **Identity Verification Automation / Document Intelligence** with **Compliance Monitoring Patterns & Transaction Monitoring Hooks**.

This is not two disconnected demos. Identity evidence becomes monitoring context; monitoring alerts retain identity/document lineage; all decisions are replayable against versioned synthetic policy.

## What is included
- inherited `/v1` KYC/document-verification API for backwards compatibility
- document OCR sidecar + legacy parser seams
- cross-document identity profile and inconsistency detection
- customer/KYC context including expected activity
- transaction-hook event datasets
- duplicate/idempotency handling
- event-time monitoring patterns
- structuring, velocity, corridor, expected-activity and pass-through patterns
- integrated compliance-case disposition
- evidence lineage + policy version
- 15 embedded AI-FDE engineering challenge cards
- pytest regression/integration tests
- golden integrated evals
- synthetic data only; no API keys/network required

## Architecture
`Document → Evidence → Resolved Identity → KYC Context → Transaction Hook → Monitoring Pattern → Alert → Compliance Case → Human Review → Audit/Evals`

See `docs/integrated_architecture.md` and `docs/15_integrated_engineering_challenges.md`.

## Quick start
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pytest -q
python scripts/run_integrated_evals.py
python -m uvicorn src.app:app --host 127.0.0.1 --port 8000
```
Open `http://127.0.0.1:8000/docs`.

## Useful API calls
```bash
# Legacy identity verification
curl -X POST http://127.0.0.1:8000/v1/cases/CASE-005/verify

# Resolved identity profile
curl -X POST http://127.0.0.1:8000/v2/identity/cases/CASE-005/profile

# Transaction monitoring
curl -X POST http://127.0.0.1:8000/v2/monitoring/cases/CASE-007/evaluate

# Connected identity + monitoring case
curl -X POST http://127.0.0.1:8000/v2/compliance/cases/CASE-008/evaluate
```

## Core synthetic cases
- CASE-001 clean identity + normal transactions
- CASE-004 expired identity + otherwise normal activity
- CASE-005 cross-document name/OCR conflict
- CASE-007 structuring
- CASE-008 high-risk corridor + stale/high-risk identity context
- CASE-009 duplicate transaction hook delivery
- CASE-010 rapid velocity + event-time ordering
- CASE-011 expected-activity deviation
- CASE-012 pass-through/funnel pattern

## Important limitations
The monitoring thresholds and country codes are fabricated for engineering training. This repository is not a production AML/KYC engine and must not be used for real customer decisions or regulatory reporting.
