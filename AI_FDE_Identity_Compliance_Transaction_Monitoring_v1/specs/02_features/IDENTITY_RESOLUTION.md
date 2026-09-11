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

## Reason codes

**Implemented** (`src/identity.py`, locked in by `AC-ID-001`):
- `CROSS_DOCUMENT_NAME_MISMATCH`
- `CROSS_DOCUMENT_DOB_MISMATCH`

Resolved via `backlog.md` BL-004: an earlier draft of this spec proposed
`IDENTITY_NAME_MISMATCH`/`IDENTITY_DOB_MISMATCH`/`IDENTITY_MATCH_UNCERTAIN` before
implementation; the acceptance criteria and code were built against the `CROSS_DOCUMENT_*`
names instead. The implemented naming is canonical — this section now matches it rather
than the reverse, since renaming the implemented flags would break the already-approved,
already-passing `AC-ID-001` for no functional benefit.

Requirement #4's "cannot be confidently classified as either consistent or inconsistent"
case does not have a distinct third reason code today — the implementation uses a single
similarity threshold, so anything below it is treated as `CROSS_DOCUMENT_NAME_MISMATCH`
(REVIEW), satisfying the requirement's actual mandate (prevent silent APPROVE) without a
separate "uncertain" tier. A dedicated `IDENTITY_MATCH_UNCERTAIN`-style code remains a
possible future refinement, not a current gap.

## Explicit non-requirements
- No biometric face matching.
- No external identity provider.
- No generative model call.
- No requirement to solve transliteration in the first increment.

## Design freedom
The implementation may use deterministic normalization/similarity logic in the workshop increment, provided thresholds/logic are explicit, tested and recorded in an ADR.

Initials/abbreviated first-name handling (`backlog.md` BL-005) is recorded in
`docs/adr/ADR-002-initials-aware-name-matching.md`.
