# Prompt 13 — HITL Workflow Integrity (CH-13)

## Prerequisite
Prompts 00–12 complete. This is a design challenge — `docs/15_integrated_engineering_
challenges.md` lists its repo evidence as "design challenge" (no seeded case), so more of
this prompt's forensics is about what's *absent* than about auditing existing behavior.

## Section 2 fill-in
- **Engineering transformation:** HITL (Human-in-the-Loop) Workflow Integrity
- **Problem to solve:** Human review can become an uncontrolled override channel if
  authority, state transitions and evidence changes are not governed; confirm in forensics
  that `src/compliance.py`'s `Disposition` (`CLEAR`/`REVIEW`/`ESCALATE` in
  `src/models_v2.py`) currently has no analyst-action model at all (no reviewer identity, no
  state-transition rules, no override audit trail).
- **Desired production outcome:** Reviewers can inspect identity evidence, correct extracted
  fields and resolve document conflicts, and can set alert disposition/escalation/
  suppression/override — but every such action is role-controlled, timestamped, tied to a
  specific evidence snapshot, and auditable; it must never silently rewrite the underlying
  rule/model-derived facts.
- **Business/risk consequence:** An ungoverned override channel is precisely how compliance
  programs fail audits — a reviewer's disposition change must be distinguishable from, and
  never overwrite, the deterministic evidence that triggered the alert in the first place.

## Repo grounding
- `challenges/CH-13.md`, row 13 of `docs/15_integrated_engineering_challenges.md`
- Register questions 17–18 in `docs/engineering_challenge_register.md` (authorization,
  where sensitive data is written/logged)
- Code: `src/compliance.py`, `src/models_v2.py` (`Disposition`), `src/app.py` (no
  `/v2` review-action endpoint currently exists — confirm this in forensics)
- Specs: `specs/04_security_privacy/SECURITY_PRIVACY.md`,
  `specs/06_api_contracts/API_CONTRACTS.md`, `specs/07_acceptance/ACCEPTANCE_CRITERIA.md`

## Suggested change boundary
- In scope: a minimal reviewer-action model and endpoint (e.g. a `ReviewDecision` record
  with reviewer id, timestamp, prior/new disposition, rationale, and a reference to the
  alert/case evidence version it was made against) plus authorization checks; append-only
  storage of review decisions (never mutate the original alert's evidence fields).
- Out of scope: building a full identity/auth system — use whatever minimal
  authorization mechanism the specs already define or require (`specs/04_security_privacy/
  SECURITY_PRIVACY.md`); if none is defined, record that gap under
  `specs/09_change_requests/` rather than inventing an auth stack.

## STOP conditions
1. Complete CLAUDE.md §3 and §15 before implementing — since this is a design challenge
   with no seeded evidence case, the plan must state explicitly what new
   file(s)/endpoint(s) are proposed and why, and must be approved before coding.
2. This is new-capability work, not a bug fix — apply CLAUDE.md §21 (Change Boundary)
   strictly: no new framework, no external auth service, smallest coherent addition only.
3. Every review action must produce an audit event and be reproducible after the fact
   (CLAUDE.md §7 invariants: "analyst decisions must be auditable").
4. Follow CLAUDE.md §22 in order and close with §24.
