# AI FDE Workshop — KYC + Transaction Monitoring: v1 → v2

This repo root coordinates a structured pass through **15 engineering challenges** embedded
in the brownfield service at `AI_FDE_Identity_Compliance_Transaction_Monitoring_v1/`. The
goal is to work through each challenge as a governed, test-first engineering change and end
up with a hardened `v2` of that service — not a rewrite.

## What's here

| Path | Role |
|---|---|
| `AI_FDE_Identity_Compliance_Transaction_Monitoring_v1/` | The brownfield service under transformation. **Untouched so far.** |
| `CLAUDE.md` | Project-wide engineering posture and execution contract that governs every change made in this repo (see below). |
| `Engineering_challenges_in_repo_1.0.pdf` | Source definition of the 15 engineering challenges. |
| `Engineering_challenge_workflow.pdf` | One-page pipeline diagram the challenges are embedded across. |
| `Production-Grade_Engineering_Transformation_Prompt.pdf` | Source of `CLAUDE.md` (identical content, exported as a PDF template). |
| `Initial Instruction.md` | The original task instruction that kicked this off. |
| `prompts/` | The 18-prompt series that works through the 15 challenges one at a time. **Reference copies — never edited after being run**, so any prompt can be re-run later exactly as originally drafted. |
| `results/` | One results file per prompt actually run, named to match (`00-repository-forensic-pass.md`, `01-...md`, …). This is where forensics findings, command output, and evidence live — kept separate from `prompts/` so the prompts stay pristine and reusable. |
| `backlog.md` | Findings and change requests surfaced mid-prompt that were out of that prompt's scope. Reviewed later, not auto-actioned — many get resolved as a side effect of a subsequent prompt. |

## The approach

**Why prompts, not a plan-and-code pass.** The 15 challenges are deliberately interlocking —
they touch the same handful of small source files (`src/identity.py`, `src/monitoring.py`,
`src/compliance.py`, `src/models_v2.py`) from different angles. Working through all 15 in one
pass risks conflating unrelated fixes and losing the "smallest safe change" discipline
`CLAUDE.md` requires. Instead, each challenge gets its own prompt with its own forensics,
test-first change, and evidence record — so each is independently reviewable and revertable.

**Why nothing has been changed yet.** Per the original instruction, the code folder stays
untouched until the prompt series itself is reviewed. Producing 15+ prompts and then
immediately running them would make review meaningless — you can't approve an approach
you haven't seen.

**Governing framework.** Every prompt in `prompts/` assumes `CLAUDE.md`'s 24-section
Production-Grade Engineering Transformation framework is active for the session (it
auto-loads as this repo's project instructions). The prompts don't repeat that framework —
they only fill in its Section 2 (Transformation Objective) and add repo-specific grounding
(exact files, evidence cases, specs, open questions, a scoped change boundary) so the
executing agent doesn't have to rediscover context that's already been established. Inside
`AI_FDE_Identity_Compliance_Transaction_Monitoring_v1/`, that framework sits alongside the
repo's own governance docs — `AGENTS.md` (mandatory workflow), `SPEC_DRIVEN_DEVELOPMENT.md`
(the READ → TRACE → CHALLENGE → PLAN → TEST → IMPLEMENT → VERIFY → EVIDENCE → UPDATE loop),
and `CURSOR_WORKFLOW.md` (the same loop phrased as Cursor prompts) — which the prompt series
was built to be consistent with, not to replace.

**Brownfield discipline.** Per `docs/integrated_architecture.md` inside the service repo,
the inherited `/v1` API must keep working throughout; `/v2` is additive. Every prompt's
change boundary is written to respect that, and CLAUDE.md's compatibility and change-boundary
sections (§14, §21) apply to all of them.

## The plan

1. **Prompt 00 — Repository forensic pass.** Reproduce the baseline (`workshop_preflight.py`,
   `sanity_check.py`, `pytest`, `smoke_server.py`), build a current-state map, and rank the
   15 challenges by how much downstream contamination each causes if left unfixed. No code
   changes.
2. **Prompts 01–05 — Identity-side challenges.** Entity linkage, document-intelligence
   confidence propagation, cross-document identity resolution, KYC lifecycle freshness,
   expected-activity profile normalization. These establish the identity/KYC foundation
   later prompts depend on.
3. **Prompts 06–11 — Transaction/monitoring-side challenges.** Event-hook idempotency,
   out-of-order/late events, structuring detection, velocity detection, corridor × identity
   fusion, pass-through/funnel detection. Built on the identity foundation from step 2.
4. **Prompts 12–15 — Cross-cutting governance.** Explainability of alerts already produced,
   human-in-the-loop review integrity, policy/threshold versioning, and evals/observability/
   production-readiness across everything built so far.
5. **Prompt 16 — Release evidence pack.** Full regression, rollback/backward-compatibility
   proof, a release-evidence pack (tests, evals, threat model, residual risks), traceability
   update, and a version bump marking the service as `v2`.

Each numbered prompt carries its own STOP checkpoints (forensics and plan must be reported
and approved before any code is written) and Definition of Done, per `CLAUDE.md` §23 and the
service repo's own `DEFINITION_OF_DONE.md`. No prompt should be run out of order — later
prompts assume earlier ones already landed. Full detail, including exact file grounding and
evidence-case mapping per challenge, is in `prompts/README.md`.

## Status

- Prompt 00 (repository forensic pass) has been run. Results: `results/00-repository-forensic-pass.md`.
  No code change — it was a read-only pass. Baseline is green (preflight, sanity check,
  32 pytest tests, smoke server all pass).
- Prompts 01–16 have not been run yet. Nothing in
  `AI_FDE_Identity_Compliance_Transaction_Monitoring_v1/` has been modified.
