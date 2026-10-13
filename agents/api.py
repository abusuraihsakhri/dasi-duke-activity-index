"""
FastAPI REST API Server for Dasi Duke Activity Index.
"""
from typing import Dict, Any, List
from pathlib import Path
from fastapi.responses import FileResponse
from dasi_index import DASI_ITEMS, calculate_metrics
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from .base import AuditLogger, PHIGuard
from .models import SystemTaskPayload, ConsensusDossier
from .supervisor import SystemSupervisor

supervisor = SystemSupervisor(model_provider="mock")

app = FastAPI(
    title="Dasi Duke Activity Index API",
    description="Enterprise Distributed Component Platform (Clinical & Biomedical AI)",
    version="3.0.0-ENTERPRISE",
)


class ChatRequest(BaseModel):
    query: str


@app.get("/health")
def health():
    return {"status": "HEALTHY", "service": "dasi-duke-activity-index", "domain": "Clinical & Biomedical AI", "standard": "CAP / CLSI / ISO Standards", "version": "3.0.0-ENTERPRISE"}


@app.get("/metrics")
def metrics():
    return {
        "dossiers_processed_total": len(supervisor.dossier_registry),
        "audit_blocks_total": len(AuditLogger.get_trail()),
        "system_status": "NOMINAL_OPTIMAL"
    }


@app.post("/api/audit")
def api_audit(payload: SystemTaskPayload):
    dossier = supervisor.process_task(payload)
    return dossier.to_dict()


@app.post("/api/chat")
def api_chat(req: ChatRequest):
    try:
        ans = supervisor.query_supervisory_chat(req.query)
        return {"response": ans}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/audit/logs")
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
