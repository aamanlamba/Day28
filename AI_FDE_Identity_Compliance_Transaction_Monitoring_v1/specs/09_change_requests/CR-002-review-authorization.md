# Change Request — CR-002

**Status:** Proposed
**Raised by:** Prompt 13 forensics (CH-13, HITL Workflow Integrity)
**Date:** 2026-09-11
**Affected requirements:** None existing; this is a new capability with no prior
requirement ID. Relates to `specs/04_security_privacy/SECURITY_PRIVACY.md`.

## Requested change

Back `ReviewDecisionRequest.reviewer_id`/`reviewer_role` with real authentication (e.g. a
verified session/token claim) instead of trusting client-supplied values.

## Why

`docs/15_integrated_engineering_challenges.md` (CH-13) and `challenges/CH-13.md` both
require that review/override actions be "role-controlled." `specs/04_security_privacy/
SECURITY_PRIVACY.md` defines no authentication or authorization mechanism anywhere in this
repo (confirmed: no endpoint, `/v1` or `/v2`, has ever required credentials). Per the
originating prompt's explicit instruction ("use whatever minimal authorization mechanism
the specs already define... if none is defined, record that gap... rather than inventing an
auth stack"), Prompt 13 implements the *governance structure* — a deterministic rule
requiring `SUPERVISOR` role to downgrade a disposition, with every decision recorded
against a `reviewer_id` and `reviewer_role` — without verifying that the caller actually
holds the role they claim.

## Current behavior

`POST /v2/compliance/cases/{case_id}/review` accepts `reviewer_id` and `reviewer_role` as
plain request-body fields (`src/models_v2.py:ReviewDecisionRequest`). Anyone who can reach
the endpoint can claim `reviewer_role: "SUPERVISOR"` and downgrade any disposition,
including clearing an `ESCALATE`. The resulting `ReviewDecision` is fully audit-logged
(who claimed to act, when, why, against what prior state) but the "who" is unverified.

## Proposed target behavior

`reviewer_id`/`reviewer_role` should be derived from an authenticated identity (e.g. a
verified JWT claim or session, per whatever auth mechanism the broader platform eventually
adopts) rather than accepted as free-form request fields. Until such a mechanism exists,
this endpoint's authorization is advisory/structural only — a real deployment must not treat
it as a security control.

## Compatibility impact

None to existing endpoints. Adding real authentication would likely change
`ReviewDecisionRequest`'s shape (removing `reviewer_id`/`reviewer_role` as client-supplied
fields) and would be a breaking change to the endpoint introduced in this same prompt — not
to any pre-existing `/v1` or `/v2` contract.

## Security/privacy impact

**Significant, until resolved.** The review-override channel this prompt introduces is
currently trust-on-input for authorization. It must not be exposed in any non-training
deployment without this CR being addressed first.

## Acceptance criteria changes

None proposed yet — pending a decision on which authentication mechanism this platform will
eventually adopt, which is outside this workshop's engineering scope.

## Decision

Pending — not yet approved. Filed for visibility; the HITL endpoints ship with this
limitation clearly documented (`src/review.py` module docstring, this CR, and
`results/13-hitl-workflow-integrity.md`) rather than silently.
