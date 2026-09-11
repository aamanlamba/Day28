# ADR-001 — Preserve Brownfield Baseline and Add a Specification Control Plane

**Status:** Accepted  
**Date:** 2026-09-10  
**Requirements:** KYC-PR-001 through KYC-PR-006, KYC-NFR-006

## Context
The repo is intentionally a credible legacy baseline. Replacing its implementation during conversion would erase the gap participants need to discover and would conflate SDD training with solution modernization.

## Decision
Keep the current `src/`, baseline fixtures and regression tests intact during the SDD conversion. Add a specification control plane (`specs/`, Cursor rules, acceptance criteria, traceability, tasks and evidence) around the baseline. Target feature work will subsequently be executed requirement-by-requirement.

## Consequences
Participants can compare legacy behavior against explicit target requirements, discover test/spec conflicts, and practice controlled modernization with auditable evidence.
