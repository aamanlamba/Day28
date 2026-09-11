import json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.compliance import evaluate_compliance_case

golden=json.loads((ROOT/'evals/golden_cases.json').read_text())
failed=[]
for cid,expect in golden.items():
    r=evaluate_compliance_case(cid)
    alerts={a.pattern_code for a in r.monitoring.alerts}
    warnings=set(r.monitoring.hook_warnings)
    if expect.get('expected_disposition') and r.disposition != expect['expected_disposition']:
        failed.append(f'{cid}: disposition {r.disposition}')
    if not set(expect.get('must_alert',[])).issubset(alerts): failed.append(f'{cid}: missing alert')
    if not set(expect.get('must_warn',[])).issubset(warnings): failed.append(f'{cid}: missing warning')
print(json.dumps({'status':'PASS' if not failed else 'FAIL','failures':failed},indent=2))
raise SystemExit(1 if failed else 0)
