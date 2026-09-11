# Prompt 04 — KYC Lifecycle Drift vs Live Transactions (CH-04)

## Prerequisite
Prompts 00–03 complete.

## Section 2 fill-in
- **Engineering transformation:** KYC Lifecycle Drift vs Live Transactions
- **Problem to solve:** Customer activity continues even when identity evidence becomes
  stale, expired, rejected or materially changed; check whether `src/identity.py` /
  `IdentityProfile.identity_status` in `src/models_v2.py` currently tracks document expiry,
  verification status or a refresh date at all, or only a point-in-time status.
- **Desired production outcome:** `evaluate_transactions`/`evaluate_compliance_case` in
  `src/monitoring.py` / `src/compliance.py` incorporate KYC freshness (expiry, refresh date,
  unresolved identity exceptions) and trigger enhanced review when transaction activity
  continues against stale identity evidence.
- **Business/risk consequence:** Monitoring that ignores KYC staleness keeps scoring
  transactions against identity facts that are no longer true, which is itself a regulatory
  finding independent of whether any individual transaction looks suspicious.

## Repo grounding
- `challenges/CH-04.md`, row 4 of `docs/15_integrated_engineering_challenges.md`
- Evidence: `data/` for **CASE-004** and **CASE-008** (shared with Prompt 10 — CASE-008 also
  exercises high-risk-corridor fusion; keep this prompt's changes scoped to freshness only)
- Code: `src/identity.py`, `src/monitoring.py`, `src/compliance.py`, `src/models_v2.py`
- Specs: `specs/02_features/IDENTITY_RESOLUTION.md`,
  `specs/02_features/COMPLIANCE_MONITORING.md`
- Tests: `tests/test_integrated_compliance.py`

## Suggested change boundary
- In scope: adding/using an expiry or refresh-date field on `IdentityProfile` if genuinely
  absent, and a freshness check in the monitoring/compliance path that adds a reason code
  rather than silently changing the risk score formula.
- Out of scope: the geographic/corridor fusion logic that also touches CASE-008 (Prompt
  10) and the HITL escalation workflow itself (Prompt 13) — this prompt only needs to
  produce the *signal* that identity is stale; routing that signal to a human is Prompt 13's
  concern.

## STOP conditions
1. Complete CLAUDE.md §3 and §15 before implementing. State what "stale" means today (is
   there any expiry concept in the data model at all?) before proposing a threshold.
2. If no expiry/refresh semantics exist anywhere in the current data contracts, treat the
   exact staleness policy as ambiguous and record it under `specs/09_change_requests/`
   rather than inventing a business rule.
3. Follow CLAUDE.md §22 in order and close with §24.
