# Prompt 15 — Evals, Observability & Production Readiness (CH-15)

## Prerequisite
Prompts 00–14 complete. This prompt evaluates the cumulative result of all prior prompts,
so it should run last among the challenge prompts, immediately before Prompt 16's release
pack.

## Section 2 fill-in
- **Engineering transformation:** Evals, Observability & Production Readiness
- **Problem to solve:** Passing unit tests does not prove operational safety, monitoring
  quality, resilience or compliance readiness; check current coverage in
  `evals/golden_cases.json` and `scripts/run_integrated_evals.py` against what CLAUDE.md
  §17 requires (golden, edge, adversarial, metamorphic, outage cases) and what's actually
  present today.
- **Desired production outcome:** Measurable acceptance criteria exist for extraction
  accuracy, identity-resolution quality, contradiction handling, alert precision/recall,
  replayability, latency, duplicate handling, temporal correctness, security, auditability
  and failure recovery — covering every capability built in Prompts 01–14 — with a
  documented release gate.
- **Business/risk consequence:** Without measured evals, there is no evidence the platform
  actually reduces false positives/negatives, survives duplicate/late/adversarial input, or
  recovers from partial failure — claims of "production ready" would be unfounded.

## Repo grounding
- `challenges/CH-15.md`, row 15 of `docs/15_integrated_engineering_challenges.md`
  ("repo evidence: evals + tests")
- Code: `evals/golden_cases.json`, `scripts/run_integrated_evals.py`,
  `scripts/workshop_preflight.py`, `scripts/sanity_check.py`, `src/app.py` (health/ready
  endpoints, logging middleware)
- Docs: `docs/qa_release_report_integrated.md`, `docs/known_limitations.md`,
  `docs/operational_incidents.md`
- Specs: `specs/03_non_functional/NFR.md`, `specs/07_acceptance/ACCEPTANCE_CRITERIA.md`
- Tests: `tests/test_release_integrity.py`, all other files under `tests/`

## Suggested change boundary
- In scope: extending `evals/golden_cases.json` and `scripts/run_integrated_evals.py` to
  cover each of Prompts 01–14's capabilities (identity linkage, confidence propagation,
  cross-document resolution, KYC freshness, expected-activity baseline, idempotency,
  temporal ordering, structuring, velocity, corridor fusion, pass-through, explainability,
  HITL, versioning) with golden/edge/adversarial cases; adding structured logging fields
  (correlation id, entity/transaction id, decision reason) anywhere they're currently
  missing per CLAUDE.md §18; updating `docs/qa_release_report_integrated.md` with measured
  results.
- Out of scope: introducing new metrics/tracing infrastructure (Prometheus, OpenTelemetry,
  etc.) unless already present in `requirements.txt` — use the repo's existing logging and
  scripting patterns; this is a synthetic, offline workshop repo (`WORKSHOP_RUNBOOK.md` §7),
  not a live production deployment.

## STOP conditions
1. Complete CLAUDE.md §3 and §15 before implementing.
2. Report measured results, not assertions — every acceptance criterion in CLAUDE.md §17
   needs an actual number or pass/fail from a real run, per
   `superpowers:verification-before-completion`.
3. Follow CLAUDE.md §22 in order and close with §24, including an explicit
   READY / READY WITH CONDITIONS / NOT READY verdict for the accumulated v2 work.
