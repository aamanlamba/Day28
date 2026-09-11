# Change Request — CR-001

**Status:** Proposed
**Raised by:** Prompt 04 forensics (CH-04, KYC Lifecycle Drift vs Live Transactions)
**Date:** 2026-09-11
**Affected requirements:** KYC-FR-004 (indirectly); no existing requirement ID currently
covers KYC refresh scheduling itself.

## Requested change

Add a real, date-based field (e.g. `kyc_refresh_due_date`) to the customer-context data
model and to `IdentityProfile`, and compute "is refresh due" by comparing it against the
current/reference date — rather than storing the already-computed boolean result as a
static fixture value.

## Why

`docs/15_integrated_engineering_challenges.md` (CH-04) and `challenges/CH-04.md` both
describe the friction as "customer activity continues even when identity evidence becomes
stale... [the system must track] document expiry, verification status, refresh date and
unresolved identity exceptions." Document expiry is already handled correctly with a real
date computation (`src/rules.py`'s `REFERENCE_DATE` comparison). KYC refresh due-ness is not
— it never becomes stale or fresh again on its own; it is whatever a human hardcoded into
the test fixture.

## Current behavior

`data/customer_context/{case_id}.json` carries a boolean `kyc_refresh_due` field.
`src/identity.py:build_identity_profile` reads it directly (`ctx.get('kyc_refresh_due')`)
and, if true, adds a `KYC_REFRESH_DUE` risk flag and bumps `identity_status` toward
`REVIEW`. There is no date field anywhere in `data/customer_context/`,
`specs/05_data_contracts/DATA_CONTRACTS.md`, or `IdentityProfile`'s schema that this boolean
is derived from.

## Proposed target behavior

1. Add `kyc_refresh_due_date: str | None` (ISO date) to the customer-context data contract
   and, if useful for API consumers, to `IdentityProfile`.
2. Compute `kyc_refresh_due = kyc_refresh_due_date is not None and kyc_refresh_due_date <= REFERENCE_DATE`
   (or an equivalent live comparison in production), replacing the static boolean.
3. Decide and document the actual refresh-cycle policy this date is meant to represent
   (e.g. annual review, risk-tier-dependent cadence) — this is a business-policy decision
   outside engineering scope and is the main reason this is a change request rather than an
   immediate fix.

## Compatibility impact

- **Data:** `data/customer_context/*.json` fixtures would need the new field; the existing
  `kyc_refresh_due` boolean could be kept as a derived/computed value for one transition
  period, or replaced outright with a fixture update (all 9 files, only `CASE-008` currently
  sets it `true`).
- **API:** additive only if `kyc_refresh_due_date` is exposed on `IdentityProfile` — no
  existing field removed or renamed.
- **Tests:** `tests/test_integrated_compliance.py`'s CASE-008-based assertions
  (`test_high_risk_corridor_is_strengthened_by_identity_context`) do not assert on the
  boolean directly and should be unaffected if the *computed result* for CASE-008 stays
  `true` under whatever reference/refresh date is chosen.

## Security/privacy impact

None identified. A refresh-due date is not more sensitive than the boolean it would replace.

## Acceptance criteria changes

None proposed yet — pending a decision on the refresh-cycle policy referenced above. Once
decided, a new AC (e.g. `AC-ID-003`) should specify the exact comparison and reference-date
semantics, mirroring how `AC-KYC-002` documents the existing document-expiry gate.

## Decision

Pending — not yet approved. Filed for review; no code change has been made based on this CR.
