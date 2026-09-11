# Prompt Series — AI FDE KYC + Transaction Monitoring v1 → v2

This directory holds the prompt sequence for working through the **15 Engineering
Challenges** documented in `../Engineering_challenges_in_repo_1.0.pdf` and mirrored in
`../AI_FDE_Identity_Compliance_Transaction_Monitoring_v1/challenges/CH-01.md` … `CH-15.md`.

Each prompt is a filled-in instance of the **Production-Grade Engineering Transformation**
framework already loaded for this repo as `../CLAUDE.md` (identical to
`../Production-Grade_Engineering_Transformation_Prompt.pdf`). The prompts do **not** repeat
that 24-section framework — CLAUDE.md auto-applies to every session opened in this
directory. Each prompt only fills in **Section 2 (Transformation Objective)** and adds
repo-specific grounding (files, evidence cases, specs, register questions, change
boundary) so the executing agent doesn't have to rediscover it.

No prompt has been run yet. Nothing in `AI_FDE_Identity_Compliance_Transaction_Monitoring_v1/`
has been modified.

## Sequence

| # | File | Purpose |
|---|------|---------|
| 00 | `00-repository-forensic-pass.md` | Baseline reproduction + current-state map. No code changes. Run once, first. |
| 01 | `01-identity-to-transaction-entity-linkage.md` | CH-01 |
| 02 | `02-document-intelligence-uncertainty-propagation.md` | CH-02 |
| 03 | `03-cross-document-identity-resolution.md` | CH-03 |
| 04 | `04-kyc-lifecycle-drift-vs-live-transactions.md` | CH-04 |
| 05 | `05-expected-activity-profile-normalization.md` | CH-05 |
| 06 | `06-transaction-hook-idempotency.md` | CH-06 |
| 07 | `07-out-of-order-and-late-events.md` | CH-07 |
| 08 | `08-structuring-threshold-avoidance.md` | CH-08 |
| 09 | `09-rapid-transaction-velocity.md` | CH-09 |
| 10 | `10-high-risk-corridor-identity-context-fusion.md` | CH-10 |
| 11 | `11-pass-through-funnel-account-behaviour.md` | CH-11 |
| 12 | `12-false-positive-reduction-vs-explainability.md` | CH-12 |
| 13 | `13-hitl-workflow-integrity.md` | CH-13 |
| 14 | `14-policy-rule-model-version-drift.md` | CH-14 |
| 15 | `15-evals-observability-production-readiness.md` | CH-15 |
| 16 | `16-release-v2-evidence-pack.md` | Wrap-up: regression, rollback demo, evidence pack, traceability, cut v2. Run once, last. |

## Why this order

Challenges build on each other along the pipeline
`Document → Identity → KYC Context → Transaction → Monitoring → Alert → HITL → Audit`
(see `docs/integrated_architecture.md` and `docs/15_integrated_engineering_challenges.md`).
Identity-side challenges (01–05) should land before the transaction/monitoring challenges
that consume identity output (06–11), which should land before the cross-cutting
governance challenges (12–15). Challenges sharing evidence cases (e.g. 07/09 both use
CASE-010; 04/10 both use CASE-008) are easiest to verify together but are kept as separate
prompts so each has its own test-first cycle, change boundary and evidence record, per
`AGENTS.md` and `WORKSHOP_RUNBOOK.md`.

## How to run a prompt

1. Open a session in `AI_FDE_Identity_Compliance_Transaction_Monitoring_v1/` (so `AGENTS.md`,
   `.cursor/rules/*.mdc` and the repo's specs are in scope) with the repo-root `CLAUDE.md`
   still active.
2. Paste the target prompt file's contents.
3. Respect every "STOP" checkpoint in the prompt — it corresponds to a gate in
   `CURSOR_WORKFLOW.md` and `SPEC_DRIVEN_DEVELOPMENT.md` (`READ → TRACE → CHALLENGE → PLAN →
   TEST → IMPLEMENT → VERIFY → EVIDENCE → UPDATE`). Do not let the agent skip from forensics
   straight to implementation.
4. Only after a prompt's Definition of Done is satisfied (per `DEFINITION_OF_DONE.md` and
   CLAUDE.md §23) move to the next numbered prompt.

## Status

All 17 prompts are drafted and awaiting your review. None have been executed.
