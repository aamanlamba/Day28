# Results — Prompt 02: Document-Intelligence Uncertainty Propagation (CH-02)

**Prompt run:** `prompts/02-document-intelligence-uncertainty-propagation.md` (unmodified)
**Date:** 2026-09-11
**Requirements:** CH-02 (`docs/15_integrated_engineering_challenges.md` row 2)
**Approved plan:** current-state finding, root cause and design were reported in-session and
approved before any code was written (per the prompt's own STOP gate).

## 1. Problem Diagnosed

`IdentityProfile.confidence` was computed purely from the case's *decision outcome*
(`identity_status`), never from the *evidence quality* that produced it. A document with
perfect field completeness and one with `OCR_QUALITY: DEGRADED` could receive an identical
confidence score.

## 2. Current-State Findings

- Real, quantifiable quality signals already reach `DocumentResult`:
  `completeness` (`src/rules.py:12-13`, a real 0–1 ratio) and `warnings` — two differently
  named pairs for the same conditions: `DEGRADED_OCR_QUALITY`/`ROTATED_CAPTURE`
  (`src/parser.py:17-18`) and `OCR_QUALITY_DEGRADED`/`ROTATED_DOCUMENT`
  (`src/rules.py:29-30`).
- `src/identity.py`'s `build_identity_profile` already holds `base.documents` (each a full
  `DocumentResult`) but never read `.completeness` or `.warnings` from them before this
  change — confidence was a pure function of `identity_status`.
- Confirmed via `data/sidecar_ocr/CASE-002-*.txt`: both documents carry
  `OCR_QUALITY: DEGRADED` and `UNREADABLE_GLYPHS: 4`. The glyph count is silently dropped by
  `src/parser.py` (excluded from both field extraction and the `UNPARSED_LINE:` fallback) —
  logged as backlog item BL-002, not fixed here (out of this prompt's approved scope, which
  targeted signals that already reach `DocumentResult`).
- Compatibility check: `/v1`'s `DocumentResult` already exposes `completeness` and
  `warnings` in its response today — this was a pure `/v2`-side consumption gap, not a
  `/v1` compatibility problem. No `/v1` change made or needed.
- `grep` for `.confidence` across `tests/`, `evals/`, `data/expected_baseline_outputs/`,
  `specs/` returned nothing — no exact confidence value is asserted anywhere, confirming low
  regression risk for changing the formula.
- Only `CASE-002` and `CASE-003` sidecars carry quality-degradation markers, and neither is
  used by any existing `/v2` test — so the new logic needed synthetic tests (via
  `monkeypatch`, same technique as Prompt 01) rather than a new `data/` fixture.

## 3. Root Cause

Confidence was derived from `identity_status` alone; the function had the per-document
quality data in scope (`base.documents[i].completeness`, `.warnings`) but never consulted it.

## 4. Architecture / Design Decision

In `src/identity.py`: added `QUALITY_WARNING_CODES` (covering both existing naming variants)
and a documented `QUALITY_DEGRADED_CONFIDENCE_MULTIPLIER = 0.9`. `build_identity_profile`
now computes `quality_flags` (any document warning in that set) and `worst_completeness`
(minimum completeness across the case's documents), adds a new risk flag
`DOCUMENT_QUALITY_DEGRADED` when quality flags are present, and folds both into the existing
confidence calculation — multiplying by `0.9` when quality is flagged and always multiplying
by `worst_completeness`. Both are deterministic post-processing over already-extracted
facts; no probabilistic/LLM component is involved, and no new schema field was needed —
`confidence` and `risk_flags` already existed and are exactly the right shape for this
signal.

## 5. Files Changed

- `src/identity.py` — quality-aware confidence calculation (7 lines added, 1 line changed).
- `tests/test_integrated_compliance.py` — added `DocumentResult`/`CaseResult` import and two
  new tests.

No files added. No schema, spec, or `/v1` change.

## 6. Implementation Summary

`build_identity_profile` now reduces `confidence` on two independent axes: a documented
multiplier when any source document carries an OCR-quality warning (flagged visibly via
`DOCUMENT_QUALITY_DEGRADED`), and proportionally to the worst per-document field
completeness in the case — even when the decision outcome itself remains `VERIFIED`.

## 7. Data / Schema Changes

None. `confidence: float` and `risk_flags: list[str]` already existed on `IdentityProfile`.

## 8. Tests Added

- `test_identity_confidence_penalized_by_document_quality_warning` — synthetic case (via
  `monkeypatch` on `src.identity.verify_case`) with one clean document and one
  `DEGRADED_OCR_QUALITY`-warned document; asserts the new risk flag and confidence below the
  plain REVIEW-status baseline (0.70).
- `test_identity_confidence_penalized_by_incomplete_document_even_when_verified` — synthetic
  case, both documents `APPROVE`, one with `completeness=0.75` and no warnings; asserts
  `identity_status == 'VERIFIED'` but confidence below 0.97 — proving the completeness
  dimension works independently of the warning dimension.

## 9. Test Results

| Command | Exit | Result |
| --- | --- | --- |
| Both new tests (before fix) | 1 | Failed as expected: `DOCUMENT_QUALITY_DEGRADED` absent; `0.97 < 0.97` false |
| Both new tests (after fix) | 0 | Passed |
| `pytest -q` (full suite) | 0 | `35 passed, 1 warning in 0.17s` (was 33; +2 new tests, zero regressions) |
| `workshop_preflight.py` | 0 | `PREFLIGHT PASSED` |
| `sanity_check.py` | 0 | `SANITY CHECK PASSED` — case/document/challenge counts unchanged |
| `run_integrated_evals.py` | 0 | `{"status": "PASS", "failures": []}` |
| `smoke_server.py` | 0 | `SMOKE SERVER PASSED` |

## 10. Edge Cases Covered

- Quality-warned document with an otherwise-passing sibling document (warning-driven
  penalty, status already REVIEW).
- Incomplete document with no warnings and an otherwise-`VERIFIED` status
  (completeness-driven penalty, isolated from the warning path).
- Both existing dimensions (`identity_status`-driven baseline, cross-document name/DOB
  mismatch) verified unchanged by the full regression run.

Not covered in this pass (explicitly out of scope): recovering the `UNREADABLE_GLYPHS`
count (BL-002), consolidating the duplicate warning-code names (BL-003), cross-document
name/DOB matching internals (Prompt 03).

## 11. Security / Privacy Impact

None. No new external input surface; the new logic reads already-validated in-memory fields
(`completeness`, `warnings`) and adds no new logging of sensitive content — only a fixed
flag string (`DOCUMENT_QUALITY_DEGRADED`), consistent with existing risk-flag patterns.

## 12. Observability Added

Confidence now visibly reflects evidence quality, and `DOCUMENT_QUALITY_DEGRADED` is a new,
audit-traceable risk flag distinguishing "decision outcome was fine but evidence was weak"
from every other flag already on `IdentityProfile.risk_flags`.

## 13. Compatibility Assessment

Fully additive. `/v1` untouched. `/v2` `IdentityProfile` schema unchanged (reusing existing
fields). No existing fixture combines "used by a `/v2` test" with "quality-degraded," so no
existing test's expected output changed — confirmed by the full regression suite (33
pre-existing tests unchanged, 2 new tests added, all green).

## 14. Remaining Risks / Assumptions

- `0.9` and the completeness multiplication are documented engineering heuristics, not
  calibrated probabilities — consistent with the pre-existing 0.97/0.70/0.20 constants and
  with `docs/known_limitations.md`'s own acknowledgment of this. This pass stops evidence
  from being *discarded*; it does not claim to make confidence a calibrated probability.
- Backlog items opened during this pass, not fixed: BL-002 (glyph-count signal discarded by
  the parser) and BL-003 (duplicate OCR-quality warning-code naming) — see `backlog.md`.

## 15. Production-Readiness Verdict

**READY WITH CONDITIONS** — the implemented fix is safe, tested, and backward-compatible.
Conditions: BL-002 and BL-003 should be picked up before CH-02 is considered fully closed;
neither blocks this increment.
