# Backlog — Improvements & Change Requests

Running list of findings surfaced while working the 15-challenge prompt series
(`prompts/00`–`16`) that were out of scope for the prompt that found them. Reviewed
periodically, not automatically actioned — many items may turn out to be resolved as a
side effect of a later numbered prompt before they need separate work.

## How this is used

- **Type** — `Improvement` (non-blocking hardening/cleanup, safe smallest-change fix
  whenever picked up) or `Change Request` (needs a policy decision before it can be
  implemented, per `AGENTS.md` step 4 — do not guess at these).
- **Status** — `Open` / `Resolved (Prompt N)` / `Deferred` / `Superseded`.
- Every item is sourced from a specific prompt's forensics or results file so it can be
  traced back to why it was raised.
- When a later prompt turns out to resolve an item as a side effect, mark it
  `Resolved (Prompt N)` in the same commit that lands that prompt, with a one-line note —
  don't leave it silently stale.

## Index

| ID | Type | Source | Title | Status |
| --- | --- | --- | --- | --- |
| BL-001 | Change Request | Prompt 01 | Document-id-to-case-id linkage is unvalidated | Open |
| BL-002 | Improvement | Prompt 02 | `UNREADABLE_GLYPHS` count is silently discarded by the parser | Open |
| BL-003 | Improvement | Prompt 02 | Duplicate/inconsistent OCR-quality warning codes | Open |

## BL-001 — Document-id-to-case-id linkage is unvalidated

- **Type:** Change Request
- **Source:** Prompt 01 (`results/01-identity-to-transaction-entity-linkage.md`, Remaining
  Risks)
- **Status:** Open
- **Description:** A document's association with a case (e.g. `CASE-005-PASSPORT` belonging
  to `CASE-005`) is enforced only by a string-prefix naming convention, never asserted in
  code. There is no independent ground-truth field on a document/ground-truth record that
  states which case it belongs to, so there's nothing to validate against without adding
  one.
- **Why deferred:** Fixing this without a real ground-truth field would mean inventing a
  policy (CLAUDE.md: "do not fabricate APIs, schemas, files or dependencies"). It likely
  needs a data-model addition — e.g. an explicit `case_id` field on document/ground-truth
  records — which is a broader change than the transaction-side fix Prompt 01 was scoped to.
- **Suggested next step:** Raise a formal change request under
  `specs/09_change_requests/` (using `CR_TEMPLATE.md`) if/when this is picked up, since it
  affects the data contract, not just application code.

## BL-002 — `UNREADABLE_GLYPHS` count is silently discarded by the parser

- **Type:** Improvement
- **Source:** Prompt 02 forensics
- **Status:** Open
- **Description:** `data/sidecar_ocr/CASE-002-*.txt` carries a line `UNREADABLE_GLYPHS: 4` —
  a real, quantifiable OCR-quality signal. `src/parser.py`'s `parse_legacy_ocr` explicitly
  excludes `UNREADABLE_GLYPHS:` lines from both field extraction and the
  `UNPARSED_LINE:` warning fallback, so the count reaches no field, no warning, and no
  downstream consumer. Prompt 02 propagates the *existing* `DEGRADED_OCR_QUALITY`/
  `OCR_QUALITY_DEGRADED` boolean-style warnings into `IdentityProfile.confidence`, but does
  not recover this finer-grained count.
- **Why deferred:** Out of Prompt 02's approved scope (which targeted signals that already
  reach `DocumentResult`, not new parser extraction). Recovering it would need a new parsed
  field and a decision on how a glyph count should scale a confidence penalty — a small but
  distinct design step.
- **Suggested next step:** Pick up alongside a future confidence-model refinement, or fold
  into Prompt 15 (evals/observability) as an evidence-fidelity gap to test for.

## BL-003 — Duplicate/inconsistent OCR-quality warning codes

- **Type:** Improvement
- **Source:** Prompt 02 forensics
- **Status:** Open
- **Description:** The same degraded-quality condition currently produces two
  differently-named warnings on the same `DocumentResult`: `DEGRADED_OCR_QUALITY` (from
  `src/parser.py:17`) and `OCR_QUALITY_DEGRADED` (from `src/rules.py:29`). Likewise
  `ROTATED_CAPTURE` (parser) vs. `ROTATED_DOCUMENT` (rules). Both pairs fire together for
  the same input, which is redundant and easy to miss when someone greps for "the" warning
  code.
- **Why deferred:** Consolidating them touches both `src/parser.py` and `src/rules.py`, is
  pure cleanup unrelated to any single challenge, and — since nothing currently asserts on
  the exact warning-code strings — carries a small chance of surprising a future prompt that
  starts relying on one of the two names. Prompt 02 accounted for both names explicitly in
  its `QUALITY_WARNING_CODES` set instead of picking one, to stay correct without touching
  this.
- **Suggested next step:** A small standalone cleanup prompt/PR once no in-flight prompt
  still depends on the current dual-naming.
