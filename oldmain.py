from fastapi import FastAPI

from backend.app.gagf.schemas import (
    AdaptiveState,
    AdaptiveStateSnapshot,
    EvidenceConfidence,
)

from backend.app.gagf.gpl_loader import GPLLoader
from backend.app.gagf.arbitration_service import ArbitrationService

app = FastAPI(title="GAGF Kernel MVP")


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

    gpl = GPLLoader(
        "backend/app/gagf/policies/gpl_v0_1.yaml"
    )

    arbiter = ArbitrationService(gpl)

    decision = arbiter.arbitrate(
        snapshot,
        active_strategy="Normal",
        proposal="continue",
    )

    return decision