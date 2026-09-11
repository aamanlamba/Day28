# Prompt 01 — Identity-to-Transaction Entity Linkage (CH-01)

## Prerequisite
Prompt 00 complete and its current-state map available.

## Section 2 fill-in (CLAUDE.md Transformation Objective)
- **Engineering transformation:** Identity-to-Transaction Entity Linkage
- **Problem to solve:** Customer, case, document, account and transaction identifiers may
  not align cleanly, creating false joins or missed associations — `src/identity.py` and
  `src/monitoring.py` currently key off whatever identifiers each data file happens to
  contain, with no single verified correlation key asserted between them.
- **Desired production outcome:** A resolved identity carries one canonical
  customer/account correlation key that every transaction, alert and compliance-case
  record must reference; joins that cannot be verified against that key are rejected or
  flagged, not silently accepted.
- **Business/risk consequence:** A false join attributes someone else's transactions to a
  customer's compliance case (or vice versa), which can hide real risk or generate an alert
  against the wrong person — both are compliance and reputational failures.

## Repo grounding — read before proposing a design
- `challenges/CH-01.md`, row 1 of `docs/15_integrated_engineering_challenges.md`
- Register questions 5, 8 in `docs/engineering_challenge_register.md`
- Evidence: `data/` files for **CASE-005** and **CASE-009** (input_documents,
  customer_context, transactions, ground_truth, expected_baseline_outputs)
- Code: `src/identity.py` (`build_identity_profile`), `src/monitoring.py`
  (`evaluate_transactions`), `src/compliance.py` (`evaluate_compliance_case`),
  `src/repository.py`, `src/models_v2.py` (`IdentityProfile`, `TransactionEvent`,
  `MonitoringResult`, `ComplianceCaseResult`)
- Specs: `specs/02_features/IDENTITY_RESOLUTION.md`,
  `specs/02_features/COMPLIANCE_MONITORING.md`, `specs/05_data_contracts/DATA_CONTRACTS.md`
- Tests: `tests/test_integrated_compliance.py`, `tests/test_service.py`

## Suggested change boundary
- In scope: `src/identity.py`, `src/monitoring.py`, `src/compliance.py`,
  `src/models_v2.py` (add fields only if a canonical key/linkage-evidence field is
  genuinely missing — do not rename existing fields), `tests/test_integrated_compliance.py`,
  a new adversarial case under `data/` if CASE-005/CASE-009 don't already exercise a
  mismatched-identifier scenario, `evals/golden_cases.json` if applicable.
- Out of scope: `/v1` endpoints and `src/service.py`/`src/parser.py`/`src/rules.py`
  (legacy path), OCR/document-intelligence confidence propagation (that's Prompt 02),
  cross-document name matching internals (that's Prompt 03).

## STOP conditions
1. Complete CLAUDE.md §3 (current-state forensics) and §15 (implementation strategy:
   current-state finding, root cause, proposed design, files to modify/add, migration
   implications, risks, test strategy) and report them. Wait for approval before writing
   any code, per `CURSOR_WORKFLOW.md` step 3.
2. If the canonical-key format is ambiguous (e.g. no single field in the synthetic data is
   authoritative), do not invent a policy — record the ambiguity under
   `specs/09_change_requests/` using `specs/09_change_requests/CR_TEMPLATE.md` and propose
   the smallest reversible default, per `AGENTS.md` step 4.
3. Follow CLAUDE.md §22 Execution Contract exactly (Inspect → Trace → Diagnose → Design →
   Change boundary → Implement → Tests → Targeted tests → Regression suite → Fix → Re-run →
   Security review → Production-readiness review) and close with the §24 Final Response
   Format.
