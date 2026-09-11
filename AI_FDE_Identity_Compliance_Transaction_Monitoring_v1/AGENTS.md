# AI FDE KYC — Agent Operating Instructions

This repository is a Specs-Driven Development training environment. Treat `specs/` as the source of engineering intent and the current `src/` implementation as brownfield evidence, not as the definition of correct future behavior.

## Mandatory workflow
1. Read `SPEC_DRIVEN_DEVELOPMENT.md` and `specs/00_product/PRD.md`.
2. Identify requirement IDs and acceptance criteria relevant to the requested change.
3. Inspect current code and regression tests; distinguish baseline behavior from target behavior.
4. If the requirement is ambiguous, do not code. Record an assumption or change request under `specs/09_change_requests/`.
5. Produce an implementation plan before editing code.
6. Define or update tests that trace to acceptance criteria.
7. Implement the smallest change that satisfies the approved spec.
8. Run targeted tests, then the full regression suite.
9. Record evidence and update `specs/08_traceability/TRACEABILITY_MATRIX.md`.
10. Do not mark work complete until Definition of Done is met.

## Guardrails
- Preserve `/v1` API compatibility unless an approved spec explicitly changes it.
- Preserve synthetic/offline operation; no external API keys or network dependency.
- Never silently drop identity evidence.
- Do not log raw sensitive identity fields unnecessarily.
- Do not convert existing limitations into implicit requirements.
- Every material engineering decision must cite a requirement, ADR, or approved change request.
