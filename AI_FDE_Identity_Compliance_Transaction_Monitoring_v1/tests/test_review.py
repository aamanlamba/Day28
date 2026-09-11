import pytest
from fastapi.testclient import TestClient
from src.app import app
from src.compliance import evaluate_compliance_case
from src.review import submit_review_decision, list_review_decisions, UnauthorizedReviewAction, _REVIEW_LOG

client = TestClient(app)


@pytest.fixture(autouse=True)
def _reset_review_log():
    _REVIEW_LOG.clear()
    yield
    _REVIEW_LOG.clear()


def test_review_upgrade_is_recorded():
    decision = submit_review_decision('CASE-001', reviewer_id='alice', reviewer_role='ANALYST',
                                       new_disposition='REVIEW', rationale='manual spot check')
    assert decision.case_id == 'CASE-001'
    assert decision.prior_disposition == 'CLEAR'
    assert decision.new_disposition == 'REVIEW'
    assert decision.reviewer_id == 'alice'
    assert decision.reviewer_role == 'ANALYST'
    assert decision.rationale == 'manual spot check'


def test_review_does_not_mutate_underlying_evaluation():
    # CH-13: a review decision must never silently rewrite the deterministic,
    # rule-derived disposition it was made against.
    submit_review_decision('CASE-001', reviewer_id='alice', reviewer_role='ANALYST',
                            new_disposition='REVIEW', rationale='manual spot check')
    r = evaluate_compliance_case('CASE-001')
    assert r.disposition == 'CLEAR'


def test_downgrade_requires_supervisor_role():
    with pytest.raises(UnauthorizedReviewAction):
        submit_review_decision('CASE-004', reviewer_id='bob', reviewer_role='ANALYST',
                                new_disposition='CLEAR', rationale='attempting to clear without authority')


def test_downgrade_allowed_for_supervisor_role():
    decision = submit_review_decision('CASE-004', reviewer_id='carol', reviewer_role='SUPERVISOR',
                                       new_disposition='CLEAR', rationale='reviewed evidence, false positive')
    assert decision.prior_disposition == 'ESCALATE'
    assert decision.new_disposition == 'CLEAR'


def test_review_requires_reviewer_id():
    with pytest.raises(ValueError):
        submit_review_decision('CASE-001', reviewer_id='', reviewer_role='ANALYST',
                                new_disposition='REVIEW', rationale='x')


def test_review_requires_rationale():
    with pytest.raises(ValueError):
        submit_review_decision('CASE-001', reviewer_id='alice', reviewer_role='ANALYST',
                                new_disposition='REVIEW', rationale='')


def test_review_history_is_append_only_and_ordered():
    submit_review_decision('CASE-007', reviewer_id='alice', reviewer_role='ANALYST',
                            new_disposition='ESCALATE', rationale='first pass')
    submit_review_decision('CASE-007', reviewer_id='carol', reviewer_role='SUPERVISOR',
                            new_disposition='REVIEW', rationale='downgraded after investigation')
    history = list_review_decisions('CASE-007')
    assert [d.reviewer_id for d in history] == ['alice', 'carol']
    assert [d.decision_id for d in history] == ['CASE-007-REV-1', 'CASE-007-REV-2']


def test_api_review_endpoint_success():
    r = client.post('/v2/compliance/cases/CASE-001/review', json={
        'reviewer_id': 'alice', 'reviewer_role': 'ANALYST',
        'new_disposition': 'REVIEW', 'rationale': 'spot check',
    })
    assert r.status_code == 200
    assert r.json()['new_disposition'] == 'REVIEW'


def test_api_review_endpoint_unauthorized_downgrade_is_403():
    r = client.post('/v2/compliance/cases/CASE-004/review', json={
        'reviewer_id': 'bob', 'reviewer_role': 'ANALYST',
        'new_disposition': 'CLEAR', 'rationale': 'trying to clear',
    })
    assert r.status_code == 403


def test_api_review_endpoint_validation_error_is_422():
    r = client.post('/v2/compliance/cases/CASE-001/review', json={
        'reviewer_id': '', 'reviewer_role': 'ANALYST',
        'new_disposition': 'REVIEW', 'rationale': 'x',
    })
    assert r.status_code == 422


def test_api_review_endpoint_unknown_case_is_404():
    r = client.post('/v2/compliance/cases/CASE-999/review', json={
        'reviewer_id': 'alice', 'reviewer_role': 'ANALYST',
        'new_disposition': 'REVIEW', 'rationale': 'x',
    })
    assert r.status_code == 404


def test_api_review_history_endpoint():
    client.post('/v2/compliance/cases/CASE-012/review', json={
        'reviewer_id': 'alice', 'reviewer_role': 'ANALYST',
        'new_disposition': 'ESCALATE', 'rationale': 'x',
    })
    r = client.get('/v2/compliance/cases/CASE-012/reviews')
    assert r.status_code == 200
    assert len(r.json()) == 1
