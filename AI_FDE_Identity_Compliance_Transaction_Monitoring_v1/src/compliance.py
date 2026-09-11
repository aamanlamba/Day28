from .identity import build_identity_profile
from .monitoring import evaluate_transactions
from .models_v2 import ComplianceCaseResult

def evaluate_compliance_case(case_id: str, policy_version: str | None = None) -> ComplianceCaseResult:
    identity=build_identity_profile(case_id)
    monitoring=evaluate_transactions(case_id, policy_version)
    reasons=[]
    disposition='CLEAR'
    if identity.identity_status == 'REJECTED':
        disposition='ESCALATE'; reasons.append('IDENTITY_NOT_VERIFIED')
    elif identity.identity_status == 'REVIEW':
        disposition='REVIEW'; reasons.append('IDENTITY_REQUIRES_REVIEW')
    if 'KYC_REFRESH_DUE' in identity.risk_flags:
        # CH-04: staleness must be explainable, not folded into a generic identity reason.
        reasons.append('KYC_REFRESH_DUE')
    # CH-12: name which specific pattern(s) drove a transaction-monitoring escalation,
    # so an analyst isn't forced to separately cross-reference monitoring.alerts.
    triggering_patterns=[f'TRIGGERING_PATTERN:{code}' for code in sorted({a.pattern_code for a in monitoring.alerts})]
    if monitoring.overall_risk in ('HIGH','CRITICAL'):
        disposition='ESCALATE'; reasons.append('TRANSACTION_MONITORING_HIGH_RISK'); reasons.extend(triggering_patterns)
    elif monitoring.overall_risk == 'MEDIUM' and disposition=='CLEAR':
        disposition='REVIEW'; reasons.append('TRANSACTION_MONITORING_MEDIUM_RISK'); reasons.extend(triggering_patterns)
    if not reasons: reasons=['NO_ESCALATION_TRIGGERED']
    lineage=identity.evidence_refs + [f'transactions:{case_id}'] + [f'alert:{a.alert_id}' for a in monitoring.alerts]
    return ComplianceCaseResult(case_id=case_id, disposition=disposition, reason_codes=reasons, identity=identity, monitoring=monitoring, policy_version=monitoring.policy_version, evidence_lineage=lineage)
