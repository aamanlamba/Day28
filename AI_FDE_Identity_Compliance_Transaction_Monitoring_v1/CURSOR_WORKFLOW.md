# Cursor Workflow for AI FDEs

Cursor project rules are stored in `.cursor/rules/*.mdc`; `AGENTS.md` provides a plain-Markdown repository-wide instruction set.

## Recommended workshop sequence
### 1. Repository forensic pass
Prompt Cursor:
> Read AGENTS.md, SPEC_DRIVEN_DEVELOPMENT.md, the product/system specs, current README, docs, tests and src. Do not modify files. Build a current-state map, identify requirement gaps, known defects, compatibility constraints and the top five spec-to-code conflicts. Cite file paths.

### 2. Requirement selection
> Work on KYC-FR-004 only. Explain the requirement, acceptance criteria, relevant legacy behavior, affected modules and any ambiguity. Do not code.

### 3. Plan mode
> Produce an implementation plan for KYC-FR-004. Map each step to acceptance criteria. Include tests first, affected files, compatibility risks and evidence to capture. Do not implement yet.

### 4. Test-first execution
> Implement only the first approved plan increment. Add the acceptance test first, run it to demonstrate the gap, implement the minimum change, then rerun targeted tests. Stop after reporting the diff and evidence.

### 5. Regression + release gate
> Run the full test suite and applicable preflight checks. Classify failures as target-spec defect, legacy-regression conflict, implementation defect, or environment issue. Do not weaken tests to get green.

### 6. Traceability closure
> Update the traceability matrix and create an evidence record containing requirement IDs, files changed, tests run, outcomes, residual risks and any ADR/change request references.

## Anti-pattern prompts
Avoid: "Improve this repo", "make it production ready", "fix everything", or "modernize KYC" without a governed specification. Those prompts encourage hidden assumptions and untraceable design drift.
