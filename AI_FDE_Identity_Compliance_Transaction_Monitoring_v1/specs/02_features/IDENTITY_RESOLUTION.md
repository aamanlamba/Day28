# Feature Spec — Cross-Document Identity Consistency

**Requirement:** KYC-FR-004  
**Feature ID:** KYC-FEAT-IR-001

## Intent
Prevent a case from receiving APPROVE merely because each document independently passes document-level checks when the documents may not represent a consistent identity.

## Inputs
Parsed identity attributes from all successfully processed documents in the case. Initial training scope focuses on `full_name` and `date_of_birth` because they already exist in the brownfield data model.

## Required behavior
1. Normalize superficial formatting differences before comparison.
2. Treat exact normalized agreement as consistent.
3. A material identity mismatch shall prevent automatic APPROVE.
4. OCR corruption/variation that cannot be confidently classified as either consistent or inconsistent shall result in REVIEW, not silent APPROVE.
5. The case response shall include an actionable reason code when identity consistency affects the decision.
6. Document-level fraud/expiry REJECT outcomes shall continue to dominate the case decision.

## Initial reason codes
- `IDENTITY_NAME_MISMATCH`
- `IDENTITY_DOB_MISMATCH`
- `IDENTITY_MATCH_UNCERTAIN`

## Explicit non-requirements
- No biometric face matching.
- No external identity provider.
- No generative model call.
- No requirement to solve transliteration in the first increment.

## Design freedom
The implementation may use deterministic normalization/similarity logic in the workshop increment, provided thresholds/logic are explicit, tested and recorded in an ADR.
