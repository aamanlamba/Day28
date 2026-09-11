# Prompt 08 — Structuring / Threshold-Avoidance Detection (CH-08)

## Prerequisite
Prompts 00–07 complete (correct event-time windowing from Prompt 07 is required for this
pattern to be meaningful).

## Section 2 fill-in
- **Engineering transformation:** Structuring / Threshold-Avoidance Detection
- **Problem to solve:** Individual transactions may appear harmless while the aggregate
  pattern over a time window indicates deliberate threshold avoidance; verified ownership
  and linked-account identity (from Prompt 01) are necessary to aggregate correctly across
  the right customer relationship rather than per-transaction in isolation.
- **Desired production outcome:** A windowed-aggregation rule in `src/monitoring.py`
  identifies multiple sub-threshold transactions whose combined behavior within a
  configurable window constitutes a monitoring pattern, and raises a `MonitoringAlert`
  (`src/models_v2.py`) with the specific transaction IDs and reasons behind it.
- **Business/risk consequence:** Structuring is specifically designed to evade
  single-transaction thresholds; without aggregate detection, this is a known,
  well-understood evasion technique that a monitoring platform must catch to be credible.

## Repo grounding
- `challenges/CH-08.md`, row 8 of `docs/15_integrated_engineering_challenges.md`
- Evidence: `data/` for **CASE-007**
- Code: `src/monitoring.py`, `src/models_v2.py` (`MonitoringAlert`), `src/rules.py` (check
  whether any threshold constant is already defined there for the legacy `/v1` path and
  should be reused/versioned rather than duplicated)
- Specs: `specs/02_features/COMPLIANCE_MONITORING.md`
- Tests: `tests/test_integrated_compliance.py`, `tests/test_rules.py`

## Suggested change boundary
- In scope: a windowed-aggregation pattern rule in `src/monitoring.py`, its threshold as a
  versioned, externally visible constant (see Prompt 14 for the general versioning
  mechanism — if that hasn't landed yet, use a simple explicit constant here and flag it for
  Prompt 14 to formalize), test cases with transactions just under/at/over the boundary.
- Out of scope: velocity detection based on transaction *count/frequency* alone without a
  monetary-threshold angle (Prompt 09) and pass-through/funnel patterns (Prompt 11) — keep
  this rule specific to sub-threshold aggregation.

## STOP conditions
1. Complete CLAUDE.md §3 and §15 before implementing.
2. Explicitly test the threshold boundary condition (exactly at the limit, one unit under,
   one unit over) per CLAUDE.md §9.
3. The rule itself must be deterministic; any AI/probabilistic scoring, if used at all, may
   only advise or explain — the accept/flag decision stays rule-based, per CLAUDE.md §8 and
   the repo's design constraint in `docs/15_integrated_engineering_challenges.md`.
4. Follow CLAUDE.md §22 in order and close with §24.
