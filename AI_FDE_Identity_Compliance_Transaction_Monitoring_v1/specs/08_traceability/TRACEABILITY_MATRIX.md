# Traceability Matrix

| Requirement | Acceptance | Implementation / evidence | Status |
|---|---|---|---|
| KYC-COMP-001/002 | AC-KYC-001..004 | `src/app.py`, `src/repository.py`, legacy snapshots, `tests/test_api.py`, `tests/test_service.py` | PASS |
| KYC-FR-004 | AC-ID-001 | `src/identity.py`, `tests/test_integrated_compliance.py` | PASS |
| CMP-FR-001 | AC-CMP-001..006 | `data/transactions/`, `src/monitoring.py` | PASS |
| CMP-FR-002 | AC-CMP-003 | `_dedupe`, CASE-009 | PASS |
| CMP-FR-003 | AC-CMP-004 | event-time sorting/window logic, CASE-010 | PASS |
| CMP-FR-004 | AC-CMP-001/002/004/005/006 | pattern functions in `src/monitoring.py` | PASS |
| CMP-FR-005 | AC-CMP-002/005 | `src/identity.py` + `src/monitoring.py` | PASS |
| CMP-FR-006 | AC-INT-003 | `src/policy.py` (versioned lookup table), `tests/test_policy.py` (includes a replay test reproducing a past decision after the current policy changes) | PASS |
| CMP-FR-007 | AC-INT-003/004 | `evidence_refs`, `evidence_lineage` | PASS |
| CMP-FR-008 | AC-INT-001/002 | `src/compliance.py` | PASS |
| Evaluation gate | all | `evals/golden_cases.json`, `scripts/run_integrated_evals.py`, pytest | PASS |

## Per-challenge traceability (CH-01 .. CH-15)

Resolved via the prompt series in `../../prompts/` (unmodified originals) and
`../../results/` (run reports, one per prompt, outside this repo). Full narrative evidence
for each row is in the correspondingly-numbered `results/NN-*.md` file.

| Challenge | Related requirement | Files | Tests | Status |
|---|---|---|---|---|
| CH-01 Identity-to-transaction linkage | — (repo-internal invariant) | `src/monitoring.py` (`_filter_case_mismatch`) | `test_transaction_with_mismatched_case_id_is_quarantined` | RESOLVED |
| CH-02 Document-intelligence uncertainty propagation | — | `src/identity.py` (`QUALITY_WARNING_CODES`, confidence calc) | `test_identity_confidence_penalized_by_document_quality_warning`, `test_identity_confidence_penalized_by_incomplete_document_even_when_verified` | RESOLVED |
| CH-03 Cross-document identity resolution | KYC-FR-004 | `src/identity.py` (`_normalize_dob`) | `test_dob_comparison_tolerates_equivalent_formats`, `test_dob_comparison_still_flags_a_genuine_mismatch_across_formats` | RESOLVED (bounded gaps: BL-004, BL-005, BL-006) |
| CH-04 KYC lifecycle drift vs live transactions | — | `src/compliance.py` (`KYC_REFRESH_DUE` reason) | `test_kyc_refresh_due_surfaces_a_specific_reason_code` | RESOLVED (explainability); underlying date policy DEFERRED — `CR-001` |
| CH-05 Expected-activity profile normalization | — | `src/identity.py` (`EXPECTED_ACTIVITY_BASELINE_MISSING`) | `test_missing_expected_activity_baseline_is_flagged_not_silent` | RESOLVED (bounded gaps: BL-007, BL-008) |
| CH-06 Transaction-hook idempotency | CMP-FR-002 | `src/monitoring.py` (`_dedupe`) | `test_conflicting_duplicate_transaction_id_is_distinguished_from_true_duplicate`, `test_evaluate_transactions_is_replayable`, `test_duplicate_transaction_hook_is_idempotently_suppressed` | RESOLVED |
| CH-07 Out-of-order and late events | CMP-FR-003 | `src/monitoring.py` (event-time sort in `evaluate_transactions`) | `test_structuring_window_is_independent_of_delivery_order`, `test_structuring_window_handles_late_arriving_events` | RESOLVED (windowing); point-in-time KYC-context reconstruction DEFERRED — `BL-009` |
| CH-08 Structuring / threshold avoidance | CMP-FR-004 | `src/monitoring.py` + `src/policy.py` (`structuring_*`) | `test_structuring_count_boundary`, `test_structuring_amount_lower_boundary`, `test_structuring_amount_upper_boundary`, `test_structuring_window_boundary`, `test_structuring_pattern_creates_alert` | RESOLVED |
| CH-09 Rapid transaction velocity | CMP-FR-004 | `src/monitoring.py` + `src/policy.py` (`velocity_*`) | `test_velocity_zero_result_below_count`, `test_velocity_count_boundary`, `test_velocity_window_boundary`, `test_velocity_fires_regardless_of_counterparty_diversity`, `test_velocity_pattern_detected_over_sliding_window` | RESOLVED |
| CH-10 High-risk corridor × identity-context fusion | CMP-FR-005 | `src/monitoring.py` (Pattern 3) | `test_corridor_baseline_stays_medium_with_clean_identity`, `test_corridor_escalates_and_cites_identity_status`, `test_corridor_escalates_and_cites_kyc_refresh_due`, `test_corridor_escalates_and_cites_document_quality_degraded`, `test_high_risk_corridor_is_strengthened_by_identity_context` | RESOLVED |
| CH-11 Pass-through / funnel-account behaviour | CMP-FR-004 | `src/monitoring.py` + `src/policy.py` (`pass_through_*`) | `test_pass_through_zero_result_no_matching_debit`, `test_pass_through_count_boundary`, `test_pass_through_amount_tolerance_boundary`, `test_pass_through_window_boundary`, `test_pass_through_min_credit_amount_boundary`, `test_pass_through_pattern_detected` | RESOLVED; genuine fan-out/dispersal detection DEFERRED — `BL-010` |
| CH-12 False-positive reduction vs explainability | CMP-FR-007 | `src/monitoring.py`, `src/compliance.py` (reason text) | `test_structuring_reason_cites_actual_observed_count`, `test_corridor_base_reason_cites_actual_countries_matched`, `test_compliance_reason_codes_cite_triggering_pattern`, `test_velocity_reason_cites_actual_observed_count`, `test_pass_through_reason_cites_actual_pair_count` | RESOLVED |
| CH-13 HITL workflow integrity | CMP-FR-008 | `src/review.py`, `src/app.py`, `src/models_v2.py` (`ReviewDecision`) | `tests/test_review.py` (12 tests) | RESOLVED (governance structure); authentication behind `reviewer_role` DEFERRED — `CR-002` |
| CH-14 Policy / rule / model version drift | CMP-FR-006 | `src/policy.py`, `src/monitoring.py`, `src/compliance.py`, `src/app.py` | `tests/test_policy.py` (5 tests, incl. replay) | RESOLVED |
| CH-15 Evals, observability & production readiness | — | `evals/golden_cases.json`, `scripts/run_integrated_evals.py`, `src/app.py` (logging) | `scripts/run_integrated_evals.py` (10 golden cases + 3 checks) | RESOLVED |

Open items tracked outside this matrix: `specs/09_change_requests/CR-001`,
`specs/09_change_requests/CR-002`, and `../../backlog.md` (BL-001 through BL-010) — none
blocking.
