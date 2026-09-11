# ADR-002 — Initials-Aware Cross-Document Name Matching

**Status:** Accepted
**Date:** 2026-09-11
**Requirements:** KYC-FR-004; `backlog.md` BL-005

## Context

`challenges/CH-03.md`'s stated friction explicitly names initials (e.g. "J. Smith" vs.
"John Smith") as a source of cross-document name variation that identity resolution should
handle. The existing matcher (`SequenceMatcher` similarity over the whole normalized name
string, 0.92 threshold) has no initials-aware logic — an initial standing in for a full
first name scores well below the threshold and is flagged as a full
`CROSS_DOCUMENT_NAME_MISMATCH`, even when the surname matches exactly and the pattern is
clearly an abbreviation, not a conflict.

## Decision

Add a token-level exception check (`_names_match_allowing_initials` in `src/identity.py`),
consulted only when the existing whole-string similarity check would already flag a
mismatch:

1. Tokenize both names on non-alphanumeric characters (spaces, periods, hyphens).
2. Require **equal token counts** between the two names — a dropped or added name token
   entirely (not just abbreviated) is a materially different, less certain case and is
   **not** covered by this exception; it falls through to the existing mismatch behavior.
3. For each token pair at the same position: an exact case-insensitive match is compatible;
   a single-letter token is compatible with a multi-letter token if the multi-letter
   token's first character matches the single letter.
4. If every token pair is compatible under these rules, the names are treated as
   consistent — no `CROSS_DOCUMENT_NAME_MISMATCH` flag, `identity_status` unaffected by
   this check.

This only ever *relaxes* an existing mismatch determination for the specific
initial-vs-full-name shape; it never overrides a genuine mismatch (different surname,
different token count, or a name variant that isn't a clean initial substitution).

## Alternatives considered

1. **Lower the overall similarity threshold** (e.g. to 0.80) so initials score high enough
   to pass. Rejected: this would also raise the false-negative rate for genuinely different
   names of similar length/shape (e.g. OCR-corrupted names, which this repo's CASE-005
   fixture specifically exercises) — the whole-string threshold isn't the right lever for a
   token-shaped problem.
2. **Route initial-vs-full-name to a distinct "uncertain" reason code and still require
   REVIEW** rather than clearing it outright. Considered and available as a future
   refinement, but the user's decision was to treat a matching-surname initial as a clean
   match, not merely a softer mismatch, since the pattern is unambiguous when the surname
   agrees exactly.
3. **Do nothing** (leave BL-005 open). Rejected per the user's explicit decision to resolve
   it now.

## Consequences

- **Positive:** closes a real, named gap from the challenge brief without weakening
  detection of genuine name conflicts (verified via `test_initial_with_different_surname_is_still_a_mismatch`
  and the unchanged CASE-005 test).
- **Negative / residual risk:** a token-count-preserving abbreviation is the only pattern
  covered. Middle-name drops, hyphenated-surname variants, and transliteration remain
  unhandled (transliteration is separately confirmed out of scope per
  `specs/02_features/IDENTITY_RESOLUTION.md`). A single shared initial with a matching
  surname is treated as sufficient evidence of consistency — this is a deliberate,
  documented risk acceptance, not an oversight: two different people who share both a
  surname and a first-initial (e.g. siblings) could theoretically be under-flagged, but no
  current fixture exercises this and the user accepted this trade-off explicitly.
- **Operational:** no schema change, no new field, no `/v1` impact — pure logic addition to
  `src/identity.py`.

## Verification

- `tests/test_integrated_compliance.py::test_initial_vs_full_first_name_is_not_a_mismatch_when_surname_matches`
  — "John Smith" vs. "J Smith" → no mismatch flag, `identity_status` stays `VERIFIED`.
- `tests/test_integrated_compliance.py::test_initial_with_different_surname_is_still_a_mismatch`
  — "John Smith" vs. "J Jones" → mismatch flag still raised.
- `tests/test_integrated_compliance.py::test_identity_profile_surfaces_cross_document_name_conflict`
  — CASE-005's real OCR-corruption scenario (not an initials case) still flags as before.
- Full regression: 88 passed (was 86 before this fix), preflight/sanity/evals/smoke all
  green.
