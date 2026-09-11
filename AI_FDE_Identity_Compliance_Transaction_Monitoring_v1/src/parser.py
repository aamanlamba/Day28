PREFIXES={
'DOCUMENT TYPE:':'document_type','NAME:':'full_name','DOB:':'date_of_birth',
'DOCUMENT NO:':'document_number','ISSUE DATE:':'issue_date','EXPIRY DATE:':'expiry_date',
'ADDRESS:':'address','NATIONALITY:':'nationality'
}

def parse_legacy_ocr(text: str) -> tuple[dict,list[str]]:
    fields={}; warnings=[]
    for raw in text.splitlines():
        line=raw.strip()
        matched=False
        for prefix,key in PREFIXES.items():
            if line.startswith(prefix):
                fields[key]=line[len(prefix):].strip(); matched=True; break
        if not matched and ':' in line and not line.startswith(('OCR_QUALITY:','UNREADABLE_GLYPHS:','CAPTURE_ORIENTATION:','SECURITY NOTE:')):
            warnings.append(f'UNPARSED_LINE:{line[:40]}')
    # BL-003: DEGRADED_OCR_QUALITY/ROTATED_CAPTURE here are intentional synonyms of
    # rules.py's OCR_QUALITY_DEGRADED/ROTATED_DOCUMENT for the same two conditions.
    # Both pairs are baked into the locked /v1 golden snapshots for CASE-002/CASE-003
    # (KYC-COMP-002), so neither can be removed without an approved, recorded /v1
    # behavior change - decided to document rather than touch. /v2's identity.py
    # already checks for both names via QUALITY_WARNING_CODES, so this causes no
    # functional harm, only a minor human-readability cost.
    if 'OCR_QUALITY: DEGRADED' in text: warnings.append('DEGRADED_OCR_QUALITY')
    if 'CAPTURE_ORIENTATION: 90_DEGREES' in text: warnings.append('ROTATED_CAPTURE')
    return fields,warnings

def extract_unreadable_glyph_count(text: str) -> int | None:
    """BL-002: recovers the UNREADABLE_GLYPHS signal that parse_legacy_ocr silently
    discards. Kept as a separate function (not folded into parse_legacy_ocr's
    warnings) because DocumentResult.warnings is part of the locked /v1 contract -
    KYC-COMP-002 requires CASE-001..006's regression snapshots to stay byte-identical,
    and CASE-002 is exactly the fixture that carries this line. Callers needing this
    signal (currently only /v2's identity.py) call it separately."""
    for raw in text.splitlines():
        line=raw.strip()
        if line.startswith('UNREADABLE_GLYPHS:'):
            try:
                return int(line[len('UNREADABLE_GLYPHS:'):].strip())
            except ValueError:
                return None
    return None
