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
| BL-004 | Change Request | Prompt 03 | Reason-code naming conflict: `IDENTITY_RESOLUTION.md` vs. `AC-ID-001` | Open |
| BL-005 | Change Request | Prompt 03 | No handling for initials/abbreviated-name variants | Open |
| BL-006 | Change Request | Prompt 03 | Retain per-field match/mismatch evidence on `IdentityProfile` | Open |
| BL-007 | Change Request | Prompt 05 | `occupation` is captured but consumed by no rule | Open |
| BL-008 | Change Request | Prompt 05 | Expected-counterparty-country baseline field | Open |

## BL-001 — Document-id-to-case-id linkage is unvalidated

- **Type:** Change Request
- **Source:** Prompt 01 (`results/01-identity-to-transaction-entity-linkage.md`, Remaining
  Risks); **corrected during Prompt 03 forensics** (see update below).
- **Status:** Open
- **Description:** A document's association with a case (e.g. `CASE-005-PASSPORT` belonging
  to `CASE-005`) is enforced only by a string-prefix naming convention, never asserted in
  code.
- **Update (Prompt 03):** the original write-up of this item was wrong on one point —
  `data/ground_truth/{document_id}.json` **does** carry a `case_id` field (confirmed in
  `data/ground_truth/CASE-005-NID.json` and `CASE-005-PASSPORT.json`). So a ground-truth
  field to validate against already exists. The real gap is narrower than first stated:
  `src/repository.py:load_ground_truth` is defined but never called by any verification
  logic (`grep` across `src/` confirms only `scripts/sanity_check.py` reads it, for
  file-existence checking, not linkage validation). `src/service.py:verify_case` never
  cross-checks a document's `document_ids`-array membership against its own ground-truth
  `case_id`.
- **Why deferred:** Still out of Prompt 01's approved scope (transaction-side only) and out
  of Prompt 03's scope (identity *field* reconciliation, not document-to-case linkage). But
  this is now a smaller, no-new-schema fix than originally thought — no data-model addition
  needed, since the field already exists unused.
- **Suggested next step:** A small, contained fix in `src/service.py` or `src/repository.py`
  that cross-checks `load_ground_truth(document_id)['case_id'] == case_id` when assembling a
  `CaseResult` — likely doesn't need a formal change request anymore given the field already
  exists; a good candidate to fold into Prompt 16's hardening pass, or its own small prompt.

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

## BL-004 — Reason-code naming conflict: `IDENTITY_RESOLUTION.md` vs. `AC-ID-001`

- **Type:** Change Request
- **Source:** Prompt 03 forensics
- **Status:** Open
- **Description:** `specs/02_features/IDENTITY_RESOLUTION.md` ("Initial reason codes")
  names `IDENTITY_NAME_MISMATCH`, `IDENTITY_DOB_MISMATCH`, `IDENTITY_MATCH_UNCERTAIN`.
  `specs/07_acceptance/ACCEPTANCE_CRITERIA.md`'s `AC-ID-001` — already approved, already
  implemented (`src/identity.py`), already passing — locks in `CROSS_DOCUMENT_NAME_MISMATCH`
  for CASE-005. The two specs disagree on naming for the same concept, and the code
  implements the acceptance-criteria naming, not the feature-spec naming.
- **Why deferred:** Renaming the implemented flag to match `IDENTITY_RESOLUTION.md` would
  break the approved, passing `AC-ID-001` for no functional benefit. Renaming `AC-ID-001`
  instead is a call this repo's spec owner should make, not something to decide unilaterally
  mid-prompt.
- **Suggested next step:** Reconcile the two specs (pick one naming, update the other) as a
  documentation-only change request; no code change implied either way.

## BL-005 — No handling for initials/abbreviated-name variants

- **Type:** Change Request
- **Source:** Prompt 03 forensics
- **Status:** Open
- **Description:** `challenges/CH-03.md`'s stated friction explicitly includes "initials"
  (e.g. "J. Smith" vs. "John Smith") as a source of cross-document name variation. The
  current `SequenceMatcher`-based similarity check has no initials-aware logic — an initial
  vs. a full first name would likely score well below the 0.92 threshold and be flagged as a
  mismatch even when it's plausibly the same person abbreviated.
- **Why deferred:** No current fixture exercises this, and designing an initials-matching
  heuristic is a real policy decision (how much of a name prefix counts, whether a
  single-letter initial is sufficient evidence, false-positive risk of over-matching two
  different people who happen to share an initial) — inventing one mid-prompt would be
  encoding an undiscussed business rule.
- **Suggested next step:** Needs an explicit policy decision (recorded via
  `specs/09_change_requests/`) before implementation; likely pairs naturally with any future
  work on `IDENTITY_RESOLUTION.md`'s matching design.

## BL-006 — Retain per-field match/mismatch evidence on `IdentityProfile`

- **Type:** Change Request
- **Source:** Prompt 03 forensics
- **Status:** Open
- **Description:** `prompts/03-cross-document-identity-resolution.md`'s desired outcome
  calls for identity evidence to be "reconciled into a single normalized identity, with the
  match/mismatch evidence for each field retained (not just the final merged value)."
  Today, `IdentityProfile` only exposes a boolean-style risk flag (e.g.
  `CROSS_DOCUMENT_NAME_MISMATCH`) plus generic `evidence_refs` (document pointers) — an
  analyst can't see the actual conflicting values (e.g. "Passport says 'Mohammed Rahman',
  National ID says 'Moharnmad Rehrnan'") without opening the source documents themselves.
- **Why deferred:** Adding a structured per-field comparison would extend
  `specs/05_data_contracts/DATA_CONTRACTS.md`'s approved `IdentityProfile` shape, which
  `AGENTS.md` treats as requiring an approved spec/change record, not a unilateral addition.
  Packing raw name values into the existing flat `risk_flags` strings was considered and
  rejected — it would mix categorical codes with PII-like free text, a data-hygiene smell
  against `specs/04_security_privacy/SECURITY_PRIVACY.md`'s minimization intent.
- **Suggested next step:** If wanted, needs an approved additive schema field (e.g. a small
  `field_conflicts` list) via a change request — happy to draft one if you want to pursue
  this.

## BL-007 — `occupation` is captured but consumed by no rule

- **Type:** Change Request
- **Source:** Prompt 05 forensics
- **Status:** Open
- **Description:** `IdentityProfile.occupation` is populated verbatim from
  `data/customer_context/*.json` but `grep` across `src/monitoring.py` and
  `src/compliance.py` shows it is never read by any pattern or disposition rule. It exists
  on the schema and in every API response but currently has no effect on any outcome.
- **Why deferred:** Making occupation meaningful would require a policy decision (e.g. an
  occupation-to-risk-category taxonomy, or an occupation-vs-turnover plausibility check) —
  a business rule with no spec support today, not something to invent unilaterally.
- **Suggested next step:** If there's appetite to make `occupation` load-bearing, needs an
  explicit taxonomy/policy decision recorded via `specs/09_change_requests/` before any
  monitoring logic consumes it.

## BL-008 — Expected-counterparty-country baseline field

- **Type:** Change Request
- **Source:** Prompt 05 forensics
- **Status:** Open
- **Description:** `prompts/05-expected-activity-profile-normalization.md`'s suggested
  change boundary names "an expected-counterparty-country set" as an example of a
  genuinely new, deterministic normalization (derivable from `residency_country`). It would
  be a new field on `IdentityProfile` with no current spec backing, consumed by nothing
  until a monitoring pattern exists to compare against it.
- **Why deferred:** Prompt 05 was scoped to identity-side normalization only; the
  monitoring-side comparison explicitly belongs to Prompts 09 (velocity) and 10 (corridor
  fusion). Building the field speculatively now, before its consumer's exact needs are
  known, risks guessing at a shape that doesn't fit — better designed together.
- **Suggested next step:** Revisit when Prompt 09 or 10 is run; decide there whether a new
  `IdentityProfile` field is actually needed or whether `residency_country` (already present)
  is sufficient for the corridor/velocity fusion logic.
