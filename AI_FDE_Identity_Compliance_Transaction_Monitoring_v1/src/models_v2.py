from typing import Literal
from pydantic import BaseModel, Field

IdentityStatus = Literal["VERIFIED","REVIEW","REJECTED"]
RiskLevel = Literal["LOW","MEDIUM","HIGH","CRITICAL"]
Disposition = Literal["CLEAR","REVIEW","ESCALATE"]

class IdentityProfile(BaseModel):
    case_id: str
    canonical_name: str | None = None
    date_of_birth: str | None = None
    residency_country: str | None = None
    nationality: str | None = None
    occupation: str | None = None
    expected_monthly_turnover: float | None = None
    identity_status: IdentityStatus
    confidence: float = Field(ge=0, le=1)
    risk_flags: list[str] = []
    evidence_refs: list[str] = []

class TransactionEvent(BaseModel):
    transaction_id: str
    case_id: str
    timestamp: str
    direction: Literal["CREDIT","DEBIT"]
    amount: float = Field(gt=0)
    currency: str = "USD"
    counterparty_id: str
    counterparty_country: str
    channel: str = "TRANSFER"
    device_id: str | None = None

class MonitoringAlert(BaseModel):
    alert_id: str
    case_id: str
    pattern_code: str
    severity: RiskLevel
    score: float = Field(ge=0, le=1)
    reasons: list[str]
    transaction_ids: list[str]
    evidence_refs: list[str]
    policy_version: str

class MonitoringResult(BaseModel):
    case_id: str
    overall_risk: RiskLevel
    alerts: list[MonitoringAlert]
    received_transaction_count: int
    processed_transaction_count: int
    hook_warnings: list[str] = []

class ComplianceCaseResult(BaseModel):
    case_id: str
    disposition: Disposition
    reason_codes: list[str]
    identity: IdentityProfile
    monitoring: MonitoringResult
    policy_version: str
    evidence_lineage: list[str]
