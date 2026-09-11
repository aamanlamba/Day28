import re
from datetime import datetime
from difflib import SequenceMatcher
from .service import verify_case
from .repository import load_json, load_ground_truth
from .ocr import extract_text
from .parser import extract_unreadable_glyph_count
from .models_v2 import IdentityProfile, FieldConflict

QUALITY_WARNING_CODES = {'DEGRADED_OCR_QUALITY', 'OCR_QUALITY_DEGRADED', 'ROTATED_CAPTURE', 'ROTATED_DOCUMENT'}
QUALITY_DEGRADED_CONFIDENCE_MULTIPLIER = 0.9  # CH-02: documented heuristic, not a calibrated probability
DOB_FORMATS = ('%Y-%m-%d', '%d/%m/%Y')

def _norm_name(v: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (v or "").lower())

def _name_similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, _norm_name(a), _norm_name(b)).ratio()

def _tokenize_name(v: str) -> list[str]:
    return [t for t in re.split(r'[^a-zA-Z0-9]+', v or '') if t]

def _tokens_compatible(a: str, b: str) -> bool:
    a, b = a.lower(), b.lower()
    if a == b:
        return True
    if len(a) == 1 and len(b) > 1:
        return b[0] == a
    if len(b) == 1 and len(a) > 1:
        return a[0] == b
    return False

def _names_match_allowing_initials(a: str, b: str) -> bool:
    """BL-005: an initial standing in for a full first name (e.g. "J Smith" vs.
    "John Smith") is not a genuine mismatch, provided every other name token still
    matches exactly. Requires equal token counts - a dropped/added name entirely
    (not just abbreviated) falls through to the ordinary similarity check instead,
    since that's a materially different, less certain case not covered by this fix."""
    ta, tb = _tokenize_name(a), _tokenize_name(b)
    if not ta or len(ta) != len(tb):
        return False
    return all(_tokens_compatible(x, y) for x, y in zip(ta, tb))

def _normalize_dob(v: str):
    """CH-03: compare dates of birth by value, not by literal string, so a document
    expressing the same date in a different valid format isn't flagged as a conflict.
    An unparseable value falls back to the raw string so it still compares (and can
    still mismatch) rather than being silently ignored."""
    for fmt in DOB_FORMATS:
        try:
            return datetime.strptime(v, fmt).date()
        except ValueError:
            continue
    return v

def build_identity_profile(case_id: str) -> IdentityProfile:
    base = verify_case(case_id)
    try:
        ctx = load_json('customer_context', case_id)
    except FileNotFoundError:
        ctx = {}
    name_pairs=[(d.document_id, d.parsed_fields.get('full_name')) for d in base.documents if d.parsed_fields.get('full_name')]
    dob_pairs=[(d.document_id, d.parsed_fields.get('date_of_birth')) for d in base.documents if d.parsed_fields.get('date_of_birth')]
    names=[v for _, v in name_pairs]
    dobs=[v for _, v in dob_pairs]
    nationalities=[d.parsed_fields.get('nationality') for d in base.documents if d.parsed_fields.get('nationality')]
    flags=[]
    field_conflicts=[]  # BL-006: per-field, per-document evidence behind a mismatch flag
    status='VERIFIED'
    if base.decision == 'REJECT':
        status='REJECTED'; flags.append('IDENTITY_DOCUMENT_REJECTED')
    elif base.decision == 'REVIEW':
        status='REVIEW'; flags.append('IDENTITY_DOCUMENT_REVIEW')
    if len(names) > 1:
        min_sim=min(_name_similarity(names[0], n) for n in names[1:])
        if min_sim < 0.92 and not all(_names_match_allowing_initials(names[0], n) for n in names[1:]):
            status='REVIEW' if status == 'VERIFIED' else status
            flags.append('CROSS_DOCUMENT_NAME_MISMATCH')
            field_conflicts.extend(FieldConflict(field='full_name', document_id=doc_id, value=v) for doc_id, v in name_pairs)
    if len({_normalize_dob(d) for d in dobs}) > 1:
        status='REVIEW' if status == 'VERIFIED' else status
        flags.append('CROSS_DOCUMENT_DOB_MISMATCH')
        field_conflicts.extend(FieldConflict(field='date_of_birth', document_id=doc_id, value=v) for doc_id, v in dob_pairs)
    # BL-001: a document evidencing a different case must not be silently aggregated
    # into this identity - a false-join risk, not merely a quality/consistency issue.
    # A document with no ground-truth record at all is unverifiable, not a confirmed
    # mismatch, so it's skipped rather than flagged or treated as a hard failure.
    def _linked_to_wrong_case(document_id: str) -> bool:
        try:
            return load_ground_truth(document_id).get('case_id') != case_id
        except FileNotFoundError:
            return False
    if any(_linked_to_wrong_case(d.document_id) for d in base.documents):
        status='REVIEW' if status == 'VERIFIED' else status
        flags.append('DOCUMENT_CASE_LINKAGE_MISMATCH')
    if ctx.get('kyc_refresh_due'):
        flags.append('KYC_REFRESH_DUE')
        if status == 'VERIFIED': status='REVIEW'
    expected_turnover = ctx.get('expected_monthly_turnover')
    if expected_turnover is None:
        # CH-05: a missing expected-activity baseline silently disables the
        # monitoring-side deviation check; make the gap visible instead.
        flags.append('EXPECTED_ACTIVITY_BASELINE_MISSING')
    # CH-02: evidence quality (not just decision outcome) must reduce confidence, so
    # downstream monitoring can distinguish trusted from disputed KYC facts.
    quality_flags = {w for d in base.documents for w in d.warnings if w in QUALITY_WARNING_CODES}
    worst_completeness = min((d.completeness for d in base.documents), default=1.0)
    confidence = 0.97 if status=='VERIFIED' else (0.70 if status=='REVIEW' else 0.20)
    if quality_flags:
        flags.append('DOCUMENT_QUALITY_DEGRADED')
        confidence *= QUALITY_DEGRADED_CONFIDENCE_MULTIPLIER
    confidence = round(confidence * worst_completeness, 3)
    # BL-002: recovers the UNREADABLE_GLYPHS count that parse_legacy_ocr silently
    # discards, without touching /v1's locked DocumentResult.warnings (KYC-COMP-002).
    # Informational only, like DOCUMENT_QUALITY_DEGRADED - no separate confidence
    # penalty, since how a glyph count should scale one is an undecided policy question.
    def _has_unreadable_glyphs(document_id: str) -> bool:
        try:
            return bool(extract_unreadable_glyph_count(extract_text(document_id)))
        except FileNotFoundError:
            return False
    if any(_has_unreadable_glyphs(d.document_id) for d in base.documents):
        flags.append('OCR_GLYPH_QUALITY_DEGRADED')
    canonical = ctx.get('canonical_name') or (names[0] if names else None)
    return IdentityProfile(
        case_id=case_id, canonical_name=canonical, date_of_birth=(dobs[0] if dobs else None),
        residency_country=ctx.get('residency_country'), nationality=ctx.get('nationality') or (nationalities[0] if nationalities else None),
        occupation=ctx.get('occupation'), expected_monthly_turnover=expected_turnover,
        identity_status=status, confidence=confidence, risk_flags=sorted(set(flags)),
        evidence_refs=[f'document:{d.document_id}' for d in base.documents],
        field_conflicts=field_conflicts,
    )
