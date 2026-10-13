"""
FastAPI REST API Server for Dasi Duke Activity Index.
"""
from typing import Dict, Any, List, Optional
import os
import hmac
from pathlib import Path
from fastapi.responses import FileResponse
from dasi_index import DASI_ITEMS, calculate_metrics
from fastapi import FastAPI, HTTPException, Depends, Header
from pydantic import BaseModel
from .base import AuditLogger, PHIGuard
from .models import SystemTaskPayload, ConsensusDossier
from .supervisor import SystemSupervisor

supervisor = SystemSupervisor(model_provider="mock")

app = FastAPI(
    title="Dasi Duke Activity Index API",
    description="DASI calculator and optional authenticated legacy audit demo",
    version="1.0.0",
)




def require_audit_api_key(x_audit_key: Optional[str] = Header(default=None)):
    """Protect legacy audit/chat endpoints; never expose them without a key."""
    configured = os.environ.get("AUDIT_API_KEY")
    if not configured:
        raise HTTPException(status_code=503, detail="Audit service unavailable: AUDIT_API_KEY is not configured")
    if not x_audit_key or not hmac.compare_digest(x_audit_key, configured):
        raise HTTPException(status_code=401, detail="Invalid audit API key")

class ChatRequest(BaseModel):
    query: str


@app.get("/health")
def health():
    return {"status": "HEALTHY", "service": "dasi-duke-activity-index", "domain": "DASI scoring with optional legacy audit demo", "version": "1.0.0"}


@app.get("/metrics")
def metrics():
    return {
        "dossiers_processed_total": len(supervisor.dossier_registry),
        "audit_blocks_total": len(AuditLogger.get_trail()),
        "system_status": "AVAILABLE"
    }


@app.post("/api/audit", dependencies=[Depends(require_audit_api_key)])
def api_audit(payload: SystemTaskPayload):
    dossier = supervisor.process_task(payload)
    return dossier.to_dict()


@app.post("/api/chat", dependencies=[Depends(require_audit_api_key)])
def api_chat(req: ChatRequest):
    try:
        ans = supervisor.query_supervisory_chat(req.query)
        return {"response": ans}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/audit/logs", dependencies=[Depends(require_audit_api_key)])
def api_audit_logs():
    return {"audit_trail": AuditLogger.get_trail(), "verified": AuditLogger.verify_integrity()}


class DasiRequest(BaseModel):
    responses: Dict[str, int]


@app.get("/", include_in_schema=False)
def index():
    """Serve the same standalone questionnaire used on GitHub Pages."""
    return FileResponse(Path(__file__).resolve().parent.parent / "web" / "index.html")


@app.post("/api/dasi")
def api_dasi(request: DasiRequest):
    """Evaluate a complete, explicit twelve-item DASI questionnaire."""
    if set(request.responses) != set(DASI_ITEMS):
        raise HTTPException(status_code=422, detail="Exactly v1-v12 are required")
    try:
        return calculate_metrics(**request.responses)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
