# Integrated QA Release Report

Release candidate: `1.0.0-integrated`

## Verification evidence
- Full pytest suite: **32 passed**
- Integrated golden eval suite: **PASS**
- Repository sanity check: **PASS**
- Workshop dependency/path preflight: **PASS**
- Live FastAPI smoke-server check on ephemeral localhost port: **PASS**
- Legacy `/v1` catalog preserved at six cases
- Integrated dataset contains twelve executable cases
- Nineteen synthetic identity-document artifact triplets validated
- Fifteen AI-FDE engineering challenge cards present

## Safety / scope
All identities, countries, transactions, thresholds and monitoring scenarios are fabricated for engineering training. The repository is not a real KYC/AML decision engine and must not be used for regulatory reporting or real customer decisions.
