# Prompt 16 — Release / v2 Evidence Pack (wrap-up)

## Prerequisite
Prompts 00–15 complete and their individual Definitions of Done satisfied.

## Purpose
This prompt does not introduce a new engineering transformation. It closes out the series
per `docs/workshop_challenge_map.md` steps 6–7 and `DEFINITION_OF_DONE.md`, and is the point
at which this brownfield repo's `/v2` surface becomes the basis for a versioned release.

## Task

1. **Full regression + preflight.** Run and paste output:
   ```bash
   python scripts/workshop_preflight.py
   python scripts/sanity_check.py
   pytest -q
   python scripts/smoke_server.py
   python scripts/run_integrated_evals.py
   ```
   Every command must exit 0. Classify any failure as target-spec defect, legacy-regression
   conflict, implementation defect, or environment issue, per `CURSOR_WORKFLOW.md` step 5 —
   do not weaken a test to force green.

2. **Demonstrate rollback and backward compatibility**, per
   `docs/workshop_challenge_map.md` step 6 and CLAUDE.md §14/§20:
   - Show `/v1` endpoints (`GET /v1/cases`, `POST /v1/documents/verify`,
     `POST /v1/cases/{case_id}/verify`) behave identically to the Prompt 00 baseline output.
   - Identify one representative change from Prompts 01–15 and show it can be disabled/
     reverted (e.g. via the policy version from Prompt 14) without a code rollback, proving
     the versioning mechanism actually works.

3. **Produce the release-evidence pack**, per `docs/workshop_challenge_map.md` step 7 and
   `DEFINITION_OF_DONE.md`:
   - Tests: full list of tests added/changed across Prompts 01–15 and their current status.
   - Evals: results from `scripts/run_integrated_evals.py` against the golden/edge/
     adversarial cases added in Prompt 15.
   - Threat model: summarize the security/privacy findings surfaced across Prompts 01–15
     (sensitive-data logging, authorization gaps from Prompt 13, input validation) against
     `specs/04_security_privacy/SECURITY_PRIVACY.md`.
   - Residual risks: anything recorded under `specs/09_change_requests/` during Prompts
     01–15 that is still open.
   - Traceability: update `TRACEABILITY_MATRIX.md` to map each of the 15 challenges to the
     requirement IDs, files, and tests that resolved it.

4. **Version the release.** Update `CURRENT_VERSION.md` to reflect the completed
   transformation set (e.g. `2.0.0`), and record in `docs/qa_release_report_integrated.md`
   which of the 15 challenges are resolved, partially resolved, or deferred, with evidence
   references for each.

## STOP conditions
1. Do not mark the release done unless every item in `DEFINITION_OF_DONE.md` and CLAUDE.md
   §23 is checked with cited evidence, not asserted.
2. If any of the 15 challenges is only partially resolved, say so explicitly in the release
   report with a READY WITH CONDITIONS or NOT READY verdict (CLAUDE.md §24) — do not report
   READY for an incomplete transformation.
3. This prompt should not modify `src/` beyond what's needed to fix a regression found in
   step 1 — its job is evidence and versioning, not new functionality.
