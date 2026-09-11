from __future__ import annotations
from collections import defaultdict
from datetime import datetime, timedelta
from .repository import load_json
from .identity import build_identity_profile
from .models_v2 import TransactionEvent, MonitoringAlert, MonitoringResult

POLICY_VERSION='tm-policy-2026.09-synthetic'
HIGH_RISK_COUNTRIES={'XQ','ZR'}

def _dt(s: str) -> datetime:
    return datetime.fromisoformat(s.replace('Z','+00:00'))

def _alert(case_id, code, severity, score, reasons, txs, evidence):
    return MonitoringAlert(alert_id=f'{case_id}-{code}-{len(txs)}', case_id=case_id, pattern_code=code, severity=severity, score=score, reasons=reasons, transaction_ids=[t.transaction_id for t in txs], evidence_refs=evidence, policy_version=POLICY_VERSION)

def _dedupe(events):
    out=[]; seen=set(); warnings=[]
    for e in events:
        if e.transaction_id in seen:
            warnings.append('DUPLICATE_EVENT_SUPPRESSED'); continue
        seen.add(e.transaction_id); out.append(e)
    return out, sorted(set(warnings))

def evaluate_transactions(case_id: str) -> MonitoringResult:
    raw=load_json('transactions', case_id)
    received=[TransactionEvent(**x) for x in raw['transactions']]
    txs,warnings=_dedupe(received)
    profile=build_identity_profile(case_id)
    alerts=[]
    evidence_base=[f'identity:{case_id}'] + profile.evidence_refs

    # Pattern 1: structuring / threshold avoidance: 3+ same-direction transfers clustered just below 10k in 24h
    near=[t for t in txs if 8000 <= t.amount < 10000 and t.direction=='CREDIT']
    for anchor in near:
        window=[t for t in near if abs(_dt(t.timestamp)-_dt(anchor.timestamp)) <= timedelta(hours=24)]
        if len(window) >= 3:
            alerts.append(_alert(case_id,'TM_STRUCTURING','HIGH',0.90,['3+ credits between 8,000 and 9,999 within 24h','RULE_THRESHOLD_AVOIDANCE'],window,evidence_base)); break

    # Pattern 2: rapid velocity: 5+ events in 60 minutes
    ordered=sorted(txs,key=lambda t:_dt(t.timestamp))
    for i,t in enumerate(ordered):
        window=[x for x in ordered[i:] if _dt(x.timestamp)-_dt(t.timestamp) <= timedelta(minutes=60)]
        if len(window)>=5:
            alerts.append(_alert(case_id,'TM_RAPID_VELOCITY','HIGH',0.86,['5+ transactions observed within a 60-minute sliding window'],window,evidence_base)); break

    # Pattern 3: high-risk corridor; identity risk context strengthens severity/explanation
    corridor=[t for t in txs if t.counterparty_country in HIGH_RISK_COUNTRIES]
    if corridor:
        reasons=['counterparty country is in synthetic high-risk corridor set']
        sev='MEDIUM'; score=.68
        if profile.identity_status != 'VERIFIED' or profile.residency_country in HIGH_RISK_COUNTRIES or 'KYC_REFRESH_DUE' in profile.risk_flags:
            reasons.append('IDENTITY_CONTEXT: unresolved/stale/high-risk identity context increases monitoring concern'); sev='HIGH'; score=.88
        alerts.append(_alert(case_id,'TM_HIGH_RISK_CORRIDOR',sev,score,reasons,corridor,evidence_base))

    # Pattern 4: expected activity deviation from KYC profile
    total=sum(t.amount for t in txs)
    expected=profile.expected_monthly_turnover
    if expected and total > expected*1.75:
        alerts.append(_alert(case_id,'TM_EXPECTED_ACTIVITY_DEVIATION','HIGH',0.84,[f'observed synthetic period turnover {total:.2f} exceeds 1.75x KYC expected turnover {expected:.2f}','KYC_PROFILE_DEPENDENCY'],txs,evidence_base+[f'customer_context:{case_id}']))

    # Pattern 5: pass-through/funnel — large credits followed by near-equal debits quickly
    credits=[t for t in txs if t.direction=='CREDIT']
    debits=[t for t in txs if t.direction=='DEBIT']
    pairs=[]
    for c in credits:
        for d in debits:
            delta=_dt(d.timestamp)-_dt(c.timestamp)
            if timedelta(0) <= delta <= timedelta(hours=6) and abs(d.amount-c.amount)/c.amount <= .08 and c.amount >= 5000:
                pairs.extend([c,d])
    uniq={t.transaction_id:t for t in pairs}
    if len(uniq)>=4:
        p=list(uniq.values())
        alerts.append(_alert(case_id,'TM_PASS_THROUGH','HIGH',0.89,['multiple large credits rapidly followed by near-equal debits','FUNNEL_OR_PASS_THROUGH_BEHAVIOR'],p,evidence_base))

    rank={'LOW':0,'MEDIUM':1,'HIGH':2,'CRITICAL':3}
    overall='LOW' if not alerts else max((a.severity for a in alerts), key=lambda s:rank[s])
    return MonitoringResult(case_id=case_id,overall_risk=overall,alerts=alerts,received_transaction_count=len(received),processed_transaction_count=len(txs),hook_warnings=warnings)
