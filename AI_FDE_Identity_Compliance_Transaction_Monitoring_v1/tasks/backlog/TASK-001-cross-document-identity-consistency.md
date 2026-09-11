# TASK-001 — Cross-Document Identity Consistency

**Status:** Ready for planning  
**Requirements:** KYC-FR-004, KYC-FR-005, KYC-NFR-004  
**Acceptance:** AC-KYC-004

## Goal
Introduce the first target-behavior increment that prevents CASE-005 from silently APPROVE-ing when cross-document identity evidence is uncertain.

## Required execution sequence
1. Read `specs/02_features/IDENTITY_RESOLUTION.md`.
2. Inspect CASE-005 fixtures, parser output and current regression assertion.
3. Propose an ADR for deterministic name normalization/similarity policy; do not invent thresholds silently.
4. Add an acceptance test for AC-KYC-004 that fails against the baseline.
5. Implement the smallest isolated identity-consistency component.
6. Integrate it into case decisioning without weakening document-level REJECT semantics.
7. Run targeted and full regression suites.
8. Update traceability and evidence.

## Definition of success
CASE-005 no longer receives automatic APPROVE under the approved target policy, while clean/expired/tampered baseline scenarios remain stable.
