from datetime import datetime, timedelta, timezone
from src.compliance import evaluate_compliance_case
from src.monitoring import evaluate_transactions
from src.identity import build_identity_profile
from src.models import DocumentResult, CaseResult


def test_identity_profile_surfaces_cross_document_name_conflict():
    p = build_identity_profile('CASE-005')
    assert p.identity_status == 'REVIEW'
    assert 'CROSS_DOCUMENT_NAME_MISMATCH' in p.risk_flags


def test_missing_expected_activity_baseline_is_flagged_not_silent():
    # CH-05: a case with no customer_context (no expected_monthly_turnover) must say so
    # explicitly, not leave the monitoring-side deviation check silently disabled.
    p = build_identity_profile('CASE-002')
    assert p.expected_monthly_turnover is None
    assert 'EXPECTED_ACTIVITY_BASELINE_MISSING' in p.risk_flags


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


def _structuring_batch(amounts_and_offsets_hours):
    def tx(i, amount, offset_hours):
        base = datetime(2026, 9, 1, 0, 0, 0, tzinfo=timezone.utc) + timedelta(hours=offset_hours)
        return {
            'transaction_id': f'TS{i}', 'case_id': 'CASE-001',
            'timestamp': base.isoformat(), 'direction': 'CREDIT',
            'amount': amount, 'currency': 'USD', 'counterparty_id': 'CP-X',
            'counterparty_country': 'IN', 'channel': 'TRANSFER', 'device_id': 'DEV-1',
        }
    return [tx(i, amount, offset) for i, (amount, offset) in enumerate(amounts_and_offsets_hours)]


def _has_structuring_alert(monkeypatch, transactions):
    monkeypatch.setattr('src.monitoring.load_json',
                         lambda folder, ident: {'case_id': 'CASE-001', 'transactions': transactions})
    m = evaluate_transactions('CASE-001')
    return any(a.pattern_code == 'TM_STRUCTURING' for a in m.alerts)


def test_structuring_count_boundary(monkeypatch):
    # Below the 3-transaction minimum: no alert.
    two = _structuring_batch([(9000, 0), (9000, 1)])
    assert not _has_structuring_alert(monkeypatch, two)
    # At the 3-transaction minimum: alert.
    three = _structuring_batch([(9000, 0), (9000, 1), (9000, 2)])
    assert _has_structuring_alert(monkeypatch, three)


def test_structuring_amount_lower_boundary(monkeypatch):
    just_under = _structuring_batch([(7999, 0), (7999, 1), (7999, 2)])
    assert not _has_structuring_alert(monkeypatch, just_under)
    at_boundary = _structuring_batch([(8000, 0), (8000, 1), (8000, 2)])
    assert _has_structuring_alert(monkeypatch, at_boundary)


def test_structuring_amount_upper_boundary(monkeypatch):
    just_under = _structuring_batch([(9999, 0), (9999, 1), (9999, 2)])
    assert _has_structuring_alert(monkeypatch, just_under)
    at_boundary = _structuring_batch([(10000, 0), (10000, 1), (10000, 2)])
    assert not _has_structuring_alert(monkeypatch, at_boundary)


def test_structuring_window_boundary(monkeypatch):
    # Exactly 24h apart (0h, 12h, 24h): inclusive upper bound of the window - alert.
    within_window = _structuring_batch([(9000, 0), (9000, 12), (9000, 24)])
    assert _has_structuring_alert(monkeypatch, within_window)
    # Each pair just over 24h01m apart: no single 24h window covers all three - no alert.
    beyond_window = _structuring_batch([(9000, 0), (9000, 24.0167), (9000, 48.0334)])
    assert not _has_structuring_alert(monkeypatch, beyond_window)


def _two_cluster_structuring_events():
    # Uses CASE-001's real case_id so build_identity_profile resolves against real
    # application/customer_context fixtures; only the transactions payload is faked.
    def tx(tid, day, hour):
        return {
            'transaction_id': tid, 'case_id': 'CASE-001',
            'timestamp': f'2026-09-{day:02d}T{hour:02d}:00:00+00:00', 'direction': 'CREDIT',
            'amount': 9000, 'currency': 'USD', 'counterparty_id': 'CP-X',
            'counterparty_country': 'IN', 'channel': 'TRANSFER', 'device_id': 'DEV-1',
        }
    cluster_a = [tx('TA1', 1, 8), tx('TA2', 1, 10), tx('TA3', 1, 12)]
    cluster_b = [tx('TB1', 4, 8), tx('TB2', 4, 10), tx('TB3', 4, 12)]  # >24h after cluster A
    return cluster_a, cluster_b


def _structuring_alert_ids(monkeypatch, transactions):
    monkeypatch.setattr('src.monitoring.load_json',
                         lambda folder, ident: {'case_id': 'CASE-001', 'transactions': transactions})
    m = evaluate_transactions('CASE-001')
    alerts = [a for a in m.alerts if a.pattern_code == 'TM_STRUCTURING']
    assert len(alerts) == 1
    return set(alerts[0].transaction_ids)


def test_structuring_window_is_independent_of_delivery_order(monkeypatch):
    # CH-07: with two non-overlapping qualifying clusters, which one gets reported must
    # depend on event time, not on the arbitrary order events happened to arrive in.
    cluster_a, cluster_b = _two_cluster_structuring_events()
    forward_ids = _structuring_alert_ids(monkeypatch, cluster_a + cluster_b)
    reversed_ids = _structuring_alert_ids(monkeypatch, list(reversed(cluster_b + cluster_a)))
    assert forward_ids == reversed_ids == {'TA1', 'TA2', 'TA3'}


def test_structuring_window_handles_late_arriving_events(monkeypatch):
    # CH-07: events belonging to the chronologically-earliest cluster must still be
    # correctly identified even when they are appended to the delivery list last (i.e.
    # they arrive "late" relative to their actual business timestamp).
    cluster_a, cluster_b = _two_cluster_structuring_events()
    late_arrival_order = cluster_b + cluster_a  # cluster A (earliest) delivered last
    ids = _structuring_alert_ids(monkeypatch, late_arrival_order)
    assert ids == {'TA1', 'TA2', 'TA3'}


def test_high_risk_corridor_is_strengthened_by_identity_context():
    r = evaluate_compliance_case('CASE-008')
    codes = {a.pattern_code for a in r.monitoring.alerts}
    assert 'TM_HIGH_RISK_CORRIDOR' in codes
    assert any('IDENTITY_CONTEXT' in reason for a in r.monitoring.alerts for reason in a.reasons)


def _corridor_batch():
    return [{
        'transaction_id': 'TC1', 'case_id': 'CASE-001',
        'timestamp': '2026-09-01T09:00:00+00:00', 'direction': 'CREDIT',
        'amount': 100, 'currency': 'USD', 'counterparty_id': 'CP-X',
        'counterparty_country': 'XQ', 'channel': 'TRANSFER', 'device_id': 'DEV-1',
    }]


def _clean_identity_profile(**overrides):
    from src.models_v2 import IdentityProfile
    fields = dict(
        case_id='CASE-001', canonical_name='Test Person', date_of_birth='1990-01-01',
        residency_country='IN', nationality='Republic of Meridian', occupation='engineer',
        expected_monthly_turnover=10000, identity_status='VERIFIED', confidence=0.97,
        risk_flags=[], evidence_refs=['document:CASE-001-D1'],
    )
    fields.update(overrides)
    return IdentityProfile(**fields)


def _corridor_alert(monkeypatch, profile):
    monkeypatch.setattr('src.monitoring.build_identity_profile', lambda cid: profile)
    monkeypatch.setattr('src.monitoring.load_json',
                         lambda folder, ident: {'case_id': 'CASE-001', 'transactions': _corridor_batch()})
    m = evaluate_transactions('CASE-001')
    alerts = [a for a in m.alerts if a.pattern_code == 'TM_HIGH_RISK_CORRIDOR']
    assert len(alerts) == 1
    return alerts[0]


def test_corridor_baseline_stays_medium_with_clean_identity(monkeypatch):
    alert = _corridor_alert(monkeypatch, _clean_identity_profile())
    assert alert.severity == 'MEDIUM'
    assert not any('IDENTITY_CONTEXT' in r for r in alert.reasons)


def test_corridor_escalates_and_cites_identity_status(monkeypatch):
    alert = _corridor_alert(monkeypatch, _clean_identity_profile(identity_status='REVIEW'))
    assert alert.severity == 'HIGH'
    assert any('identity_status=REVIEW' in r for r in alert.reasons)
    assert not any('KYC_REFRESH_DUE' in r or 'DOCUMENT_QUALITY_DEGRADED' in r for r in alert.reasons)


def test_corridor_escalates_and_cites_kyc_refresh_due(monkeypatch):
    alert = _corridor_alert(monkeypatch, _clean_identity_profile(risk_flags=['KYC_REFRESH_DUE']))
    assert alert.severity == 'HIGH'
    assert any('KYC_REFRESH_DUE' in r for r in alert.reasons)
    assert not any('identity_status=' in r or 'DOCUMENT_QUALITY_DEGRADED' in r for r in alert.reasons)


def test_corridor_escalates_and_cites_document_quality_degraded(monkeypatch):
    # CH-10: identity confidence must independently influence corridor severity, even
    # when the decision outcome itself remains VERIFIED (Prompt 02's design keeps these
    # axes separate) - previously this case had zero effect on corridor fusion.
    alert = _corridor_alert(monkeypatch, _clean_identity_profile(
        confidence=0.5, risk_flags=['DOCUMENT_QUALITY_DEGRADED']))
    assert alert.severity == 'HIGH'
    assert any('DOCUMENT_QUALITY_DEGRADED' in r for r in alert.reasons)
    assert not any('identity_status=' in r or 'KYC_REFRESH_DUE' in r for r in alert.reasons)


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


def test_conflicting_duplicate_transaction_id_is_distinguished_from_true_duplicate(monkeypatch):
    # CH-06: a repeated transaction_id with DIFFERENT content is a data-integrity signal,
    # not routine redelivery noise - it must not be silently indistinguishable from an
    # exact duplicate.
    conflicting_batch = {
        'case_id': 'CASE-009',
        'transactions': [
            {
                'transaction_id': 'T901', 'case_id': 'CASE-009',
                'timestamp': '2026-09-01T09:00:00+00:00', 'direction': 'CREDIT',
                'amount': 2000, 'currency': 'USD', 'counterparty_id': 'CP-001',
                'counterparty_country': 'IN', 'channel': 'TRANSFER', 'device_id': 'DEV-1',
            },
            {
                'transaction_id': 'T901', 'case_id': 'CASE-009',
                'timestamp': '2026-09-01T09:00:00+00:00', 'direction': 'CREDIT',
                'amount': 9999, 'currency': 'USD', 'counterparty_id': 'CP-001',
                'counterparty_country': 'IN', 'channel': 'TRANSFER', 'device_id': 'DEV-1',
            },
        ],
    }
    monkeypatch.setattr('src.monitoring.load_json', lambda folder, ident: conflicting_batch)
    m = evaluate_transactions('CASE-009')
    assert 'CONFLICTING_DUPLICATE_TRANSACTION' in m.hook_warnings
    assert 'DUPLICATE_EVENT_SUPPRESSED' not in m.hook_warnings
    assert m.processed_transaction_count == 1


def test_evaluate_transactions_is_replayable():
    # CH-06 / CLAUDE.md §7: historical decisions must remain reproducible.
    first = evaluate_transactions('CASE-007')
    second = evaluate_transactions('CASE-007')
    assert first.model_dump() == second.model_dump()


def test_velocity_pattern_detected_over_sliding_window():
    # CASE-010's real fixture already uses 6 distinct counterparties (CP-0..CP-5),
    # implicitly covering the many-counterparties case for this pattern.
    m = evaluate_transactions('CASE-010')
    codes = {a.pattern_code for a in m.alerts}
    assert 'TM_RAPID_VELOCITY' in codes


def _velocity_batch(offsets_minutes, counterparty_ids=None):
    base = datetime(2026, 9, 1, 10, 0, 0, tzinfo=timezone.utc)
    cids = counterparty_ids or [f'CP-{i}' for i in range(len(offsets_minutes))]
    return [
        {
            'transaction_id': f'TV{i}', 'case_id': 'CASE-001',
            'timestamp': (base + timedelta(minutes=m)).isoformat(), 'direction': 'DEBIT',
            'amount': 100, 'currency': 'USD', 'counterparty_id': cid,
            'counterparty_country': 'IN', 'channel': 'TRANSFER', 'device_id': 'DEV-1',
        }
        for i, (m, cid) in enumerate(zip(offsets_minutes, cids))
    ]


def _has_velocity_alert(monkeypatch, transactions):
    monkeypatch.setattr('src.monitoring.load_json',
                         lambda folder, ident: {'case_id': 'CASE-001', 'transactions': transactions})
    m = evaluate_transactions('CASE-001')
    return any(a.pattern_code == 'TM_RAPID_VELOCITY' for a in m.alerts)


def test_velocity_zero_result_below_count(monkeypatch):
    four = _velocity_batch([0, 10, 20, 30])
    assert not _has_velocity_alert(monkeypatch, four)


def test_velocity_count_boundary(monkeypatch):
    four = _velocity_batch([0, 10, 20, 30])
    assert not _has_velocity_alert(monkeypatch, four)
    five = _velocity_batch([0, 10, 20, 30, 40])
    assert _has_velocity_alert(monkeypatch, five)


def test_velocity_window_boundary(monkeypatch):
    within_window = _velocity_batch([0, 15, 30, 45, 60])
    assert _has_velocity_alert(monkeypatch, within_window)
    beyond_window = _velocity_batch([0, 15, 30, 45, 61])
    assert not _has_velocity_alert(monkeypatch, beyond_window)


def test_velocity_fires_regardless_of_counterparty_diversity(monkeypatch):
    # Contrast with CASE-010's many-counterparties case above: a burst concentrated on a
    # single counterparty must still trigger - this rule is a pure frequency check.
    same_counterparty = _velocity_batch([0, 10, 20, 30, 40], counterparty_ids=['CP-SAME'] * 5)
    assert _has_velocity_alert(monkeypatch, same_counterparty)


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
