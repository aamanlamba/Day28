from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = [
    'AGENTS.md',
    'SPEC_DRIVEN_DEVELOPMENT.md',
    'CURSOR_WORKFLOW.md',
    'DEFINITION_OF_READY.md',
    'DEFINITION_OF_DONE.md',
    '.cursor/rules/00-sdd-core.mdc',
    '.cursor/rules/10-python-fastapi.mdc',
    '.cursor/rules/20-security-privacy.mdc',
    '.cursor/rules/30-testing-traceability.mdc',
    'specs/00_product/PRD.md',
    'specs/01_system/SYSTEM_REQUIREMENTS.md',
    'specs/02_features/IDENTITY_RESOLUTION.md',
    'specs/03_non_functional/NFR.md',
    'specs/04_security_privacy/SECURITY_PRIVACY.md',
    'specs/05_data_contracts/DATA_CONTRACTS.md',
    'specs/06_api_contracts/API_CONTRACTS.md',
    'specs/07_acceptance/ACCEPTANCE_CRITERIA.md',
    'specs/08_traceability/TRACEABILITY_MATRIX.md',
    'specs/09_change_requests/CR_TEMPLATE.md',
    'tasks/backlog/TASK-001-cross-document-identity-consistency.md',
    'evidence/EVIDENCE_TEMPLATE.md',
]
missing = [p for p in REQUIRED if not (ROOT / p).is_file()]
if missing:
    raise SystemExit('Missing SDD artifacts: ' + ', '.join(missing))
core=(ROOT/'specs/01_system/SYSTEM_REQUIREMENTS.md').read_text(encoding='utf-8')
accept=(ROOT/'specs/07_acceptance/ACCEPTANCE_CRITERIA.md').read_text(encoding='utf-8')
trace=(ROOT/'specs/08_traceability/TRACEABILITY_MATRIX.md').read_text(encoding='utf-8')
for rid in ['KYC-FR-001','KYC-FR-004','KYC-FR-007']:
    if rid not in core or rid not in trace:
        raise SystemExit(f'Traceability check failed for {rid}')
if 'AC-KYC-004' not in accept or 'KYC-FR-004' not in accept:
    raise SystemExit('Target acceptance criterion AC-KYC-004 is missing traceability')
print(f'SDD structure OK: {len(REQUIRED)} required artifacts present; critical IDs traceable.')
