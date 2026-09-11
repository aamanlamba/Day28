# Prompt 02 — Document-Intelligence Uncertainty Propagation (CH-02)

## Prerequisite
Prompt 00 complete. Prompt 01 landed (canonical linkage key exists) — this prompt attaches
confidence/provenance to evidence flowing through that linkage; it does not need Prompt 01's
implementation details, only its resulting `IdentityProfile` shape.

## Section 2 fill-in
- **Engineering transformation:** Document-Intelligence Uncertainty Propagation
- **Problem to solve:** OCR confidence, poor image quality, extraction ambiguity and
  classification uncertainty are lost after parsing — `src/ocr.py` (5 lines) and
  `src/parser.py` (19 lines) return plain extracted values, and `IdentityProfile.confidence`
  in `src/models_v2.py` exists as a field but must be checked for whether it is populated
  from real extraction-quality signals or is a placeholder constant.
- **Desired production outcome:** Confidence, provenance and bounding/quality evidence
  survive from the OCR/parsing seam through to `IdentityProfile` and into every downstream
  decision that depends on identity evidence, so monitoring can distinguish trusted from
  disputed KYC facts.
- **Business/risk consequence:** Treating uncertain OCR output as verified fact lets weak or
  fabricated identity evidence pass through to transaction monitoring unchallenged, which
  undermines the entire KYC-to-monitoring chain regardless of how good the monitoring rules
  are.

## Repo grounding
- `challenges/CH-02.md`, row 2 of `docs/15_integrated_engineering_challenges.md`
- Register questions 1–4 in `docs/engineering_challenge_register.md` (document handling)
- Evidence: `data/` for **CASE-002** and **CASE-005**, plus `data/sidecar_ocr/` and
  `data/input_documents/`
- Code: `src/ocr.py`, `src/parser.py`, `src/identity.py`, `src/models_v2.py`
  (`IdentityProfile.confidence`, `evidence_refs`)
- Specs: `specs/02_features/IDENTITY_RESOLUTION.md`,
  `specs/05_data_contracts/DATA_CONTRACTS.md`
- Tests: `tests/test_service.py` (legacy OCR/parse path), `tests/test_integrated_compliance.py`

## Suggested change boundary
- In scope: `src/ocr.py`, `src/parser.py` (only if confidence/quality signals are being
  dropped there), `src/identity.py`, `src/models_v2.py` if a provenance/quality field is
  genuinely missing.
- Out of scope: `/v1` `DocumentResult`/`CaseResult` contract in `src/models.py` and
  `src/service.py` unless the current-state forensics prove the `/v1` contract already
  exposes (and is silently dropping) a confidence field — if so, treat that as a
  compatibility-affecting finding to flag, not to fix silently.

## STOP conditions
1. Complete CLAUDE.md §3 and §15 and report before implementing.
2. Explicitly separate deterministic post-processing (e.g. thresholding a confidence score)
   from any probabilistic/OCR component, per CLAUDE.md §8/§12 — do not let an LLM or
   probabilistic step make the final accept/reject call.
3. Follow CLAUDE.md §22 in order and close with §24.
