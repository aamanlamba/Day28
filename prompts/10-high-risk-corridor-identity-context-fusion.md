# Prompt 10 — High-Risk Corridor × Identity-Context Fusion (CH-10)

## Prerequisite
Prompts 00–09 complete, especially Prompt 04 (KYC freshness signal) and Prompt 05
(normalized identity/geography attributes), which this prompt fuses with transaction
geography.

## Section 2 fill-in
- **Engineering transformation:** High-Risk Corridor × Identity-Context Fusion
- **Problem to solve:** Geography alone produces excessive false positives; risk depends on
  customer context and identity evidence (residency, nationality, address, identity
  confidence, KYC refresh state, unresolved-document discrepancies) combined with the
  transaction's counterparty country.
- **Desired production outcome:** `src/monitoring.py`/`src/compliance.py` fuse
  corridor/geographic signals (`TransactionEvent.counterparty_country`) with
  `IdentityProfile` context to produce prioritized, defensible alerts instead of a bare
  geography denylist.
- **Business/risk consequence:** A pure geography rule either over-alerts on routine
  transactions to common corridors (analyst fatigue, see Prompt 12) or under-alerts because
  it ignores that the same corridor is far riskier for a customer with weak/stale identity
  evidence.

## Repo grounding
- `challenges/CH-10.md`, row 10 of `docs/15_integrated_engineering_challenges.md`
- Evidence: `data/` for **CASE-008** (shared with Prompt 04 — that prompt produced the
  staleness signal this prompt consumes as one fusion input)
- Code: `src/monitoring.py`, `src/compliance.py`, `src/identity.py`, `src/models_v2.py`
- Specs: `specs/02_features/COMPLIANCE_MONITORING.md`,
  `specs/02_features/IDENTITY_RESOLUTION.md`
- Tests: `tests/test_integrated_compliance.py`

## Suggested change boundary
- In scope: a fusion rule that combines a corridor/geography signal with identity-context
  fields already on `IdentityProfile` (residency, nationality, confidence, freshness from
  Prompt 04); each resulting alert must cite which identity fields and which transaction
  fields drove it (feeds Prompt 12's explainability requirement).
- Out of scope: defining the corridor risk list itself if one doesn't exist in
  `config/baseline.json` — if it's genuinely undefined, record the gap under
  `specs/09_change_requests/` rather than inventing a real-world sanctions/high-risk-country
  list.

## STOP conditions
1. Complete CLAUDE.md §3 and §15 before implementing.
2. Keep the fusion logic deterministic and rule-based per CLAUDE.md §8; if any weighting is
   probabilistic, it must be advisory only, with the deterministic rule/threshold remaining
   the authoritative gate, per the repo's design constraint.
3. Follow CLAUDE.md §22 in order and close with §24.
