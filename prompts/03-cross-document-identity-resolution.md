# Prompt 03 — Cross-Document Identity Resolution (CH-03)

## Prerequisite
Prompts 00–02 complete. This prompt consumes the confidence/provenance fields Prompt 02
attached to extracted evidence.

## Section 2 fill-in
- **Engineering transformation:** Cross-Document Identity Resolution
- **Problem to solve:** Names, initials, transliteration, punctuation, OCR corruption,
  address variations and inconsistent dates of birth create contradictory identity records
  across a case's documents; `src/identity.py` must be checked for whether it does any real
  reconciliation or just takes the last/first document's fields.
- **Desired production outcome:** Passport, PAN, Aadhaar, DL or other synthetic document
  evidence for one case is reconciled into a single normalized identity, with the
  match/mismatch evidence for each field retained (not just the final merged value).
- **Business/risk consequence:** Fragmented customer profiles (one real person split into
  two case records) hide aggregate transactional risk; incorrectly merged profiles (two
  people treated as one) contaminate monitoring with someone else's activity.

## Repo grounding
- `challenges/CH-03.md`, row 3 of `docs/15_integrated_engineering_challenges.md`
- Register questions 5–8 in `docs/engineering_challenge_register.md` (identity consistency)
- Evidence: `data/` for **CASE-005** — inspect every document in that case's
  `data/input_documents/` and `data/ground_truth/` for the specific name/DOB variant it's
  designed to exercise
- Code: `src/identity.py`
- Specs: `specs/02_features/IDENTITY_RESOLUTION.md`
- Tests: `tests/test_integrated_compliance.py`

## Suggested change boundary
- In scope: `src/identity.py` matching/normalization logic, new synthetic adversarial
  documents under `data/input_documents/` (transliteration, punctuation, OCR-corrupted
  name variants, mismatched DOB) with matching `data/ground_truth/` entries, matching
  golden/edge cases in `evals/golden_cases.json`.
- Out of scope: OCR extraction itself (Prompt 02), the canonical linkage key mechanism
  (Prompt 01) — this prompt assumes a key exists and focuses on whether the *evidence
  feeding* that key is correctly reconciled.

## STOP conditions
1. Complete CLAUDE.md §3 and §15 before writing matching logic. State explicitly: does a
   matching date of birth compensate for a name mismatch, and under what documented policy
   (register question 7) — do not encode an undocumented threshold; if none exists, record
   an assumption under `specs/09_change_requests/`.
2. Add adversarial/edge test cases (transliteration, corrupted OCR, address variation)
   before adjusting any matching threshold, per `docs/workshop_challenge_map.md` step 4.
3. Follow CLAUDE.md §22 in order and close with §24.
