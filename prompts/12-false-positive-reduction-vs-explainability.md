# Prompt 12 — False-Positive Reduction vs Explainability (CH-12)

## Prerequisite
Prompts 00–11 complete (all monitoring patterns exist and produce alerts to make
explainable).

## Section 2 fill-in
- **Engineering transformation:** False-Positive Reduction vs Explainability
- **Problem to solve:** More sophisticated scoring can reduce alert volume but make
  decisions opaque and hard to defend; check whether `MonitoringAlert.reasons`,
  `evidence_refs` and `policy_version` in `src/models_v2.py` are populated with real,
  specific content by every pattern rule from Prompts 06–11, or left generic/empty.
- **Desired production outcome:** Every alert links the specific transactions, the
  rule/pattern that matched, the identity/KYC factors involved, and the policy version, so
  an investigator can reconstruct why it fired without reading source code.
- **Business/risk consequence:** Alerts without traceable reasons either get dismissed
  without proper review (compliance risk) or overwhelm analysts because nothing can be
  triaged by cause (operational risk) — both undermine the point of monitoring.

## Repo grounding
- `challenges/CH-12.md`, row 12 of `docs/15_integrated_engineering_challenges.md`
  ("repo evidence: all monitoring cases")
- Register question 10 in `docs/engineering_challenge_register.md`
- Code: `src/monitoring.py`, `src/compliance.py`, `src/models_v2.py` (`MonitoringAlert`,
  `ComplianceCaseResult.reason_codes`, `evidence_lineage`)
- Specs: `specs/02_features/COMPLIANCE_MONITORING.md`,
  `specs/07_acceptance/ACCEPTANCE_CRITERIA.md`
- Tests: `tests/test_integrated_compliance.py`

## Suggested change boundary
- In scope: auditing every pattern rule added in Prompts 06–11 for whether `reasons`,
  `transaction_ids` and `evidence_refs` are specific (not a generic string), and fixing any
  that aren't; a test per pattern rule asserting the alert's evidence fields identify the
  exact contributing transactions/identity fields.
- Out of scope: adding new detection patterns — this prompt is strictly about the
  explainability of alerts that already exist; do not change what triggers an alert, only
  what the alert records about why.

## STOP conditions
1. Complete CLAUDE.md §3 and §15 before implementing — the forensics step here is
   specifically an audit of existing alert payloads against the "every alert links
   transactions, rule/pattern matches, KYC factors, policy versions and reasons" requirement
   in `docs/15_integrated_engineering_challenges.md`.
2. If a pattern rule cannot currently justify itself with concrete evidence, that is itself
   a finding to report, not something to paper over with a generic reason string.
3. Follow CLAUDE.md §22 in order and close with §24.
