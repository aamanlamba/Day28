from datetime import timedelta

# CH-14: one versioned lookup table for every /v2 monitoring threshold introduced in
# Prompts 08-11. A past decision stays replayable because a version's entry is never
# mutated after the fact - a policy change means adding a new entry and repointing
# CURRENT_POLICY_VERSION, never editing an existing one.
POLICY_VERSIONS = {
    'tm-policy-2026.09-synthetic': {
        'high_risk_countries': frozenset({'XQ', 'ZR'}),
        'structuring_min_amount': 8000,
        'structuring_max_amount': 10000,
        'structuring_min_count': 3,
        'structuring_window': timedelta(hours=24),
        'velocity_min_count': 5,
        'velocity_window': timedelta(minutes=60),
        'pass_through_window': timedelta(hours=6),
        'pass_through_amount_tolerance': 0.08,
        'pass_through_min_credit_amount': 5000,
        'pass_through_min_matched_count': 4,
    },
}
CURRENT_POLICY_VERSION = 'tm-policy-2026.09-synthetic'

class UnknownPolicyVersion(ValueError):
    pass

def get_policy(version: str | None = None) -> dict:
    """Returns the threshold bundle for `version` (defaulting to the current policy),
    with the resolved version string included under 'version' for stamping onto
    MonitoringAlert/MonitoringResult/ComplianceCaseResult."""
    version = version or CURRENT_POLICY_VERSION
    if version not in POLICY_VERSIONS:
        raise UnknownPolicyVersion(f'unknown policy version: {version}')
    return {**POLICY_VERSIONS[version], 'version': version}
