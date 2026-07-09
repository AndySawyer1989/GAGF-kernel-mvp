import shutil
from pathlib import Path
from typing import List
from uuid import uuid4

from fastapi import FastAPI, File, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.app.connectors.defender_connector import DefenderConnector
from backend.app.connectors.entra_connector import EntraConnector
from backend.app.connectors.github_connector import GitHubConnector
from backend.app.connectors.jira_connector import JiraConnector
from backend.app.connectors.okta_connector import OktaConnector
from backend.app.connectors.sentinelone_connector import SentinelOneConnector
from backend.app.connectors.servicenow_connector import ServiceNowConnector
from backend.app.gagf.arbitration_service import ArbitrationService
from backend.app.gagf.decision_ledger import DecisionLedger
from backend.app.gagf.gpl_loader import GPLLoader
from backend.app.gagf.metric_adapter import MetricAdapter
from backend.app.gagf.source_registry import SourceRegistry
from backend.app.gagf.schemas import (
    AdaptiveState,
    AdaptiveStateSnapshot,
    EvidenceConfidence,
    RawSecurityEvent,
)
from backend.app.gagf.snapshot_ledger import SnapshotLedger
from backend.app.services.dashboard_service import DashboardService
from backend.app.services.ingestion_service import IngestionService


GPL_POLICY_PATH = "backend/app/gagf/policies/gpl_v0_1.yaml"

app = FastAPI(title="GAGF Kernel MVP")

app.mount(
    "/static",
    StaticFiles(directory="backend/app/static"),
    name="static",
)


def get_arbiter() -> ArbitrationService:
    gpl = GPLLoader(GPL_POLICY_PATH)
    return ArbitrationService(gpl)


def validate_github_payload(payload: dict):
    errors = []

    if "events" not in payload:
        errors.append("missing_events_field")
        return errors

    events = payload.get("events")

    if not isinstance(events, list):
        errors.append("events_must_be_a_list")
        return errors

    if len(events) == 0:
        errors.append("events_list_is_empty")
        return errors

    for index, event in enumerate(events):
        if not isinstance(event, dict):
            errors.append(f"event_{index}_must_be_an_object")
            continue

        if not event.get("id"):
            errors.append(f"event_{index}_missing_id")

        if not event.get("event_name"):
            errors.append(f"event_{index}_missing_event_name")

        if not event.get("created_at"):
            errors.append(f"event_{index}_missing_created_at")

    return errors


def validate_servicenow_payload(payload: dict):
    errors = []

    if "events" not in payload:
        errors.append("missing_events_field")
        return errors

    events = payload.get("events")

    if not isinstance(events, list):
        errors.append("events_must_be_a_list")
        return errors

    if len(events) == 0:
        errors.append("events_list_is_empty")
        return errors

    for index, event in enumerate(events):
        if not isinstance(event, dict):
            errors.append(f"event_{index}_must_be_an_object")
            continue

        if not event.get("sys_id"):
            errors.append(f"event_{index}_missing_sys_id")

        if not event.get("table"):
            errors.append(f"event_{index}_missing_table")

        if not event.get("opened_at") and not event.get("sys_created_on"):
            errors.append(f"event_{index}_missing_timestamp")

    return errors


def validate_defender_payload(payload: dict):
    errors = []

    if "events" not in payload:
        errors.append("missing_events_field")
        return errors

    events = payload.get("events")

    if not isinstance(events, list):
        errors.append("events_must_be_a_list")
        return errors

    if len(events) == 0:
        errors.append("events_list_is_empty")
        return errors

    for index, event in enumerate(events):
        if not isinstance(event, dict):
            errors.append(f"event_{index}_must_be_an_object")
            continue

        if not event.get("id") and not event.get("alertId") and not event.get("incidentId"):
            errors.append(f"event_{index}_missing_id")

        if not event.get("title"):
            errors.append(f"event_{index}_missing_title")

        if not event.get("createdDateTime") and not event.get("lastUpdateDateTime"):
            errors.append(f"event_{index}_missing_timestamp")

    return errors


def validate_jira_payload(payload: dict):
    errors = []

    if "events" not in payload:
        errors.append("missing_events_field")
        return errors

    events = payload.get("events")

    if not isinstance(events, list):
        errors.append("events_must_be_a_list")
        return errors

    if len(events) == 0:
        errors.append("events_list_is_empty")
        return errors

    for index, event in enumerate(events):
        if not isinstance(event, dict):
            errors.append(f"event_{index}_must_be_an_object")
            continue

        if not event.get("id"):
            errors.append(f"event_{index}_missing_id")

        if not event.get("key"):
            errors.append(f"event_{index}_missing_key")

        if not event.get("status"):
            errors.append(f"event_{index}_missing_status")

        if not event.get("created") and not event.get("updated"):
            errors.append(f"event_{index}_missing_timestamp")

    return errors


def validate_okta_payload(payload: dict):
    errors = []

    if "events" not in payload:
        errors.append("missing_events_field")
        return errors

    events = payload.get("events")

    if not isinstance(events, list):
        errors.append("events_must_be_a_list")
        return errors

    if len(events) == 0:
        errors.append("events_list_is_empty")
        return errors

    for index, event in enumerate(events):
        if not isinstance(event, dict):
            errors.append(f"event_{index}_must_be_an_object")
            continue

        if not event.get("uuid"):
            errors.append(f"event_{index}_missing_uuid")

        if not event.get("eventType"):
            errors.append(f"event_{index}_missing_eventType")

        if not event.get("published"):
            errors.append(f"event_{index}_missing_published")

    return errors


def validate_entra_payload(payload: dict):
    errors = []

    if "events" not in payload:
        errors.append("missing_events_field")
        return errors

    events = payload.get("events")

    if not isinstance(events, list):
        errors.append("events_must_be_a_list")
        return errors

    if len(events) == 0:
        errors.append("events_list_is_empty")
        return errors

    for index, event in enumerate(events):
        if not isinstance(event, dict):
            errors.append(f"event_{index}_must_be_an_object")
            continue

        if not event.get("id"):
            errors.append(f"event_{index}_missing_id")

        if not event.get("activityDisplayName"):
            errors.append(f"event_{index}_missing_activityDisplayName")

        if not event.get("createdDateTime"):
            errors.append(f"event_{index}_missing_createdDateTime")

    return errors


def validate_sentinelone_payload(payload: dict):
    errors = []

    if "events" not in payload:
        errors.append("missing_events_field")
        return errors

    events = payload.get("events")

    if not isinstance(events, list):
        errors.append("events_must_be_a_list")
        return errors

    if len(events) == 0:
        errors.append("events_list_is_empty")
        return errors

    for index, event in enumerate(events):
        if not isinstance(event, dict):
            errors.append(f"event_{index}_must_be_an_object")
            continue

        if (
            not event.get("id")
            and not event.get("threatId")
            and not event.get("activityUuid")
            and not event.get("uuid")
        ):
            errors.append(f"event_{index}_missing_id")

        if not event.get("eventType"):
            errors.append(f"event_{index}_missing_eventType")

        if (
            not event.get("threatName")
            and not event.get("classification")
            and not event.get("eventType")
        ):
            errors.append(f"event_{index}_missing_threat_context")

        if (
            not event.get("createdAt")
            and not event.get("updatedAt")
            and not event.get("detectedAt")
            and not event.get("mitigatedAt")
        ):
            errors.append(f"event_{index}_missing_createdAt")
            errors.append(f"event_{index}_missing_timestamp")

    return errors

@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/version")
def version():
    return {
        "version": "0.4.0",
        "release": "evidence-expansion",
        "sprint": "3.3",
        "status": "complete",
    }


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

    decision = get_arbiter().arbitrate(
        snapshot=snapshot,
        active_strategy="Normal",
        proposal="continue",
    )

    return decision


@app.post("/snapshot")
def create_snapshot(events: List[RawSecurityEvent]):
    adapter_result = MetricAdapter().build_snapshot(events)

    timestamp_quality_distribution = {
        "SOURCE_OCCURRED_AT": sum(
            1 for event in events if event.timestamp_quality == "SOURCE_OCCURRED_AT"
        ),
        "BACKFILLED_FROM_CREATED_AT": sum(
            1 for event in events if event.timestamp_quality == "BACKFILLED_FROM_CREATED_AT"
        ),
        "MISSING_TIMESTAMP": sum(
            1 for event in events if event.timestamp_quality == "MISSING_TIMESTAMP"
        ),
    }

    status = (
        "INVALID"
        if timestamp_quality_distribution["MISSING_TIMESTAMP"] > 0
        else "VALID"
    )

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

@app.get("/sources")
def list_sources():
    return {
        "status": "ok",
        "sources": SourceRegistry().list_sources(),
    }
@app.get("/sources/{source_system}")
def get_source(source_system: str):
    source = SourceRegistry().get_source(source_system)

    if source is None:
        return {
            "status": "failed",
            "error": "source_not_found",
            "source_system": source_system,
        }

    return {
        "status": "ok",
        "source": source,
    }

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


@app.post("/ingest/github")
def ingest_github(payload: dict):
    validation_errors = validate_github_payload(payload)

    if validation_errors:
        return {
            "status": "failed",
            "source_system": "github",
            "events_normalized": 0,
            "errors": validation_errors,
        }

    connector = GitHubConnector()
    events = connector.normalize_events(payload.get("events", []))

    adapter_result = MetricAdapter().build_snapshot(events)

    snapshot = AdaptiveStateSnapshot(
        snapshot_id=f"github-{uuid4()}",
        tenant_id="demo",
        work_item_id="github-ingestion",
        status="VALID",
        adaptive_state=adapter_result.adaptive_state,
        evidence_confidence=adapter_result.evidence_confidence,
        evidence=[event.event_id for event in events],
        timestamp_quality_distribution={
            "SOURCE_OCCURRED_AT": len(events),
            "BACKFILLED_FROM_CREATED_AT": 0,
            "MISSING_TIMESTAMP": 0,
        },
    )

    SnapshotLedger().save_snapshot(
        snapshot,
        normalization_applied=adapter_result.normalization_applied,
    )

    decision = get_arbiter().arbitrate(
        snapshot=snapshot,
        active_strategy="Normal",
        proposal="continue",
    )

    decision_id = DecisionLedger().save_decision(
        decision,
        snapshot.snapshot_id,
    )

    return {
        "status": "ingested",
        "source_system": "github",
        "events_normalized": len(events),
        "snapshot_id": snapshot.snapshot_id,
        "snapshot_status": snapshot.status,
        "decision_id": decision_id,
        "selected_strategy": decision.selected_strategy,
        "kernel_decision": decision.kernel_decision,
        "reason": decision.reason,
    }


@app.post("/ingest/servicenow")
def ingest_servicenow(payload: dict):
    validation_errors = validate_servicenow_payload(payload)

    if validation_errors:
        return {
            "status": "failed",
            "source_system": "servicenow",
            "events_normalized": 0,
            "errors": validation_errors,
        }

    connector = ServiceNowConnector()
    events = connector.normalize_events(payload.get("events", []))

    adapter_result = MetricAdapter().build_snapshot(events)

    snapshot = AdaptiveStateSnapshot(
        snapshot_id=f"servicenow-{uuid4()}",
        tenant_id="demo",
        work_item_id="servicenow-ingestion",
        status="VALID",
        adaptive_state=adapter_result.adaptive_state,
        evidence_confidence=adapter_result.evidence_confidence,
        evidence=[event.event_id for event in events],
        timestamp_quality_distribution={
            "SOURCE_OCCURRED_AT": len(events),
            "BACKFILLED_FROM_CREATED_AT": 0,
            "MISSING_TIMESTAMP": 0,
        },
    )

    SnapshotLedger().save_snapshot(
        snapshot,
        normalization_applied=adapter_result.normalization_applied,
    )

    decision = get_arbiter().arbitrate(
        snapshot=snapshot,
        active_strategy="Normal",
        proposal="continue",
    )

    decision_id = DecisionLedger().save_decision(
        decision,
        snapshot.snapshot_id,
    )

    return {
        "status": "ingested",
        "source_system": "servicenow",
        "events_normalized": len(events),
        "snapshot_id": snapshot.snapshot_id,
        "snapshot_status": snapshot.status,
        "decision_id": decision_id,
        "selected_strategy": decision.selected_strategy,
        "kernel_decision": decision.kernel_decision,
        "reason": decision.reason,
    }


@app.post("/ingest/jira")
def ingest_jira(payload: dict):
    validation_errors = validate_jira_payload(payload)

    if validation_errors:
        return {
            "status": "failed",
            "source_system": "jira",
            "events_normalized": 0,
            "errors": validation_errors,
        }

    connector = JiraConnector()
    events = connector.normalize_events(payload.get("events", []))

    adapter_result = MetricAdapter().build_snapshot(events)

    snapshot = AdaptiveStateSnapshot(
        snapshot_id=f"jira-{uuid4()}",
        tenant_id="demo",
        work_item_id="jira-ingestion",
        status="VALID",
        adaptive_state=adapter_result.adaptive_state,
        evidence_confidence=adapter_result.evidence_confidence,
        evidence=[event.event_id for event in events],
        timestamp_quality_distribution={
            "SOURCE_OCCURRED_AT": len(events),
            "BACKFILLED_FROM_CREATED_AT": 0,
            "MISSING_TIMESTAMP": 0,
        },
    )

    SnapshotLedger().save_snapshot(
        snapshot,
        normalization_applied=adapter_result.normalization_applied,
    )

    decision = get_arbiter().arbitrate(
        snapshot=snapshot,
        active_strategy="Normal",
        proposal="continue",
    )

    decision_id = DecisionLedger().save_decision(
        decision,
        snapshot.snapshot_id,
    )

    return {
        "status": "ingested",
        "source_system": "jira",
        "events_normalized": len(events),
        "snapshot_id": snapshot.snapshot_id,
        "snapshot_status": snapshot.status,
        "decision_id": decision_id,
        "selected_strategy": decision.selected_strategy,
        "kernel_decision": decision.kernel_decision,
        "reason": decision.reason,
    }


@app.post("/ingest/okta")
def ingest_okta(payload: dict):
    validation_errors = validate_okta_payload(payload)

    if validation_errors:
        return {
            "status": "failed",
            "source_system": "okta",
            "events_normalized": 0,
            "errors": validation_errors,
        }

    connector = OktaConnector()
    events = connector.normalize_events(payload.get("events", []))

    adapter_result = MetricAdapter().build_snapshot(events)

    snapshot = AdaptiveStateSnapshot(
        snapshot_id=f"okta-{uuid4()}",
        tenant_id="demo",
        work_item_id="okta-ingestion",
        status="VALID",
        adaptive_state=adapter_result.adaptive_state,
        evidence_confidence=adapter_result.evidence_confidence,
        evidence=[event.event_id for event in events],
        timestamp_quality_distribution={
            "SOURCE_OCCURRED_AT": len(events),
            "BACKFILLED_FROM_CREATED_AT": 0,
            "MISSING_TIMESTAMP": 0,
        },
    )

    SnapshotLedger().save_snapshot(
        snapshot,
        normalization_applied=adapter_result.normalization_applied,
    )

    decision = get_arbiter().arbitrate(
        snapshot=snapshot,
        active_strategy="Normal",
        proposal="continue",
    )

    decision_id = DecisionLedger().save_decision(
        decision,
        snapshot.snapshot_id,
    )

    return {
        "status": "ingested",
        "source_system": "okta",
        "events_normalized": len(events),
        "snapshot_id": snapshot.snapshot_id,
        "snapshot_status": snapshot.status,
        "decision_id": decision_id,
        "selected_strategy": decision.selected_strategy,
        "kernel_decision": decision.kernel_decision,
        "reason": decision.reason,
    }


@app.post("/ingest/entra")
def ingest_entra(payload: dict):
    validation_errors = validate_entra_payload(payload)

    if validation_errors:
        return {
            "status": "failed",
            "source_system": "entra",
            "events_normalized": 0,
            "errors": validation_errors,
        }

    connector = EntraConnector()
    events = connector.normalize_events(payload.get("events", []))

    adapter_result = MetricAdapter().build_snapshot(events)

    snapshot = AdaptiveStateSnapshot(
        snapshot_id=f"entra-{uuid4()}",
        tenant_id="demo",
        work_item_id="entra-ingestion",
        status="VALID",
        adaptive_state=adapter_result.adaptive_state,
        evidence_confidence=adapter_result.evidence_confidence,
        evidence=[event.event_id for event in events],
        timestamp_quality_distribution={
            "SOURCE_OCCURRED_AT": len(events),
            "BACKFILLED_FROM_CREATED_AT": 0,
            "MISSING_TIMESTAMP": 0,
        },
    )

    SnapshotLedger().save_snapshot(
        snapshot,
        normalization_applied=adapter_result.normalization_applied,
    )

    decision = get_arbiter().arbitrate(
        snapshot=snapshot,
        active_strategy="Normal",
        proposal="continue",
    )

    decision_id = DecisionLedger().save_decision(
        decision,
        snapshot.snapshot_id,
    )

    return {
        "status": "ingested",
        "source_system": "entra",
        "events_normalized": len(events),
        "snapshot_id": snapshot.snapshot_id,
        "snapshot_status": snapshot.status,
        "decision_id": decision_id,
        "selected_strategy": decision.selected_strategy,
        "kernel_decision": decision.kernel_decision,
        "reason": decision.reason,
    }


@app.post("/ingest/sentinelone")
def ingest_sentinelone(payload: dict):
    validation_errors = validate_sentinelone_payload(payload)

    if validation_errors:
        return {
            "status": "failed",
            "source_system": "sentinelone",
            "events_normalized": 0,
            "errors": validation_errors,
        }

    connector = SentinelOneConnector()
    events = connector.normalize_events(payload.get("events", []))

    adapter_result = MetricAdapter().build_snapshot(events)

    snapshot = AdaptiveStateSnapshot(
        snapshot_id=f"sentinelone-{uuid4()}",
        tenant_id="demo",
        work_item_id="sentinelone-ingestion",
        status="VALID",
        adaptive_state=adapter_result.adaptive_state,
        evidence_confidence=adapter_result.evidence_confidence,
        evidence=[event.event_id for event in events],
        timestamp_quality_distribution={
            "SOURCE_OCCURRED_AT": len(events),
            "BACKFILLED_FROM_CREATED_AT": 0,
            "MISSING_TIMESTAMP": 0,
        },
    )

    SnapshotLedger().save_snapshot(
        snapshot,
        normalization_applied=adapter_result.normalization_applied,
    )

    decision = get_arbiter().arbitrate(
        snapshot=snapshot,
        active_strategy="Normal",
        proposal="continue",
    )

    decision_id = DecisionLedger().save_decision(
        decision,
        snapshot.snapshot_id,
    )

    return {
        "status": "ingested",
        "source_system": "sentinelone",
        "events_normalized": len(events),
        "snapshot_id": snapshot.snapshot_id,
        "snapshot_status": snapshot.status,
        "decision_id": decision_id,
        "selected_strategy": decision.selected_strategy,
        "kernel_decision": decision.kernel_decision,
        "reason": decision.reason,
    }


@app.post("/ingest/defender")
def ingest_defender(payload: dict):
    validation_errors = validate_defender_payload(payload)

    if validation_errors:
        return {
            "status": "failed",
            "source_system": "defender",
            "events_normalized": 0,
            "errors": validation_errors,
        }

    connector = DefenderConnector()
    events = connector.normalize_events(payload.get("events", []))

    adapter_result = MetricAdapter().build_snapshot(events)

    snapshot = AdaptiveStateSnapshot(
        snapshot_id=f"defender-{uuid4()}",
        tenant_id="demo",
        work_item_id="defender-ingestion",
        status="VALID",
        adaptive_state=adapter_result.adaptive_state,
        evidence_confidence=adapter_result.evidence_confidence,
        evidence=[event.event_id for event in events],
        timestamp_quality_distribution={
            "SOURCE_OCCURRED_AT": len(events),
            "BACKFILLED_FROM_CREATED_AT": 0,
            "MISSING_TIMESTAMP": 0,
        },
    )

    SnapshotLedger().save_snapshot(
        snapshot,
        normalization_applied=adapter_result.normalization_applied,
    )

    decision = get_arbiter().arbitrate(
        snapshot=snapshot,
        active_strategy="Normal",
        proposal="continue",
    )

    decision_id = DecisionLedger().save_decision(
        decision,
        snapshot.snapshot_id,
    )

    return {
        "status": "ingested",
        "source_system": "defender",
        "events_normalized": len(events),
        "snapshot_id": snapshot.snapshot_id,
        "snapshot_status": snapshot.status,
        "decision_id": decision_id,
        "selected_strategy": decision.selected_strategy,
        "kernel_decision": decision.kernel_decision,
        "reason": decision.reason,
    }