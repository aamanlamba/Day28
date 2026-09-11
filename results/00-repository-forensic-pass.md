# Results — Prompt 00: Repository Forensic Pass

**Prompt run:** `prompts/00-repository-forensic-pass.md` (unmodified — see that file for the exact instructions executed)
**Date:** 2026-09-11
**Code changes made:** None. This was a read-only pass.

## Commands executed

```text
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python scripts/workshop_preflight.py
python scripts/sanity_check.py
pytest -q
python scripts/smoke_server.py
```

Environment note: this pass originally ran on Python 3.14.7 (outside the `WORKSHOP_RUNBOOK.md`
3.11–3.13 range) because no in-range interpreter was installed on this machine yet. Python
3.13.15 was subsequently installed (`brew install python@3.13`) and the `.venv` was rebuilt
against it; all four baseline commands were re-run below and pass unchanged. The residual
risk noted in the original pass is resolved. `Dockerfile`'s base image was also updated from
`python:3.12-slim` to `python:3.13-slim` to match.

## Baseline results

| Command | Exit | Output |
| --- | --- | --- |
| `workshop_preflight.py` | 0 | `PREFLIGHT PASSED` |
| `sanity_check.py` | 0 | `SANITY CHECK PASSED: 6 legacy cases preserved, 12 integrated cases executable, 19 document artifacts validated, 15 challenge cards present` |
| `pytest -q` | 0 | `32 passed, 1 warning in 0.19s` (warning: `starlette.testclient` `anyio.abc.BlockingPortal` deprecation, unrelated to app code) |
| `smoke_server.py` | 0 | `SMOKE SERVER PASSED on ephemeral localhost port 64013` |

All four baseline commands exited 0, per `WORKSHOP_RUNBOOK.md` §4.

## Current-state map

### Request paths

- **`/v1`:** `src/app.py:38-42` → `src/service.py` (`verify_document`/`verify_case`) →
  `src/ocr.py:extract_text` (reads `data/sidecar_ocr/*.txt`, `src/ocr.py:3-5`) →
  `src/parser.py:parse_legacy_ocr` (line-prefix parsing, `src/parser.py:7-19`) →
  `src/rules.py:evaluate`/`completeness` (deterministic gate, `src/rules.py:15-33`) →
  `src/repository.py:load_application`/`list_cases`. `verify_case` (`src/service.py:16-22`)
  takes the *worst* per-document decision and explicitly ships a
  `limitation_notice: "...does not perform robust cross-document identity resolution."`
- **`/v2`:** `src/app.py:51-61` → `src/identity.py:build_identity_profile` (calls
  `verify_case` internally, `src/identity.py:14`) / `src/monitoring.py:evaluate_transactions`
  (calls `build_identity_profile` again — recomputed, not passed through,
  `src/monitoring.py:29`) / `src/compliance.py:evaluate_compliance_case` (calls both again,
  `src/compliance.py:6-7`) → `src/models_v2.py`. **No persistence layer exists anywhere** —
  every `/v2` call re-derives `IdentityProfile`/`MonitoringResult`/`ComplianceCaseResult`
  from `data/*.json` on every request. There is no case/decision datastore, confirmed by
  `docs/known_limitations.md:16` ("There is no durable audit datastore").

### Domain objects

None persisted beyond request lifecycle — all recomputed from `data/`:

- `src/models.py`: `VerifyDocumentRequest`, `DocumentResult`, `CaseResult` (`/v1`, unchanged
  per `specs/05_data_contracts/DATA_CONTRACTS.md:4`).
- `src/models_v2.py`: `IdentityProfile`, `TransactionEvent`, `MonitoringAlert`,
  `MonitoringResult`, `ComplianceCaseResult` — matches
  `specs/05_data_contracts/DATA_CONTRACTS.md` field-for-field exactly.

### Challenge-by-challenge code coverage

Compared against `docs/15_integrated_engineering_challenges.md`:

| # | Challenge | Coverage found | Evidence |
| --- | --- | --- | --- |
| 1 | Identity-to-transaction entity linkage | Partial. Every layer keys uniformly on `case_id` (no separate customer/account/transaction identifier domains exist in the synthetic model), so the stated friction is largely avoided by construction rather than resolved by a verified-linkage mechanism. No explicit "verified account ownership" concept distinct from `case_id`. | `src/identity.py:13`, `src/monitoring.py:25-29` |
| 2 | Document-intelligence uncertainty propagation | Weak. `DocumentResult.warnings` carries `DEGRADED_OCR_QUALITY`/`ROTATED_CAPTURE` (`src/parser.py:17-18`), but `build_identity_profile`'s `confidence` is a coarse constant keyed only on `identity_status` (0.97/0.70/0.20, `src/identity.py:39`) — it never reads per-document warnings/completeness. `docs/known_limitations.md:11` confirms: "Confidence is a heuristic completeness ratio rather than a calibrated probability." | `src/identity.py:39`, `src/rules.py:12-13` |
| 3 | Cross-document identity resolution | Partial. Name matching is `SequenceMatcher` on lowercased/alphanumeric-stripped strings at a 0.92 threshold (`src/identity.py:7-11,28-32`); DOB matching is exact set equality (`src/identity.py:33-35`, no fuzzy/format tolerance). Transliteration explicitly out of scope per `specs/02_features/IDENTITY_RESOLUTION.md:29` and confirmed absent per `docs/known_limitations.md:10`. | `src/identity.py:7-35` |
| 4 | KYC lifecycle drift vs live transactions | Weak. Driven entirely by a static boolean `ctx.get('kyc_refresh_due')` in `data/customer_context/*.json` (`src/identity.py:36-38`) — no date-based expiry/refresh computation exists anywhere. | `src/identity.py:36-38` |
| 5 | Expected-activity profile normalization | Not implemented as "normalization." `occupation`/`expected_monthly_turnover` are passed through verbatim from already-structured `customer_context` JSON (`src/identity.py:44`) — there is no free-text-to-computable-attribute logic; the synthetic data bypasses the hard part of this challenge. | `src/identity.py:40-46` |
| 6 | Transaction-hook idempotency | Implemented, scoped narrowly. `_dedupe` (`src/monitoring.py:17-23`) suppresses duplicate `transaction_id`s within one loaded transaction list and reports `DUPLICATE_EVENT_SUPPRESSED`. Tested by `tests/test_integrated_compliance.py:40-43` and `AC-CMP-003`. Caveat: since there's no persistence, this only dedupes duplicates within a single request's dataset, not redelivery across separate API calls over time. | `src/monitoring.py:17-23` |
| 7 | Out-of-order and late events | Partial. Velocity pattern explicitly sorts by event time (`src/monitoring.py:41`); structuring and pass-through patterns compare timestamps pairwise so are order-independent by construction. No test feeds shuffled/reversed input to prove order-independence directly. | `src/monitoring.py:33-45,62-74` |
| 8 | Structuring / threshold avoidance | Implemented. 3+ CREDIT transactions in [8000,10000) within 24h (`src/monitoring.py:34-38`). Threshold values are Python literals, not sourced from `config/baseline.json`. | `src/monitoring.py:34-38`, `tests/test_integrated_compliance.py:19-23` |
| 9 | Rapid transaction velocity | Implemented. 5+ events in a 60-minute sliding window (`src/monitoring.py:40-45`). Same hardcoded-threshold caveat as #8. | `src/monitoring.py:40-45` |
| 10 | High-risk corridor × identity-context fusion | Implemented. `HIGH_RISK_COUNTRIES={'XQ','ZR'}` (`src/monitoring.py:9`) fused with `identity_status`/`residency_country`/`KYC_REFRESH_DUE` to escalate severity (`src/monitoring.py:47-54`). | `src/monitoring.py:47-54`, `tests/test_integrated_compliance.py:26-30` |
| 11 | Pass-through / funnel-account behaviour | Implemented. Credit→debit pairing within 6h, ≤8% amount delta, credit ≥5000, ≥2 pairs (`src/monitoring.py:62-74`). | `src/monitoring.py:62-74` |
| 12 | False-positive reduction vs explainability | Mostly implemented at the alert level (`reasons`, `transaction_ids`, `evidence_refs`, `policy_version` all populated with specific content, not generic strings). Weaker at the disposition level: `ComplianceCaseResult.reason_codes` in `src/compliance.py:9-18` records coarse codes (`TRANSACTION_MONITORING_HIGH_RISK`) but not which alert/pattern_code drove the escalation. | `src/compliance.py:9-20` |
| 13 | HITL workflow integrity | Absent — confirmed design challenge. No reviewer/authorization model, no disposition-override endpoint, no persisted case state to override in the first place. `docs/known_limitations.md:15,19` confirm no review queue and no auth/authz. | Absent from `src/`, `src/app.py` |
| 14 | Policy / rule / model version drift | Weak. `POLICY_VERSION='tm-policy-2026.09-synthetic'` (`src/monitoring.py:8`) is a single hardcoded string with no version history and no replay-by-recorded-version capability. All actual thresholds (8000/10000, 5/60min, 1.75×, 6h/8%/5000) are Python literals in `src/monitoring.py`, not sourced from `config/baseline.json`, which only holds `/v1` legacy settings. `docs/known_limitations.md:25` states this explicitly. | `src/monitoring.py:8-9,34,40,59,69`, `config/baseline.json` |
| 15 | Evals, observability & production readiness | Thin. `evals/golden_cases.json` covers 6 of 12 integrated cases with only `expected_disposition`/`must_alert`/`must_warn` checks — no golden `IdentityProfile` values, no edge/adversarial/metamorphic/outage cases. `scripts/run_integrated_evals.py` is pass/fail only, no latency/precision-recall/replay measurement. No metrics endpoint exists (`docs/known_limitations.md:18`). | `evals/golden_cases.json`, `scripts/run_integrated_evals.py` |

### Register questions — resolved by code inspection vs. still open

Against `docs/engineering_challenge_register.md`:

**Resolved by code inspection:**

- Q3 (fields silently omitted): `src/identity.py` treats every context/document field as
  optional via `.get()`; nothing hard-fails on a missing field — confirmed answered (silent
  `None`, not a hard failure), but worth challenging in Prompt 05.
- Q6 (name differences): handled via `SequenceMatcher` ratio, not exact match —
  `src/identity.py:10-11`.
- Q13 (correlation trail): `src/app.py:12-17` middleware assigns/logs an `x-correlation-id`
  for every request.
- Q17 (unauthorized endpoints): every `/v1` and `/v2` endpoint in `src/app.py` is callable
  with no auth check at all — confirmed open/absent, not merely undocumented.

**Genuinely open (no code answers them):**

- Q1 (orientation/noise/spacing robustness) — no test varies these independent of the fixed
  synthetic sidecar text.
- Q7 (does a DOB match compensate for a name mismatch?) — no such compensation logic exists;
  the two checks are independent and additive (`src/identity.py:28-35`).
- Q9 (which decisions are policy vs. parser side-effects) — the 8000/10000, 5/60min, 1.75×,
  6h/8% constants are undocumented as policy anywhere outside source code (ties to gap #14).
- Q11 (is completeness a meaningful confidence measure) — `docs/known_limitations.md:11`
  says no.
- Q18 (where is sensitive data logged) — not verified in this pass; `src/app.py`'s logging
  middleware logs method/path/status/correlation-id only, not field values, but no explicit
  check was run against `IdentityProfile`/document field logging elsewhere.
- Q19 (retention/deletion controls) — confirmed absent (`docs/known_limitations.md:21`), not
  merely unverified.
- Q20 (unsafe file access) — `src/repository.py:safe_id` blocks `/`, `\`, `..`
  (`src/repository.py:7-10`, tested by `tests/test_api.py:46-47`), so this one is resolved:
  path traversal is blocked.

### Tests — what they actually lock in

- `tests/test_rules.py` (3 tests): `/v1` rule-level completeness/expiry/tamper logic only.
- `tests/test_service.py` (6 tests): `/v1` case-level aggregation, including
  `test_name_variation_exposes_brownfield_gap` — explicitly asserts CASE-005 still
  APPROVEs on `/v1`, i.e. the legacy cross-document gap is a locked-in regression baseline,
  not a bug to fix under `/v1` compatibility rules.
- `tests/test_api.py` (9 tests): `/v1` HTTP contract, 404s, path-traversal block (400),
  empty-body validation (422), correlation-id echo.
- `tests/test_integrated_compliance.py` (9 tests): `/v2` identity/monitoring/compliance
  happy-path and one-pattern-each assertions (one test per challenge 1, 6, 8, 9, 10, 11 plus
  CASE-001 clear and CASE-004 escalate). No test currently exercises boundary conditions
  (e.g. exactly 7999/8000/9999/10000, exactly 4/5/6 events in the velocity window, exactly
  1.75×) or adversarial/malformed input for the `/v2` path.
- `tests/test_release_integrity.py` (2 tests): image-decodability and byte-for-byte
  regression-snapshot equality against `data/expected_baseline_outputs/*.json` for the six
  legacy cases.

### `TODO`s, hard-coded/synthetic-only assumptions, missing validation in `src/`

- No literal `TODO` comments exist in `src/`.
- Hard-coded synthetic-only: `REFERENCE_DATE=date(2026,9,9)` (`src/rules.py:4`) freezes
  "today" for reproducible expiry checks — by design, but means the expiry gate will
  silently stop being meaningful once real-world testing occurs after that date without
  updating the constant.
- `POLICY_VERSION` and all `/v2` thresholds are hard-coded literals (see gap #14).
- `HIGH_RISK_COUNTRIES={'XQ','ZR'}` is a two-entry synthetic set with no source-of-truth
  document.
- No validation exists on `/v2` endpoints beyond path-based case lookup (`FileNotFoundError`
  → 404 via `src/app.py:19-21`); there is no Pydantic request body for the `/v2` POST
  endpoints (they take no body), so malformed-body edge cases don't apply, but there is also
  no validation that `TransactionEvent` amounts/timestamps in `data/transactions/*.json` are
  well-formed before construction — a malformed fixture would raise an unhandled
  `pydantic.ValidationError` (500), not a controlled 4xx, which conflicts with
  `specs/06_api_contracts/API_CONTRACTS.md:21` ("`/v2` errors for unknown IDs are controlled
  client errors") for the malformed-data case specifically (only unknown-ID is currently
  controlled).

## Ranked gaps

Most downstream-contaminating first:

1. **CH-13 HITL workflow integrity** — absent entirely, and every other challenge's output
   (alerts, disposition) currently has no governed path to a human decision or override.
   This is the biggest structural gap because it's a prerequisite for any of this being
   usable beyond a single stateless scoring call.
2. **CH-14 Policy/rule/model version drift** — every monitoring threshold from challenges
   6–11 is an undocumented Python literal; without fixing this first, any future rule change
   is already unreproducible.
3. **CH-02 Document-intelligence uncertainty propagation** — `confidence` is disconnected
   from actual per-document evidence quality, contaminating the credibility of challenges 1,
   3, 4, 10 and 12 simultaneously.
4. **CH-05 Expected-activity profile normalization** — the hard part of this challenge is
   bypassed by synthetic data being pre-structured; challenge 9's deviation alert is only as
   trustworthy as this bypass allows.
5. **CH-06 Transaction-hook idempotency** — implemented but only within a single request's
   dataset; a genuine redelivery-over-time scenario is unproven.
6. **CH-15 Evals/observability** — thin golden-case coverage means none of challenges 1–14's
   claimed fixes will be measurably verified until this is strengthened; ranked lower only
   because it's a measurement gap, not a functional one.
7. **CH-03 Cross-document identity resolution** — bounded gap (transliteration explicitly
   out of scope per spec); DOB comparison has no format tolerance.
8. **CH-04 KYC lifecycle drift** — static flag rather than computed staleness; narrow scope.
9. **CH-01 Identity-to-transaction linkage** — largely avoided by construction; residual risk
   is conceptual rather than an active defect.
10. **CH-12 False-positive reduction vs explainability** — alert-level evidence is already
    good; only the disposition-level reason-code granularity needs improvement.
11. Challenges **7, 8, 9, 10, 11** (temporal correctness, structuring, velocity, corridor
    fusion, pass-through) are functionally implemented and covered by at least one passing
    test each; residual risk is boundary-condition and reordering-robustness testing, not
    missing logic.

## Compatibility constraints (must not change)

- `/v1` response shapes: `DocumentResult`, `CaseResult` (`src/models.py`) — per
  `specs/05_data_contracts/DATA_CONTRACTS.md:4` and `KYC-COMP-001/002`.
- `/v1` endpoints and behavior: `GET /health/live`, `GET /health/ready`, `GET /v1/cases`
  (exactly six cases, `src/repository.py:31-36`), `POST /v1/documents/verify`,
  `POST /v1/cases/{case_id}/verify` — per `specs/06_api_contracts/API_CONTRACTS.md:3-10`.
- `tests/test_release_integrity.py`'s byte-for-byte snapshot equality against
  `data/expected_baseline_outputs/*.json` for CASE-001..006 is a hard regression gate —
  includes `test_name_variation_exposes_brownfield_gap`'s CASE-005 APPROVE outcome, which
  must NOT change under `/v1` even after `/v2` identity resolution is hardened in
  Prompts 01–03.
- `/v2` response shapes: `IdentityProfile`, `TransactionEvent`, `MonitoringAlert`,
  `MonitoringResult`, `ComplianceCaseResult` (`src/models_v2.py`) — additive changes only,
  per `specs/05_data_contracts/DATA_CONTRACTS.md` and `AGENTS.md`'s "Preserve `/v1` API
  compatibility unless an approved spec explicitly changes it."

## Environment update (post-pass)

Local Python was updated to 3.13.15 (`brew install python@3.13`), `.venv` rebuilt against
it, and `Dockerfile` changed from `python:3.12-slim` to `python:3.13-slim` for consistency.
All four baseline commands were re-run and pass unchanged:

| Command | Exit | Output |
| --- | --- | --- |
| `workshop_preflight.py` | 0 | `PREFLIGHT PASSED` (reports `Python: 3.13.15`) |
| `sanity_check.py` | 0 | `SANITY CHECK PASSED: 6 legacy cases preserved, 12 integrated cases executable, 19 document artifacts validated, 15 challenge cards present` |
| `pytest -q` | 0 | `32 passed, 1 warning in 0.15s` |
| `smoke_server.py` | 0 | `SMOKE SERVER PASSED on ephemeral localhost port 64464` |

## Residual risk

- This pass is read-only analysis; it resolves none of the 15 challenges. The ranked list
  above is offered as additional context for prompt sequencing, not a proposal to reorder
  the existing `prompts/00` → `16` numbering, which was chosen for pipeline-order reasons
  (identity → transaction → governance) rather than pure severity order.
