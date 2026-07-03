import shutil
from pathlib import Path

from fastapi import UploadFile, File
from backend.app.gagf.decision_ledger import DecisionLedger
from typing import List
from uuid import uuid4
from backend.app.services.dashboard_service import DashboardService
from fastapi import FastAPI
from fastapi.responses import FileResponse
from backend.app.services.ingestion_service import IngestionService
from fastapi.staticfiles import StaticFiles
app = FastAPI(title="GAGF Kernel MVP")
app.mount("/static", StaticFiles(directory="backend/app/static"), name="static")


from backend.app.gagf.schemas import (
    AdaptiveState,
    AdaptiveStateSnapshot,
    EvidenceConfidence,
    RawSecurityEvent,
)

from backend.app.gagf.metric_adapter import MetricAdapter
from backend.app.gagf.snapshot_ledger import SnapshotLedger
from backend.app.gagf.gpl_loader import GPLLoader
from backend.app.gagf.arbitration_service import ArbitrationService

app = FastAPI(title="GAGF Kernel MVP")

app.mount(
    "/static",
    StaticFiles(directory="backend/app/static"),
    name="static"
)

@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/arbitrate")
def arbitrate(state: AdaptiveState):
    snapshot = AdaptiveStateSnapshot(
        snapshot_id="api-demo",
        tenant_id="demo",
        work_item_id="demo",
        status="VALID",
        adaptive_state=state,
        evidence_confidence=EvidenceConfidence(
            score=1.0,
            factors={
                "timestamp_quality": 1.0,
                "sensor_reliability": 1.0,
                "cross_source_agreement": 1.0,
                "telemetry_completeness": 1.0,
            },
        ),
        evidence=[],
        timestamp_quality_distribution={},
    )

    gpl = GPLLoader("backend/app/gagf/policies/gpl_v0_1.yaml")
    arbiter = ArbitrationService(gpl)

    decision = arbiter.arbitrate(
        snapshot,
        active_strategy="Normal",
        proposal="continue",
    )

    return decision


@app.post("/snapshot")
def create_snapshot(events: List[RawSecurityEvent]):
    adapter_result = MetricAdapter().build_snapshot(events)

    timestamp_quality_distribution = {
        "SOURCE_OCCURRED_AT": sum(1 for event in events if event.timestamp_quality == "SOURCE_OCCURRED_AT"),
        "BACKFILLED_FROM_CREATED_AT": sum(1 for event in events if event.timestamp_quality == "BACKFILLED_FROM_CREATED_AT"),
        "MISSING_TIMESTAMP": sum(1 for event in events if event.timestamp_quality == "MISSING_TIMESTAMP"),
    }

    status = "INVALID" if timestamp_quality_distribution["MISSING_TIMESTAMP"] > 0 else "VALID"

    snapshot = AdaptiveStateSnapshot(
        snapshot_id=str(uuid4()),
        tenant_id="demo",
        work_item_id="demo",
        status=status,
        adaptive_state=adapter_result.adaptive_state,
        evidence_confidence=adapter_result.evidence_confidence,
        evidence=adapter_result.evidence,
        timestamp_quality_distribution=timestamp_quality_distribution,
    )

    SnapshotLedger().save_snapshot(
        snapshot,
        normalization_applied=adapter_result.normalization_applied,
    )

    return snapshot
@app.get("/snapshots")
def list_snapshots():
    return SnapshotLedger().list_snapshots()

@app.get("/decisions")
def list_decisions():
    return DecisionLedger().list_decisions()


@app.get("/decision/{decision_id}")
def get_decision(decision_id: str):
    decision = DecisionLedger().get_decision(decision_id)

    if decision is None:
        return {"error": "decision_not_found"}

    return decision
@app.get("/dashboard")
def dashboard():
    return DashboardService().get_dashboard_summary()
@app.get("/console")
def console():
    return FileResponse("backend/app/static/console.html")
@app.post("/upload-csv")
def upload_csv(file: UploadFile = File(...)):
    upload_dir = Path("uploads")
    upload_dir.mkdir(exist_ok=True)

    file_path = upload_dir / file.filename

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    result = IngestionService().ingest_csv(str(file_path))

    return result