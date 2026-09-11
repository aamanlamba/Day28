from src.compliance import evaluate_compliance_case
from src.monitoring import evaluate_transactions
from src.identity import build_identity_profile
from src.models import DocumentResult, CaseResult


def test_identity_profile_surfaces_cross_document_name_conflict():
    p = build_identity_profile('CASE-005')
    assert p.identity_status == 'REVIEW'
    assert 'CROSS_DOCUMENT_NAME_MISMATCH' in p.risk_flags


def _case_with_dobs(dob_a: str, dob_b: str) -> CaseResult:
    return CaseResult(
        case_id='CASE-TEST-DOB', decision='APPROVE', reason_codes=['BASELINE_RULES_PASSED'],
        documents=[
            DocumentResult(document_id='CASE-TEST-DOB-D1', decision='APPROVE',
                            reason_codes=['BASELINE_RULES_PASSED'],
                            parsed_fields={'full_name': 'Test Person', 'date_of_birth': dob_a},
                            completeness=1.0, warnings=[]),
            DocumentResult(document_id='CASE-TEST-DOB-D2', decision='APPROVE',
                            reason_codes=['BASELINE_RULES_PASSED'],
                            parsed_fields={'full_name': 'Test Person', 'date_of_birth': dob_b},
                            completeness=1.0, warnings=[]),
        ],
        limitation_notice='n/a',
    )


def test_dob_comparison_tolerates_equivalent_formats(monkeypatch):
    # CH-03: the same date of birth expressed in two valid formats must not be treated
    # as a cross-document conflict.
    monkeypatch.setattr('src.identity.verify_case', lambda cid: _case_with_dobs('1992-12-08', '08/12/1992'))
    p = build_identity_profile('CASE-TEST-DOB')
    assert 'CROSS_DOCUMENT_DOB_MISMATCH' not in p.risk_flags


def test_dob_comparison_still_flags_a_genuine_mismatch_across_formats(monkeypatch):
    # Format tolerance must not mask an actual conflicting date of birth.
    monkeypatch.setattr('src.identity.verify_case', lambda cid: _case_with_dobs('1992-12-08', '09/12/1992'))
    p = build_identity_profile('CASE-TEST-DOB')
    assert 'CROSS_DOCUMENT_DOB_MISMATCH' in p.risk_flags


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


def test_kyc_refresh_due_surfaces_a_specific_reason_code(monkeypatch):
    # CH-04: staleness must be explainable at the disposition level, not just folded
    # into a generic "identity requires review" reason.
    case = CaseResult(
        case_id='CASE-TEST-KYC', decision='APPROVE', reason_codes=['BASELINE_RULES_PASSED'],
        documents=[
            DocumentResult(document_id='CASE-TEST-KYC-D1', decision='APPROVE',
                            reason_codes=['BASELINE_RULES_PASSED'],
                            parsed_fields={'full_name': 'Test Person', 'date_of_birth': '1990-01-01'},
                            completeness=1.0, warnings=[]),
        ],
        limitation_notice='n/a',
    )
    monkeypatch.setattr('src.identity.verify_case', lambda cid: case)
    monkeypatch.setattr('src.identity.load_json', lambda folder, ident: {'kyc_refresh_due': True})
    monkeypatch.setattr('src.monitoring.load_json', lambda folder, ident: {'case_id': 'CASE-TEST-KYC', 'transactions': []})
    r = evaluate_compliance_case('CASE-TEST-KYC')
    assert r.identity.identity_status == 'REVIEW'
    assert 'KYC_REFRESH_DUE' in r.identity.risk_flags
    assert r.disposition == 'REVIEW'
    assert 'KYC_REFRESH_DUE' in r.reason_codes


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


def test_identity_confidence_penalized_by_document_quality_warning(monkeypatch):
    # CH-02: a document-level OCR-quality warning must reduce identity confidence, not
    # be discarded once the document decision is aggregated into a case.
    case = CaseResult(
        case_id='CASE-TEST-Q', decision='REVIEW', reason_codes=['MANUAL_REVIEW_REQUIRED'],
        documents=[
            DocumentResult(document_id='CASE-TEST-Q-D1', decision='APPROVE',
                            reason_codes=['BASELINE_RULES_PASSED'],
                            parsed_fields={'full_name': 'Test Person', 'date_of_birth': '1990-01-01'},
                            completeness=1.0, warnings=[]),
            DocumentResult(document_id='CASE-TEST-Q-D2', decision='REVIEW',
                            reason_codes=['MANUAL_REVIEW_REQUIRED'],
                            parsed_fields={'full_name': 'Test Person', 'date_of_birth': '1990-01-01'},
                            completeness=1.0, warnings=['DEGRADED_OCR_QUALITY']),
        ],
        limitation_notice='n/a',
    )
    monkeypatch.setattr('src.identity.verify_case', lambda cid: case)
    p = build_identity_profile('CASE-TEST-Q')
    assert 'DOCUMENT_QUALITY_DEGRADED' in p.risk_flags
    assert p.confidence < 0.70


def test_identity_confidence_penalized_by_incomplete_document_even_when_verified(monkeypatch):
    # CH-02: incomplete field extraction must reduce confidence even when the decision
    # outcome itself stays VERIFIED.
    case = CaseResult(
        case_id='CASE-TEST-C', decision='APPROVE', reason_codes=['BASELINE_RULES_PASSED'],
        documents=[
            DocumentResult(document_id='CASE-TEST-C-D1', decision='APPROVE',
                            reason_codes=['BASELINE_RULES_PASSED'],
                            parsed_fields={'full_name': 'Test Person', 'date_of_birth': '1990-01-01'},
                            completeness=1.0, warnings=[]),
            DocumentResult(document_id='CASE-TEST-C-D2', decision='APPROVE',
                            reason_codes=['BASELINE_RULES_PASSED'],
                            parsed_fields={'full_name': 'Test Person', 'date_of_birth': '1990-01-01'},
                            completeness=0.75, warnings=[]),
        ],
        limitation_notice='n/a',
    )
    monkeypatch.setattr('src.identity.verify_case', lambda cid: case)
    p = build_identity_profile('CASE-TEST-C')
    assert p.identity_status == 'VERIFIED'
    assert p.confidence < 0.97


def test_transaction_with_mismatched_case_id_is_quarantined(monkeypatch):
    # CH-01: a transaction event whose own case_id disagrees with the case it was
    # loaded under must never be silently trusted (false-join risk).
    mismatched_batch = {
        'case_id': 'CASE-005',
        'transactions': [
            {
                'transaction_id': 'T501', 'case_id': 'CASE-005',
                'timestamp': '2026-09-01T09:00:00+00:00', 'direction': 'CREDIT',
                'amount': 2100, 'currency': 'USD', 'counterparty_id': 'CP-001',
                'counterparty_country': 'IN', 'channel': 'TRANSFER', 'device_id': 'DEV-1',
            },
            {
                'transaction_id': 'T502', 'case_id': 'CASE-999-WRONG',
                'timestamp': '2026-09-01T10:00:00+00:00', 'direction': 'CREDIT',
                'amount': 500, 'currency': 'USD', 'counterparty_id': 'CP-002',
                'counterparty_country': 'IN', 'channel': 'TRANSFER', 'device_id': 'DEV-2',
            },
        ],
    }
    monkeypatch.setattr('src.monitoring.load_json', lambda folder, ident: mismatched_batch)
    m = evaluate_transactions('CASE-005')
    assert 'TRANSACTION_CASE_ID_MISMATCH' in m.hook_warnings
    assert m.received_transaction_count == 2
    assert m.processed_transaction_count == 1
    assert all(t_id != 'T502' for a in m.alerts for t_id in a.transaction_ids)
