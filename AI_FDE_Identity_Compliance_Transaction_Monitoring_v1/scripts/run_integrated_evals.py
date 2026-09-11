import json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.compliance import evaluate_compliance_case
from src.monitoring import evaluate_transactions
from src.review import submit_review_decision, UnauthorizedReviewAction

golden=json.loads((ROOT/'evals/golden_cases.json').read_text())['cases']
failed=[]

# --- Golden cases: known-outcome regression gate covering every /v2 capability built in
# Prompts 01-14 (identity linkage, confidence propagation, cross-document resolution, KYC
# freshness, expected-activity baseline, idempotency, temporal ordering, structuring,
# velocity, corridor fusion, pass-through). ---
for cid,expect in golden.items():
    r=evaluate_compliance_case(cid)
    alerts={a.pattern_code for a in r.monitoring.alerts}
    warnings=set(r.monitoring.hook_warnings)
    risk_flags=set(r.identity.risk_flags)
    if expect.get('expected_disposition') and r.disposition != expect['expected_disposition']:
        failed.append(f'{cid}: expected disposition {expect["expected_disposition"]}, got {r.disposition}')
    if expect.get('expected_identity_status') and r.identity.identity_status != expect['expected_identity_status']:
        failed.append(f'{cid}: expected identity_status {expect["expected_identity_status"]}, got {r.identity.identity_status}')
    if not set(expect.get('must_alert',[])).issubset(alerts):
        failed.append(f'{cid}: missing alert(s) {set(expect.get("must_alert",[]))-alerts}')
    if not set(expect.get('must_warn',[])).issubset(warnings):
        failed.append(f'{cid}: missing warning(s) {set(expect.get("must_warn",[]))-warnings}')
    if not set(expect.get('must_have_risk_flag',[])).issubset(risk_flags):
        failed.append(f'{cid}: missing risk flag(s) {set(expect.get("must_have_risk_flag",[]))-risk_flags}')

# --- Outage / failure-recovery check (CLAUDE.md §17): an unknown case must fail in a
# controlled way, never crash unhandled. ---
try:
    evaluate_compliance_case('CASE-DOES-NOT-EXIST')
    failed.append('outage-check: unknown case did not raise')
except FileNotFoundError:
    pass
except Exception as e:
    failed.append(f'outage-check: unexpected exception type {type(e).__name__}')

# --- Metamorphic check (CLAUDE.md §17 / CH-14): replaying a case against its own
# recorded policy_version must reproduce an identical result. ---
replay_base=evaluate_transactions('CASE-007')
replay_again=evaluate_transactions('CASE-007', policy_version=replay_base.policy_version)
if replay_again.model_dump() != replay_base.model_dump():
    failed.append('metamorphic-check: policy replay did not reproduce an identical result')

# --- Adversarial check (CLAUDE.md §17 / CH-13): an unauthorized HITL downgrade must be
# rejected, confirming the authorization boundary is active in this build. ---
try:
    submit_review_decision('CASE-004', reviewer_id='eval-harness', reviewer_role='ANALYST',
                            new_disposition='CLEAR', rationale='eval harness probe')
    failed.append('adversarial-check: unauthorized downgrade was not rejected')
except UnauthorizedReviewAction:
    pass

print(json.dumps({'status':'PASS' if not failed else 'FAIL','failures':failed},indent=2))
raise SystemExit(1 if failed else 0)
