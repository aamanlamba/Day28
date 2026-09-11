from __future__ import annotations
from collections import defaultdict
from datetime import datetime, timedelta
from .repository import load_json
from .identity import build_identity_profile
from .models_v2 import TransactionEvent, MonitoringAlert, MonitoringResult
from .policy import get_policy

def _dt(s: str) -> datetime:
    return datetime.fromisoformat(s.replace('Z','+00:00'))

def _alert(case_id, code, severity, score, reasons, txs, evidence, policy_version):
    return MonitoringAlert(alert_id=f'{case_id}-{code}-{len(txs)}', case_id=case_id, pattern_code=code, severity=severity, score=score, reasons=reasons, transaction_ids=[t.transaction_id for t in txs], evidence_refs=evidence, policy_version=policy_version)

def _dedupe(events):
    """CH-06: a repeated transaction_id with different content is a data-integrity
    signal, not routine redelivery - distinguish it from an exact duplicate rather than
    silently applying the same warning to both."""
    out=[]; seen={}; warnings=[]
    for e in events:
        if e.transaction_id in seen:
            if e != seen[e.transaction_id]:
                warnings.append('CONFLICTING_DUPLICATE_TRANSACTION')
            else:
                warnings.append('DUPLICATE_EVENT_SUPPRESSED')
            continue
        seen[e.transaction_id]=e; out.append(e)
    return out, sorted(set(warnings))

def _filter_case_mismatch(events, case_id):
    """CH-01: an event's own case_id must agree with the case it was loaded under.
    A disagreeing event is a false-join risk and must be quarantined, not trusted."""
    out=[]; warnings=[]
    for e in events:
        if e.case_id != case_id:
            warnings.append('TRANSACTION_CASE_ID_MISMATCH'); continue
        out.append(e)
    return out, sorted(set(warnings))

def evaluate_transactions(case_id: str, policy_version: str | None = None) -> MonitoringResult:
    # CH-14: every threshold below comes from one versioned, replayable policy bundle
    # instead of scattered module constants - re-run with an explicit policy_version to
    # reproduce a past decision even after the current policy has changed.
    policy=get_policy(policy_version)
    raw=load_json('transactions', case_id)
    received=[TransactionEvent(**x) for x in raw['transactions']]
    linked,mismatch_warnings=_filter_case_mismatch(received, case_id)
    deduped,dedupe_warnings=_dedupe(linked)
    # CH-07: pattern windows must be computed in event-time order, not delivery order,
    # so which window/cluster is reported never depends on arrival sequence.
    txs=sorted(deduped, key=lambda t: _dt(t.timestamp))
    warnings=sorted(set(mismatch_warnings+dedupe_warnings))
    profile=build_identity_profile(case_id)
    alerts=[]
    evidence_base=[f'identity:{case_id}'] + profile.evidence_refs

    def alert(code, severity, score, reasons, txs_, evidence):
        return _alert(case_id, code, severity, score, reasons, txs_, evidence, policy['version'])

    # Pattern 1: structuring / threshold avoidance: 3+ same-direction transfers clustered just below 10k in 24h
    near=[t for t in txs if policy['structuring_min_amount'] <= t.amount < policy['structuring_max_amount'] and t.direction=='CREDIT']
    for anchor in near:
        window=[t for t in near if abs(_dt(t.timestamp)-_dt(anchor.timestamp)) <= policy['structuring_window']]
        if len(window) >= policy['structuring_min_count']:
            # CH-12: cite the actual observed count, not just the rule's static threshold.
            reason=f"{len(window)} credits between {policy['structuring_min_amount']} and {policy['structuring_max_amount']-1} observed within {policy['structuring_window']} (rule threshold: {policy['structuring_min_count']}+)"
            alerts.append(alert('TM_STRUCTURING','HIGH',0.90,[reason,'RULE_THRESHOLD_AVOIDANCE'],window,evidence_base)); break

    # Pattern 2: rapid velocity: 5+ events in 60 minutes
    ordered=sorted(txs,key=lambda t:_dt(t.timestamp))
    for i,t in enumerate(ordered):
        window=[x for x in ordered[i:] if _dt(x.timestamp)-_dt(t.timestamp) <= policy['velocity_window']]
        if len(window)>=policy['velocity_min_count']:
            # CH-12: cite the actual observed count, not just the rule's static threshold.
            reason=f"{len(window)} transactions observed within {policy['velocity_window']} (rule threshold: {policy['velocity_min_count']}+)"
            alerts.append(alert('TM_RAPID_VELOCITY','HIGH',0.86,[reason],window,evidence_base)); break

    # Pattern 3: high-risk corridor; identity risk context strengthens severity/explanation.
    # CH-10: each condition is checked and cited independently so an alert names exactly
    # which identity field(s) drove the escalation, not a single generic sentence.
    corridor=[t for t in txs if t.counterparty_country in policy['high_risk_countries']]
    if corridor:
        # CH-12: cite the actual matched countries, not just "the corridor set" generically.
        countries=sorted({t.counterparty_country for t in corridor})
        reasons=[f'{len(corridor)} transaction(s) to counterparty_country in {countries} (synthetic high-risk corridor set)']
        context_reasons=[]
        if profile.identity_status != 'VERIFIED':
            context_reasons.append(f'IDENTITY_CONTEXT: identity_status={profile.identity_status} (not VERIFIED)')
        if profile.residency_country in policy['high_risk_countries']:
            context_reasons.append(f'IDENTITY_CONTEXT: residency_country={profile.residency_country} is in the high-risk corridor set')
        if 'KYC_REFRESH_DUE' in profile.risk_flags:
            context_reasons.append('IDENTITY_CONTEXT: KYC_REFRESH_DUE')
        if 'DOCUMENT_QUALITY_DEGRADED' in profile.risk_flags:
            context_reasons.append('IDENTITY_CONTEXT: DOCUMENT_QUALITY_DEGRADED (weak evidence confidence)')
        if context_reasons:
            reasons.extend(context_reasons); sev='HIGH'; score=.88
        else:
            sev='MEDIUM'; score=.68
        alerts.append(alert('TM_HIGH_RISK_CORRIDOR',sev,score,reasons,corridor,evidence_base))

    # Pattern 4: expected activity deviation from KYC profile
    total=sum(t.amount for t in txs)
    expected=profile.expected_monthly_turnover
    if expected and total > expected*1.75:
        alerts.append(alert('TM_EXPECTED_ACTIVITY_DEVIATION','HIGH',0.84,[f'observed synthetic period turnover {total:.2f} exceeds 1.75x KYC expected turnover {expected:.2f}','KYC_PROFILE_DEPENDENCY'],txs,evidence_base+[f'customer_context:{case_id}']))

    # Pattern 5: pass-through/funnel — large credits followed by near-equal debits quickly
    credits=[t for t in txs if t.direction=='CREDIT']
    debits=[t for t in txs if t.direction=='DEBIT']
    pairs=[]
    for c in credits:
        for d in debits:
            delta=_dt(d.timestamp)-_dt(c.timestamp)
            if timedelta(0) <= delta <= policy['pass_through_window'] and abs(d.amount-c.amount)/c.amount <= policy['pass_through_amount_tolerance'] and c.amount >= policy['pass_through_min_credit_amount']:
                pairs.extend([c,d])
    uniq={t.transaction_id:t for t in pairs}
    if len(uniq)>=policy['pass_through_min_matched_count']:
        p=list(uniq.values())
        # CH-12: cite the actual matched pair count, not just a static description.
        reason=f"{len(uniq)//2} credit/debit pair(s) matched within {policy['pass_through_window']} at <={policy['pass_through_amount_tolerance']:.0%} amount tolerance"
        alerts.append(alert('TM_PASS_THROUGH','HIGH',0.89,[reason,'FUNNEL_OR_PASS_THROUGH_BEHAVIOR'],p,evidence_base))

    rank={'LOW':0,'MEDIUM':1,'HIGH':2,'CRITICAL':3}
    overall='LOW' if not alerts else max((a.severity for a in alerts), key=lambda s:rank[s])
    return MonitoringResult(case_id=case_id,overall_risk=overall,alerts=alerts,received_transaction_count=len(received),processed_transaction_count=len(txs),hook_warnings=warnings,policy_version=policy['version'])
