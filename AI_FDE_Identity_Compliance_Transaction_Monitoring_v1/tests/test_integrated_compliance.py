from src.compliance import evaluate_compliance_case
from src.monitoring import evaluate_transactions
from src.identity import build_identity_profile


def test_identity_profile_surfaces_cross_document_name_conflict():
    p = build_identity_profile('CASE-005')
    assert p.identity_status == 'REVIEW'
    assert 'CROSS_DOCUMENT_NAME_MISMATCH' in p.risk_flags


def test_clean_identity_and_normal_activity_stays_clear():
    r = evaluate_compliance_case('CASE-001')
    assert r.identity.identity_status == 'VERIFIED'
    assert r.monitoring.overall_risk in ('LOW','MEDIUM')
    assert r.disposition == 'CLEAR'


def test_structuring_pattern_creates_alert():
    m = evaluate_transactions('CASE-007')
    codes = {a.pattern_code for a in m.alerts}
    assert 'TM_STRUCTURING' in codes
    assert m.overall_risk in ('HIGH','CRITICAL')


def test_high_risk_corridor_is_strengthened_by_identity_context():
    r = evaluate_compliance_case('CASE-008')
    codes = {a.pattern_code for a in r.monitoring.alerts}
    assert 'TM_HIGH_RISK_CORRIDOR' in codes
    assert any('IDENTITY_CONTEXT' in reason for a in r.monitoring.alerts for reason in a.reasons)


def test_stale_or_rejected_identity_forces_review_even_when_transactions_normal():
    r = evaluate_compliance_case('CASE-004')
    assert r.identity.identity_status == 'REJECTED'
    assert r.disposition == 'ESCALATE'
    assert 'IDENTITY_NOT_VERIFIED' in r.reason_codes


def test_duplicate_transaction_hook_is_idempotently_suppressed():
    m = evaluate_transactions('CASE-009')
    assert 'DUPLICATE_EVENT_SUPPRESSED' in m.hook_warnings
    assert m.processed_transaction_count < m.received_transaction_count


def test_velocity_pattern_detected_over_sliding_window():
    m = evaluate_transactions('CASE-010')
    codes = {a.pattern_code for a in m.alerts}
    assert 'TM_RAPID_VELOCITY' in codes


def test_expected_activity_deviation_uses_kyc_profile():
    r = evaluate_compliance_case('CASE-011')
    codes = {a.pattern_code for a in r.monitoring.alerts}
    assert 'TM_EXPECTED_ACTIVITY_DEVIATION' in codes
    assert r.identity.expected_monthly_turnover is not None


def test_pass_through_pattern_detected():
    m = evaluate_transactions('CASE-012')
    codes = {a.pattern_code for a in m.alerts}
    assert 'TM_PASS_THROUGH' in codes


def test_explanations_carry_policy_and_evidence_lineage():
    r = evaluate_compliance_case('CASE-007')
    assert r.policy_version
    assert r.evidence_lineage
    assert all(a.policy_version for a in r.monitoring.alerts)
    assert all(a.evidence_refs for a in r.monitoring.alerts)
