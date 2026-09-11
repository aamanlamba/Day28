# Prompt 14 — Policy / Rule / Model Version Drift (CH-14)

## Prerequisite
Prompts 00–13 complete (there should now be several thresholds/constants scattered across
Prompts 08–11's pattern rules that this prompt must formalize into one versioning
mechanism, plus Prompt 13's disposition state that must also cite the policy version active
at decision time).

## Section 2 fill-in
- **Engineering transformation:** Policy / Rule / Model Version Drift
- **Problem to solve:** A decision made today may be impossible to reproduce later if
  thresholds, rules, prompts or models change silently; `MonitoringAlert.policy_version` and
  `ComplianceCaseResult.policy_version` already exist as fields in `src/models_v2.py` —
  forensics must determine whether they are populated from a real versioned source
  (`config/baseline.json`?) or are a hard-coded literal.
- **Desired production outcome:** Every threshold/rule/weight introduced in Prompts 08–11
  lives in one versioned, externally visible policy source; each alert/case decision records
  the exact policy version used, and replaying the same inputs against that recorded version
  reproduces the same decision.
- **Business/risk consequence:** Without versioning, historical alerts cannot be replayed or
  explained after a threshold change — this breaks auditability and makes past compliance
  decisions indefensible under review.

## Repo grounding
- `challenges/CH-14.md`, row 14 of `docs/15_integrated_engineering_challenges.md`
  ("repo evidence: all cases")
- Code: `config/baseline.json`, `src/monitoring.py`, `src/compliance.py`,
  `src/models_v2.py` (`policy_version` fields)
- Specs: `specs/02_features/COMPLIANCE_MONITORING.md`,
  `specs/08_traceability/TRACEABILITY_MATRIX.md`
- Tests: `tests/test_release_integrity.py`, `tests/test_integrated_compliance.py`

## Suggested change boundary
- In scope: consolidating the thresholds/constants added by Prompts 08–11 into
  `config/baseline.json` (or an equivalent single versioned source if that file's structure
  doesn't fit), stamping every alert/case with the version actually used, and a replay test
  that re-runs an old case against its recorded policy version and gets the same result even
  after the "current" policy has changed.
- Out of scope: introducing a full policy-management service — the smallest coherent
  mechanism (a version string plus a lookup table) satisfies this challenge; do not add a
  database or external config service unless one is already required elsewhere in the specs.

## STOP conditions
1. Complete CLAUDE.md §3 and §15 before implementing.
2. This must not weaken `/v1` compatibility or change the current default policy's behavior
   for existing tests — it should only make the *existing* behavior versioned and
   reproducible, per CLAUDE.md §13/§14.
3. Follow CLAUDE.md §22 in order and close with §24.
