import logging, os, uuid
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from .models import VerifyDocumentRequest, DocumentResult, CaseResult
from .service import verify_document, verify_case
from .repository import list_cases

logging.basicConfig(level=os.getenv('LOG_LEVEL','INFO'),format='%(asctime)s %(levelname)s %(message)s')
log=logging.getLogger('kyc-v1')
app=FastAPI(title='AI FDE Brownfield KYC Repo 1.0',version='1.0.0',description='Synthetic training service; not for real identity decisions.')

@app.middleware('http')
async def correlation(request: Request, call_next):
    cid=request.headers.get('x-correlation-id') or str(uuid.uuid4())
    response=await call_next(request); response.headers['x-correlation-id']=cid
    log.info('request method=%s path=%s status=%s correlation_id=%s',request.method,request.url.path,response.status_code,cid)
    return response

@app.exception_handler(FileNotFoundError)
async def not_found(_request, exc):
    return JSONResponse(status_code=404,content={'detail':f'unknown synthetic identifier: {exc.args[0]}'})

@app.exception_handler(ValueError)
async def bad_identifier(_request, exc):
    return JSONResponse(status_code=400,content={'detail':str(exc)})

@app.get('/health/live')
def live(): return {'status':'ok'}

@app.get('/health/ready')
def ready():
    return {'status':'ready','offline_ocr':True,'dataset_cases':len(list_cases())}

@app.get('/v1/cases')
def cases():
    return [{'case_id':x['case_id'],'scenario':x['scenario'],'document_ids':x['document_ids']} for x in list_cases()]

@app.post('/v1/documents/verify',response_model=DocumentResult)
def document_verify(req: VerifyDocumentRequest): return verify_document(req.document_id)

@app.post('/v1/cases/{case_id}/verify',response_model=CaseResult)
def case_verify(case_id: str): return verify_case(case_id)


# --- Integrated Identity + Compliance Monitoring APIs (v2) ---
from .identity import build_identity_profile
from .monitoring import evaluate_transactions
from .compliance import evaluate_compliance_case
from .review import submit_review_decision, list_review_decisions, UnauthorizedReviewAction
from .models_v2 import IdentityProfile, MonitoringResult, ComplianceCaseResult, ReviewDecision, ReviewDecisionRequest

@app.exception_handler(UnauthorizedReviewAction)
async def unauthorized_review(_request, exc):
    return JSONResponse(status_code=403,content={'detail':str(exc)})

@app.post('/v2/identity/cases/{case_id}/profile', response_model=IdentityProfile)
def identity_profile(case_id: str):
    return build_identity_profile(case_id)

@app.post('/v2/monitoring/cases/{case_id}/evaluate', response_model=MonitoringResult)
def transaction_monitoring(case_id: str):
    return evaluate_transactions(case_id)

@app.post('/v2/compliance/cases/{case_id}/evaluate', response_model=ComplianceCaseResult)
def compliance_case(case_id: str):
    return evaluate_compliance_case(case_id)

@app.post('/v2/compliance/cases/{case_id}/review', response_model=ReviewDecision)
def review_case(case_id: str, req: ReviewDecisionRequest):
    # CH-13: governed, auditable HITL override channel - never mutates the deterministic
    # evaluation above; see src/review.py.
    return submit_review_decision(case_id, req.reviewer_id, req.reviewer_role, req.new_disposition, req.rationale)

@app.get('/v2/compliance/cases/{case_id}/reviews', response_model=list[ReviewDecision])
def review_history(case_id: str):
    return list_review_decisions(case_id)
