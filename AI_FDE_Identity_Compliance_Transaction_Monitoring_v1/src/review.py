from datetime import datetime, timezone
from .compliance import evaluate_compliance_case
from .models_v2 import ReviewDecision

# CH-13: HITL workflow integrity. Review decisions are append-only and never mutate the
# rule/model-derived ComplianceCaseResult - re-running evaluate_compliance_case for the
# same case must always return the same deterministic disposition regardless of how many
# review decisions have been layered on top of it.
#
# In-memory only: this system has no persistence layer anywhere (every /v2 read recomputes
# from data/*.json), so this demonstrates the governance *pattern* - role-gated
# transitions, an append-only audit trail, evidence-version linkage - rather than a durable
# audit datastore. See specs/09_change_requests/CR-002-review-authorization.md for the
# related, deliberately-deferred authentication gap.
_DISPOSITION_RANK = {'CLEAR': 0, 'REVIEW': 1, 'ESCALATE': 2}
_REVIEW_LOG: dict[str, list[ReviewDecision]] = {}

class UnauthorizedReviewAction(Exception):
    pass

def submit_review_decision(case_id: str, reviewer_id: str, reviewer_role: str, new_disposition: str, rationale: str) -> ReviewDecision:
    if not reviewer_id:
        raise ValueError('reviewer_id is required')
    if not rationale:
        raise ValueError('rationale is required')
    if new_disposition not in _DISPOSITION_RANK:
        raise ValueError(f'invalid disposition: {new_disposition}')

    current = evaluate_compliance_case(case_id)
    prior = current.disposition
    if _DISPOSITION_RANK[new_disposition] < _DISPOSITION_RANK[prior] and reviewer_role != 'SUPERVISOR':
        raise UnauthorizedReviewAction(
            f'downgrading disposition from {prior} to {new_disposition} requires SUPERVISOR role')

    log = _REVIEW_LOG.setdefault(case_id, [])
    decision = ReviewDecision(
        decision_id=f'{case_id}-REV-{len(log)+1}', case_id=case_id,
        reviewer_id=reviewer_id, reviewer_role=reviewer_role,
        timestamp=datetime.now(timezone.utc).isoformat(),
        prior_disposition=prior, new_disposition=new_disposition, rationale=rationale,
        case_policy_version=current.policy_version, case_evidence_lineage=current.evidence_lineage,
    )
    log.append(decision)
    return decision

def list_review_decisions(case_id: str) -> list[ReviewDecision]:
    return list(_REVIEW_LOG.get(case_id, []))
