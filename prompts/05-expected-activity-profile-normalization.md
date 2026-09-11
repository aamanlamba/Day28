# Prompt 05 — Expected-Activity Profile Normalization (CH-05)

## Prerequisite
Prompts 00–04 complete. This is the last identity-side prompt before the transaction/
monitoring prompts (06–11) begin, since monitoring needs this expected-behavior baseline.

## Section 2 fill-in
- **Engineering transformation:** Expected-Activity Profile Normalization
- **Problem to solve:** Occupation, business type, income, expected turnover and
  geographic information often exist as inconsistent free text rather than computable
  attributes; `IdentityProfile.occupation` and `expected_monthly_turnover` exist in
  `src/models_v2.py` but must be checked for whether `src/identity.py` actually normalizes
  them from `data/customer_context/` or passes through raw/inconsistent values.
- **Desired production outcome:** Onboarding evidence and declarations are converted into a
  computable expected-behavior baseline (expected turnover range, geography, counterparty
  profile) that `src/monitoring.py` can compare live transactions against.
- **Business/risk consequence:** Without a normalized baseline, "abnormal volume/value/
  geography" has nothing defensible to be abnormal relative to — deviation-based alerts
  become arbitrary and unexplainable.

## Repo grounding
- `challenges/CH-05.md`, row 5 of `docs/15_integrated_engineering_challenges.md`
- Evidence: `data/` for **CASE-011**, plus all of `data/customer_context/`
- Code: `src/identity.py`, `src/models_v2.py`
- Specs: `specs/02_features/IDENTITY_RESOLUTION.md`,
  `specs/05_data_contracts/DATA_CONTRACTS.md`
- Tests: `tests/test_integrated_compliance.py`

## Suggested change boundary
- In scope: normalization logic in `src/identity.py` for occupation/turnover/geography
  fields already declared on `IdentityProfile`; if a genuinely new field is required
  (e.g. an expected-counterparty-country set), add it to `src/models_v2.py` with
  provenance, not as a bare value.
- Out of scope: the monitoring-side comparison against this baseline — that belongs to
  Prompt 09 (velocity) and Prompt 10 (corridor fusion), which consume this baseline but are
  scoped separately.

## STOP conditions
1. Complete CLAUDE.md §3 and §15 before implementing.
2. Missing or contradictory customer-context fields (register question 3: "which fields can
   be silently omitted without causing a hard failure?") must be handled explicitly — define
   what happens when expected-turnover data is absent, not left as an implicit null that
   later code might mishandle.
3. Follow CLAUDE.md §22 in order and close with §24.
