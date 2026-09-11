# Results — Prompt 03: Cross-Document Identity Resolution (CH-03)

**Prompt run:** `prompts/03-cross-document-identity-resolution.md` (unmodified)
**Date:** 2026-09-11
**Requirements:** CH-03 (`docs/15_integrated_engineering_challenges.md` row 3); KYC-FR-004
**Approved plan:** current-state finding, root cause and design were reported in-session and
approved before any code was written.

## 1. Problem Diagnosed

DOB comparison in `build_identity_profile` used exact string equality
(`len(set(dobs)) > 1`) with no format tolerance — two documents recording the same date of
birth in different (both valid) formats would be falsely flagged as a cross-document
conflict.

## 2. Current-State Findings

- Name matching (`SequenceMatcher`, 0.92 threshold) and independent name/DOB checks were
  confirmed already correctly implemented for the dataset's actual variation (punctuation,
  OCR corruption) — not touched in this pass.
- DOB format check across the *entire* dataset (`grep -h "^DOB:" data/sidecar_ocr/*.txt`)
  shows every value is ISO `YYYY-MM-DD` — the format-equality bug was 100% latent, exercised
  by no existing fixture.
- **Correction to `backlog.md` BL-001** (unrelated to CH-03, found while reading
  `data/ground_truth/*.json` for this prompt): those files *do* carry a `case_id` field,
  contradicting the original Prompt 01 write-up. The real BL-001 gap is that
  `src/repository.py:load_ground_truth` is defined but never called by verification logic —
  corrected in `backlog.md`, not fixed here (out of scope for both Prompt 01 and this one).
- **Spec-vs-spec conflict found:** `specs/02_features/IDENTITY_RESOLUTION.md` proposes
  reason codes `IDENTITY_NAME_MISMATCH`/`IDENTITY_DOB_MISMATCH`/`IDENTITY_MATCH_UNCERTAIN`;
  `specs/07_acceptance/ACCEPTANCE_CRITERIA.md`'s approved, passing `AC-ID-001` locks in
  `CROSS_DOCUMENT_NAME_MISMATCH`. Not resolved unilaterally — logged as BL-004.
- Register question 7 ("does a matching DOB compensate for a name mismatch?"): confirmed no
  compensation logic exists in either direction; the two checks are fully independent. This
  is being recorded here as an explicit, deliberate decision to **keep** that independence
  (the conservative default) rather than invent compensation logic unsupported by any spec.
- Initials handling and per-field match/mismatch evidence retention were identified as real
  gaps relative to the challenge's stated friction/desired-outcome text, but both require a
  policy decision or a schema-contract change beyond this prompt's scope — logged as BL-005
  and BL-006 rather than implemented.
- Confirmed address matching and transliteration remain explicitly out of scope per
  `specs/02_features/IDENTITY_RESOLUTION.md` ("Initial training scope focuses on
  `full_name` and `date_of_birth`"; "No requirement to solve transliteration in the first
  increment") — not touched.

## 3. Root Cause

DOB values were compared as raw strings rather than parsed to a comparable date value.

## 4. Architecture / Design Decision

Added `_normalize_dob` to `src/identity.py`: tries `%Y-%m-%d` then `%d/%m/%Y`, returning a
`date` object on success. An unparseable value falls back to the raw string so it still
participates in the comparison (and can still mismatch) rather than being silently ignored.
The existing mismatch check now compares normalized values (`{_normalize_dob(d) for d in
dobs}`) instead of raw strings — the flag name, REVIEW behavior, and everything downstream
are unchanged; only the equality test underneath is more correct.

## 5. Files Changed

- `src/identity.py` — added `DOB_FORMATS`, `_normalize_dob`; DOB mismatch check now uses it.
- `tests/test_integrated_compliance.py` — added a shared `_case_with_dobs` helper and two
  new tests.

No files added. No schema, spec, or `/v1` change.

## 6. Implementation Summary

Two documents recording the same date of birth in different valid formats no longer trigger
`CROSS_DOCUMENT_DOB_MISMATCH`. A genuinely different date of birth — even across differing
formats — still triggers it, since the fix only changes *how equality is tested*, not the
mismatch-handling behavior itself.

## 7. Data / Schema Changes

None.

## 8. Tests Added

- `test_dob_comparison_tolerates_equivalent_formats` — `1992-12-08` vs. `08/12/1992`
  (same date); asserts no mismatch flag.
- `test_dob_comparison_still_flags_a_genuine_mismatch_across_formats` — `1992-12-08` vs.
  `09/12/1992` (different date, mixed formats); asserts the flag is still raised.
- Both use a new `_case_with_dobs` test helper + `monkeypatch` on `src.identity.verify_case`
  (same technique as Prompts 01–02), since no real fixture combines format variance with a
  `/v2`-tested case.

## 9. Test Results

| Command | Exit | Result |
| --- | --- | --- |
| `test_dob_comparison_tolerates_equivalent_formats` (before fix) | 1 | Failed as expected: flag present when it shouldn't be |
| `test_dob_comparison_still_flags_a_genuine_mismatch_across_formats` (before fix) | 0 | Already passed (raw-string inequality happens to also flag this case) |
| Both tests + existing `test_identity_profile_surfaces_cross_document_name_conflict` (after fix) | 0 | All 3 passed |
| `pytest -q` (full suite) | 0 | `37 passed, 1 warning in 0.17s` (was 35; +2 new tests, zero regressions) |
| `workshop_preflight.py` | 0 | `PREFLIGHT PASSED` |
| `sanity_check.py` | 0 | `SANITY CHECK PASSED` — counts unchanged |
| `run_integrated_evals.py` | 0 | `{"status": "PASS", "failures": []}` |
| `smoke_server.py` | 0 | `SMOKE SERVER PASSED` |

## 10. Edge Cases Covered

- Same DOB, different valid formats (false-positive prevention).
- Different DOB across formats (false-negative prevention — proves the fix doesn't mask
  real mismatches).
- Unparseable DOB value: falls back to raw-string comparison (documented in the docstring;
  not separately unit-tested since it's equivalent to pre-existing behavior for that case).
- Existing CASE-005 name-mismatch behavior verified unchanged.

Not covered in this pass (explicitly out of scope, logged to backlog): initials/abbreviated
names (BL-005), per-field evidence retention (BL-006), reason-code naming reconciliation
(BL-004).

## 11. Security / Privacy Impact

None. Pure date-parsing logic over already-in-memory, already-validated field values; no new
external input surface, no new logging.

## 12. Observability Added

None new — this pass improves correctness of an existing check rather than adding new
signals (Prompt 02 already added quality-based observability).

## 13. Compatibility Assessment

Fully additive/corrective. `/v1` untouched. `/v2` `IdentityProfile` schema unchanged. No
existing fixture's DOB format varies, so no existing test's expected output changed —
confirmed by the full regression suite (35 pre-existing tests unchanged, 2 new tests added,
all green).

## 14. Remaining Risks / Assumptions

- `DOB_FORMATS` covers ISO and `DD/MM/YYYY` only, chosen because those are the two formats
  plausibly implied by "format variation" — no spec enumerates a required format list. If a
  future document type uses a third format (e.g. `MM/DD/YYYY`), it would currently fall back
  to raw-string comparison (safe — still compares, just not format-tolerant for that case).
- Three items opened to `backlog.md` during this pass, none blocking: BL-004 (reason-code
  naming conflict between specs), BL-005 (no initials-handling policy), BL-006 (per-field
  match/mismatch evidence retention would need an approved schema extension). BL-001 was
  also corrected (not newly opened) based on a finding made while reading ground-truth data
  for this prompt.

## 15. Production-Readiness Verdict

**READY WITH CONDITIONS** — the implemented fix is safe, tested, and backward-compatible.
Conditions: BL-004, BL-005, and BL-006 represent real policy decisions this repo's owner
should make before CH-03 is considered fully closed; none blocks this increment.
