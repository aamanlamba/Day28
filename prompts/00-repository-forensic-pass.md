# Prompt 00 — Repository Forensic Pass (no code changes)

## How to use this prompt
Run this first, before any of prompts 01–16. It corresponds to `CURSOR_WORKFLOW.md` step 1
("Repository forensic pass") and CLAUDE.md §3 ("Current-State Forensics — Mandatory Before
Coding"). It produces the shared current-state map every later prompt will cite instead of
re-deriving it.

## Task

Read, in this order, and do **not** modify any file:
1. `AGENTS.md`
2. `SPEC_DRIVEN_DEVELOPMENT.md`
3. `specs/00_product/PRD.md` and every file under `specs/01_system/`, `specs/02_features/`,
   `specs/03_non_functional/`, `specs/04_security_privacy/`, `specs/05_data_contracts/`,
   `specs/06_api_contracts/`, `specs/07_acceptance/`
4. `docs/integrated_architecture.md`, `docs/15_integrated_engineering_challenges.md`,
   `docs/engineering_challenge_register.md`, `docs/workshop_challenge_map.md`,
   `docs/data_dictionary_integrated.md`, `docs/known_limitations.md`,
   `docs/operational_incidents.md`, `docs/scenario_catalog.md`
5. `README.md`, `CURRENT_VERSION.md`, `DEFINITION_OF_READY.md`, `DEFINITION_OF_DONE.md`,
   `TRACEABILITY_MATRIX.md`
6. Everything under `src/`, `tests/`, `evals/`, `scripts/`, `config/`
7. The 15 challenge briefs under `challenges/CH-01.md` … `CH-15.md`

Then, without writing or editing anything:

1. **Reproduce the baseline.** Run, in order, and paste the exact output of each:
   ```bash
   python scripts/workshop_preflight.py
   python scripts/sanity_check.py
   pytest -q
   python scripts/smoke_server.py
   ```
   State whether every command exited 0, per `WORKSHOP_RUNBOOK.md` §4. If any command fails,
   stop and report the failure — do not attempt a fix in this prompt.

2. **Build a current-state map** covering, with file:line citations for every claim:
   - The `/v1` request path (`src/app.py` → `src/service.py` → `src/parser.py`/`src/ocr.py`
     → `src/rules.py` → `src/repository.py`) and the `/v2` request path (`src/app.py` →
     `src/identity.py` / `src/monitoring.py` / `src/compliance.py` → `src/models_v2.py`).
   - Every domain object currently defined in `src/models.py` and `src/models_v2.py`, and
     which of them have no persistence beyond the request lifecycle (i.e., are recomputed
     from `data/` on every call rather than stored).
   - Which of the 15 challenges in `docs/15_integrated_engineering_challenges.md` already
     have partial code coverage (e.g. `MonitoringResult.hook_warnings`,
     `IdentityProfile.confidence`) versus which have none.
   - Which of the 20 open questions in `docs/engineering_challenge_register.md` are answered
     by reading the code, and which remain genuinely open.
   - Every existing test in `tests/` and what behavior it actually locks in (not what its
     name implies).
   - Every `TODO`, hard-coded synthetic-only assumption, or missing validation you find in
     `src/`.

3. **Identify the top gaps** across the 15 challenges, ranked by which would most contaminate
   downstream results if left unfixed (per the design constraint in
   `docs/15_integrated_engineering_challenges.md`: "deterministic facts and policy gates
   remain authoritative").

4. **State compatibility constraints**: confirm which `/v1` and `/v2` response shapes must
   not change, per `docs/integrated_architecture.md` ("Brownfield contract") and
   `AGENTS.md` ("Preserve `/v1` API compatibility unless an approved spec explicitly changes
   it").

## STOP

Do not propose or make any code change in this prompt. Report the current-state map, the
baseline command output, and the ranked gap list, and wait for confirmation before starting
Prompt 01.
