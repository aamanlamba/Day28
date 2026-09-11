# Cursor SDD Conversion Implementation Plan

> **For agentic workers:** Execute this plan task-by-task and verify the baseline after changes.

**Goal:** Add a complete Specs-Driven Development control plane around the existing brownfield KYC repo for AI FDE training in Cursor.

**Architecture:** Preserve the existing runtime and tests as current-state evidence. Add specifications, Cursor rules, acceptance criteria, traceability, task/change/ADR workflows and evidence templates as version-controlled engineering controls.

**Tech Stack:** Markdown, Cursor project rules (`.mdc`), existing Python/FastAPI/pytest repo.

**Spec:** `docs/superpowers/specs/2026-09-10-cursor-sdd-conversion-design.md`

## Global Constraints
- Preserve existing `/v1` compatibility.
- Preserve offline operation.
- Do not implement the target identity-resolution feature as part of the conversion.
- Keep the existing baseline tests executable.

### Task 1 — Cursor governance
Create `AGENTS.md` and focused `.cursor/rules/*.mdc` files.

### Task 2 — Specification hierarchy
Create product, system, feature, NFR, security/privacy, data and API specifications with stable IDs.

### Task 3 — Acceptance and traceability
Create Given/When/Then acceptance criteria and a matrix mapping requirements to baseline implementation, tests and known gaps.

### Task 4 — Engineering workflow
Create Definition of Ready/Done, Cursor workflow guide, ADR/change request templates, task lifecycle and evidence templates.

### Task 5 — Seed training target
Create TASK-001 for cross-document identity consistency and explicitly document the CASE-005 legacy-test conflict.

### Task 6 — Verification and packaging
Run pytest and workshop preflight, update conversion manifest, then package the complete repository.
