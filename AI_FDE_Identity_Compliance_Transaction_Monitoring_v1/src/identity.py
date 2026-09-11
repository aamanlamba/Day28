import re
from difflib import SequenceMatcher
from .service import verify_case
from .repository import load_json
from .models_v2 import IdentityProfile

QUALITY_WARNING_CODES = {'DEGRADED_OCR_QUALITY', 'OCR_QUALITY_DEGRADED', 'ROTATED_CAPTURE', 'ROTATED_DOCUMENT'}
QUALITY_DEGRADED_CONFIDENCE_MULTIPLIER = 0.9  # CH-02: documented heuristic, not a calibrated probability

def _norm_name(v: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (v or "").lower())

def _name_similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, _norm_name(a), _norm_name(b)).ratio()

def build_identity_profile(case_id: str) -> IdentityProfile:
    base = verify_case(case_id)
    try:
        ctx = load_json('customer_context', case_id)
    except FileNotFoundError:
        ctx = {}
    names=[d.parsed_fields.get('full_name') for d in base.documents if d.parsed_fields.get('full_name')]
    dobs=[d.parsed_fields.get('date_of_birth') for d in base.documents if d.parsed_fields.get('date_of_birth')]
    nationalities=[d.parsed_fields.get('nationality') for d in base.documents if d.parsed_fields.get('nationality')]
    flags=[]
    status='VERIFIED'
    if base.decision == 'REJECT':
        status='REJECTED'; flags.append('IDENTITY_DOCUMENT_REJECTED')
    elif base.decision == 'REVIEW':
        status='REVIEW'; flags.append('IDENTITY_DOCUMENT_REVIEW')
    if len(names) > 1:
        min_sim=min(_name_similarity(names[0], n) for n in names[1:])
        if min_sim < 0.92:
            status='REVIEW' if status == 'VERIFIED' else status
            flags.append('CROSS_DOCUMENT_NAME_MISMATCH')
    if len(set(dobs)) > 1:
        status='REVIEW' if status == 'VERIFIED' else status
        flags.append('CROSS_DOCUMENT_DOB_MISMATCH')
    if ctx.get('kyc_refresh_due'):
        flags.append('KYC_REFRESH_DUE')
        if status == 'VERIFIED': status='REVIEW'
    # CH-02: evidence quality (not just decision outcome) must reduce confidence, so
    # downstream monitoring can distinguish trusted from disputed KYC facts.
    quality_flags = {w for d in base.documents for w in d.warnings if w in QUALITY_WARNING_CODES}
    worst_completeness = min((d.completeness for d in base.documents), default=1.0)
    confidence = 0.97 if status=='VERIFIED' else (0.70 if status=='REVIEW' else 0.20)
    if quality_flags:
        flags.append('DOCUMENT_QUALITY_DEGRADED')
        confidence *= QUALITY_DEGRADED_CONFIDENCE_MULTIPLIER
    confidence = round(confidence * worst_completeness, 3)
    canonical = ctx.get('canonical_name') or (names[0] if names else None)
    return IdentityProfile(
        case_id=case_id, canonical_name=canonical, date_of_birth=(dobs[0] if dobs else None),
        residency_country=ctx.get('residency_country'), nationality=ctx.get('nationality') or (nationalities[0] if nationalities else None),
        occupation=ctx.get('occupation'), expected_monthly_turnover=ctx.get('expected_monthly_turnover'),
        identity_status=status, confidence=confidence, risk_flags=sorted(set(flags)),
        evidence_refs=[f'document:{d.document_id}' for d in base.documents],
    )
