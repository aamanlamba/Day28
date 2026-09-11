"""Interactive test console for the AI FDE KYC + Transaction Monitoring service.

Not part of the service itself - a local testing/demo tool. Calls src/* directly
(same pattern as scripts/run_demo.py) rather than over HTTP, so it exercises the exact
same business logic the API and test suite do, without needing a separate uvicorn process.

Run with: streamlit run scripts/streamlit_app.py
Requires: pip install -r requirements-streamlit.txt (kept separate from the service's own
requirements.txt - Streamlit is a testing convenience, not a service dependency).
"""
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import streamlit as st

from src.repository import list_cases, list_integrated_cases
from src.service import verify_document, verify_case
from src.identity import build_identity_profile
from src.monitoring import evaluate_transactions
from src.compliance import evaluate_compliance_case
from src.review import submit_review_decision, list_review_decisions, UnauthorizedReviewAction
from src.policy import CURRENT_POLICY_VERSION, POLICY_VERSIONS

st.set_page_config(page_title="AI FDE KYC + Transaction Monitoring", layout="wide")
st.title("AI FDE KYC + Transaction Monitoring — Test Console")
st.caption(
    "All identities, documents and transactions are fabricated for engineering training. "
    "Not a real KYC/AML decision engine."
)

legacy_cases = [c["case_id"] for c in list_cases()]
integrated_cases = [c["case_id"] for c in list_integrated_cases()]

tab_legacy, tab_identity, tab_monitoring, tab_compliance, tab_review, tab_policy = st.tabs(
    ["/v1 Legacy KYC", "/v2 Identity", "/v2 Monitoring", "/v2 Compliance", "/v2 HITL Review", "Policy Versions"]
)

with tab_legacy:
    st.subheader("Legacy /v1 case verification")
    case_id = st.selectbox("Case", legacy_cases, key="legacy_case")
    if st.button("Verify case", key="legacy_verify_btn"):
        st.json(verify_case(case_id).model_dump())
    st.divider()
    st.subheader("Verify a single document")
    doc_id = st.text_input("Document ID", value=f"{case_id}-PASSPORT")
    if st.button("Verify document", key="legacy_doc_btn"):
        try:
            st.json(verify_document(doc_id).model_dump())
        except FileNotFoundError:
            st.error(f"Unknown document: {doc_id}")

with tab_identity:
    st.subheader("/v2 Identity profile")
    case_id = st.selectbox("Case", integrated_cases, key="identity_case")
    if st.button("Build identity profile", key="identity_btn"):
        profile = build_identity_profile(case_id)
        col1, col2 = st.columns(2)
        col1.metric("Identity status", profile.identity_status)
        col2.metric("Confidence", profile.confidence)
        st.write("Risk flags:", profile.risk_flags or "(none)")
        if profile.field_conflicts:
            st.write("Field conflicts (BL-006):")
            st.table([c.model_dump() for c in profile.field_conflicts])
        with st.expander("Full IdentityProfile JSON"):
            st.json(profile.model_dump())

with tab_monitoring:
    st.subheader("/v2 Transaction monitoring")
    case_id = st.selectbox("Case", integrated_cases, key="monitoring_case")
    policy_choice = st.selectbox(
        "Policy version (CH-14 replay)", ["(current)"] + list(POLICY_VERSIONS.keys()), key="monitoring_policy"
    )
    if st.button("Evaluate transactions", key="monitoring_btn"):
        policy_version = None if policy_choice == "(current)" else policy_choice
        result = evaluate_transactions(case_id, policy_version)
        col1, col2, col3 = st.columns(3)
        col1.metric("Overall risk", result.overall_risk)
        col2.metric("Received", result.received_transaction_count)
        col3.metric("Processed", result.processed_transaction_count)
        if result.hook_warnings:
            st.warning(", ".join(result.hook_warnings))
        if result.alerts:
            st.table([
                {
                    "pattern": a.pattern_code,
                    "severity": a.severity,
                    "score": a.score,
                    "transaction_ids": ", ".join(a.transaction_ids),
                    "reasons": " | ".join(a.reasons),
                }
                for a in result.alerts
            ])
        else:
            st.info("No alerts for this case under this policy version.")
        st.caption(f"Policy version used: {result.policy_version}")

with tab_compliance:
    st.subheader("/v2 Integrated compliance disposition")
    case_id = st.selectbox("Case", integrated_cases, key="compliance_case")
    if st.button("Evaluate compliance case", key="compliance_btn"):
        result = evaluate_compliance_case(case_id)
        st.metric("Disposition", result.disposition)
        st.write("Reason codes:", result.reason_codes)
        with st.expander("Evidence lineage"):
            st.write(result.evidence_lineage)
        with st.expander("Full ComplianceCaseResult JSON"):
            st.json(result.model_dump())

with tab_review:
    st.subheader("/v2 HITL review (CH-13 governed override channel)")
    st.caption(
        "In-memory only - review history resets when this Streamlit process restarts. "
        "reviewer_role is self-declared, not authenticated (CR-002)."
    )
    case_id = st.selectbox("Case", integrated_cases, key="review_case")
    reviewer_id = st.text_input("Reviewer ID", value="demo-analyst", key="review_reviewer_id")
    reviewer_role = st.selectbox("Reviewer role", ["ANALYST", "SUPERVISOR"], key="review_role")
    new_disposition = st.selectbox("New disposition", ["CLEAR", "REVIEW", "ESCALATE"], key="review_disposition")
    rationale = st.text_area("Rationale", value="Reviewed evidence during manual spot check.", key="review_rationale")
    if st.button("Submit review decision", key="review_submit_btn"):
        try:
            decision = submit_review_decision(case_id, reviewer_id, reviewer_role, new_disposition, rationale)
            st.success(f"{decision.decision_id}: {decision.prior_disposition} → {decision.new_disposition}")
        except UnauthorizedReviewAction as e:
            st.error(f"Unauthorized (403): {e}")
        except ValueError as e:
            st.error(f"Invalid request (400): {e}")
    st.divider()
    st.write("Review history for this case:")
    history = list_review_decisions(case_id)
    if history:
        st.table([d.model_dump() for d in history])
    else:
        st.info("No review decisions recorded yet for this case in this session.")

with tab_policy:
    st.subheader("Versioned monitoring policy (CH-14)")
    st.write(f"Current policy version: **{CURRENT_POLICY_VERSION}**")
    for version, bundle in POLICY_VERSIONS.items():
        with st.expander(version):
            st.json({k: (v if isinstance(v, (int, float, str, bool)) else str(v)) for k, v in bundle.items()})
