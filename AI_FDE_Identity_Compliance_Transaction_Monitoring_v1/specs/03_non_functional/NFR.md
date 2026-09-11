# Non-Functional Requirements

- **KYC-NFR-001 — Offline determinism:** Core workshop verification shall operate without external API keys or mandatory network access.
- **KYC-NFR-002 — Responsiveness:** Changes must not introduce obviously blocking network calls into the synchronous verification path.
- **KYC-NFR-003 — Reproducibility:** Test outcomes shall be reproducible using the repository's frozen reference date and synthetic fixtures.
- **KYC-NFR-004 — Maintainability:** New policy/identity logic shall be isolated behind focused functions/modules with explicit tests rather than embedded as opaque endpoint logic.
- **KYC-NFR-005 — Observability:** Failures and decisions shall remain attributable to a correlation trail without logging unnecessary sensitive field values.
- **KYC-NFR-006 — Compatibility:** Existing baseline tests are regression gates except where an approved requirement/change record intentionally updates expected behavior.
