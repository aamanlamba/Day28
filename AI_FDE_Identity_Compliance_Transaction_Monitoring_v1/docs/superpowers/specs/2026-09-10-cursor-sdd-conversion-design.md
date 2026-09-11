# Cursor Specs-Driven Development Conversion Design

## Goal
Convert the existing KYC brownfield repository into a classroom-ready Specs-Driven Development environment for AI FDEs using Cursor without prematurely implementing the target modernization.

## Architecture
The legacy application remains the executable current-state baseline. A version-controlled specification control plane is added around it: product/system/feature/NFR/security/data/API specs, acceptance criteria, traceability, change control, ADRs, tasks, evidence templates, and Cursor project rules.

## Key invariant
Current code and regression tests describe what the inherited system does; approved specs describe what the evolving system must do. Conflicts must be surfaced and resolved explicitly, never hidden by prompt-generated code changes.

## Success criteria
- Cursor has persistent project instructions via `.cursor/rules/*.mdc` and `AGENTS.md`.
- A requirement-to-acceptance-to-code/test/evidence chain exists.
- At least one deliberate spec-versus-legacy conflict is seeded for training (CASE-005 identity consistency).
- The legacy application and tests remain runnable after conversion.
- Participants can execute a repeatable READ→TRACE→CHALLENGE→PLAN→TEST→IMPLEMENT→VERIFY→EVIDENCE→UPDATE loop.
