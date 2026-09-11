from __future__ import annotations
from pathlib import Path
from datetime import date
import json, re, sys
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.repository import list_cases, list_integrated_cases, load_ground_truth, load_sidecar
from src.service import verify_case
from src.compliance import evaluate_compliance_case

errors=[]
def err(x): errors.append(x)
def readj(p):
    try: return json.loads(p.read_text(encoding='utf-8'))
    except Exception as e: err(f'invalid JSON {p.relative_to(ROOT)}: {e}'); return {}

legacy=list_cases(); all_cases=list_integrated_cases()
if len(legacy)!=6: err(f'legacy /v1 contract expected 6 cases, found {len(legacy)}')
if len(all_cases)!=12: err(f'integrated dataset expected 12 cases, found {len(all_cases)}')

# legacy regression snapshots must remain exact
legacy_ids={x['case_id'] for x in legacy}
snapshots={p.stem for p in (ROOT/'data/expected_baseline_outputs').glob('*.json')}
if snapshots != legacy_ids: err(f'legacy baseline snapshots mismatch: {sorted(snapshots)} vs {sorted(legacy_ids)}')
for c in legacy:
    cid=c['case_id']
    expected=readj(ROOT/'data/expected_baseline_outputs'/f'{cid}.json')
    actual=verify_case(cid).model_dump(mode='json')
    if actual != expected: err(f'legacy expected output drift: {cid}')

# all identity documents must be executable and have decodable images + required lineage fields
referenced=[]
for c in all_cases:
    cid=c.get('case_id','')
    if not re.fullmatch(r'CASE-\d{3}',cid): err(f'invalid case id {cid}')
    for did in c.get('document_ids',[]):
        referenced.append(did)
        try: verify_case(cid)
        except Exception as e: err(f'identity flow failed {cid}: {e}')
        for folder,suffix in [('input_documents','.png'),('sidecar_ocr','.txt'),('ground_truth','.json')]:
            p=ROOT/'data'/folder/f'{did}{suffix}'
            if not p.exists(): err(f'missing {p.relative_to(ROOT)}')
        ip=ROOT/'data/input_documents'/f'{did}.png'
        if ip.exists():
            try:
                with Image.open(ip) as im: im.verify()
            except Exception as e: err(f'invalid image {did}: {e}')
        gp=ROOT/'data/ground_truth'/f'{did}.json'
        if gp.exists():
            gt=readj(gp)
            if gt.get('document_id') != did: err(f'ground truth document mismatch {did}')
            if gt.get('case_id') != cid: err(f'ground truth case mismatch {did}')
        sp=ROOT/'data/sidecar_ocr'/f'{did}.txt'
        if sp.exists():
            s=load_sidecar(did)
            if 'DOCUMENT TYPE:' not in s or 'DOCUMENT NO:' not in s: err(f'invalid sidecar {did}')

# integrated monitoring data must exist for every case and execute
for c in all_cases:
    cid=c['case_id']
    tp=ROOT/'data/transactions'/f'{cid}.json'
    if not tp.exists(): err(f'missing transaction fixture {cid}')
    try: evaluate_compliance_case(cid)
    except Exception as e: err(f'integrated compliance flow failed {cid}: {e}')

# no orphan document artifacts relative to all integrated applications
for folder,suffix in [('input_documents','.png'),('sidecar_ocr','.txt'),('ground_truth','.json')]:
    found={p.stem for p in (ROOT/'data'/folder).glob(f'*{suffix}')}
    if found != set(referenced): err(f'document artifact set mismatch in {folder}')

required=[ROOT/'docs/15_integrated_engineering_challenges.md', ROOT/'docs/integrated_architecture.md', ROOT/'evals/golden_cases.json']
for p in required:
    if not p.exists(): err(f'missing required artifact {p.relative_to(ROOT)}')
if len(list((ROOT/'challenges').glob('CH-*.md'))) != 15: err('expected exactly 15 challenge cards')

if errors:
    print('SANITY CHECK FAILED')
    for e in errors: print('-',e)
    raise SystemExit(1)
print(f'SANITY CHECK PASSED: 6 legacy cases preserved, 12 integrated cases executable, {len(referenced)} document artifacts validated, 15 challenge cards present')
