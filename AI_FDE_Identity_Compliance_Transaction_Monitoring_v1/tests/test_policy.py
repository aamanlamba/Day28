import pytest
from src import policy
from src.monitoring import evaluate_transactions
from src.compliance import evaluate_compliance_case


def test_get_policy_returns_current_by_default():
    p = policy.get_policy()
    assert p['version'] == policy.CURRENT_POLICY_VERSION


def test_get_policy_raises_on_unknown_version():
    with pytest.raises(policy.UnknownPolicyVersion):
        policy.get_policy('nonexistent-version')


def test_monitoring_result_has_policy_version_even_with_no_alerts():
    # CASE-001 is the clean happy-path case with zero alerts.
    m = evaluate_transactions('CASE-001')
    assert m.alerts == []
    assert m.policy_version == policy.CURRENT_POLICY_VERSION


def test_compliance_case_result_policy_version_matches_monitoring():
    r = evaluate_compliance_case('CASE-001')
    assert r.policy_version == r.monitoring.policy_version


def test_replay_reproduces_original_decision_after_policy_changes(monkeypatch):
    # CH-14: the exact scenario this challenge is about - a decision made under one
    # policy version must still be reproducible after "current" has moved on.
    original = evaluate_transactions('CASE-007')
    original_version = original.policy_version
    assert any(a.pattern_code == 'TM_STRUCTURING' for a in original.alerts)

    # Simulate a future policy change: tighten structuring's count threshold so
    # CASE-007's 3 qualifying credits no longer trigger an alert under the new policy.
    new_version = 'tm-policy-2099.01-synthetic'
    tightened = {**policy.POLICY_VERSIONS[original_version], 'structuring_min_count': 10}
    monkeypatch.setitem(policy.POLICY_VERSIONS, new_version, tightened)
    monkeypatch.setattr(policy, 'CURRENT_POLICY_VERSION', new_version)

    changed = evaluate_transactions('CASE-007')  # uses the new current policy by default
    assert changed.policy_version == new_version
    assert not any(a.pattern_code == 'TM_STRUCTURING' for a in changed.alerts)

    replayed = evaluate_transactions('CASE-007', policy_version=original_version)
    assert replayed.policy_version == original_version
    assert replayed.model_dump() == original.model_dump()
