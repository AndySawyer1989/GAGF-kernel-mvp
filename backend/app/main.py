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
from backend.app.gagf.cross_source_agreement_service import CrossSourceAgreementService
from backend.app.gagf.decision_ledger import DecisionLedger
from backend.app.gagf.evidence_confidence_adapter import EvidenceConfidenceAdapter
from backend.app.gagf.evidence_conflict_service import EvidenceConflictService
from backend.app.gagf.evidence_diagnostics_service import EvidenceDiagnosticsService
from backend.app.gagf.evidence_quality_service import EvidenceQualityService
from backend.app.gagf.friction_signal_detection_service import (
    FrictionSignalDetectionService,
)
from backend.app.gagf.governance_debt_indicator_service import (
    GovernanceDebtIndicatorService,
)
from backend.app.gagf.governance_signal_service import GovernanceSignalService
from backend.app.gagf.governance_signal_summary_service import (
    GovernanceSignalSummaryService,
)
from backend.app.gagf.gpl_loader import GPLLoader
from backend.app.gagf.metric_adapter import MetricAdapter
from backend.app.gagf.schemas import (
    AdaptiveState,
    AdaptiveStateSnapshot,
    EvidenceConfidence,
    RawSecurityEvent,
)
from backend.app.gagf.signal_correlation_service import SignalCorrelationService
from backend.app.gagf.snapshot_diagnostics_ledger import SnapshotDiagnosticsLedger
from backend.app.gagf.snapshot_diagnostics_risk_service import (
    SnapshotDiagnosticsRiskService,
)
from backend.app.gagf.snapshot_diagnostics_summary_service import (
    SnapshotDiagnosticsSummaryService,
)
from backend.app.gagf.snapshot_ledger import SnapshotLedger
from backend.app.gagf.source_category_service import SourceCategoryService
from backend.app.gagf.source_coverage_service import SourceCoverageService
from backend.app.gagf.source_health_service import SourceHealthService
from backend.app.gagf.source_kernel_role_service import SourceKernelRoleService
from backend.app.gagf.source_registry import SourceRegistry
from backend.app.gagf.source_trust_tier_service import SourceTrustTierService
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


def build_snapshot_diagnostics_record(confidence_result: dict) -> dict:
    return {
        "confidence_score": confidence_result["confidence_score"],
        "confidence_band": confidence_result["confidence_band"],
        "evidence_confidence_factors": confidence_result[
            "evidence_confidence"
        ].factors,
        "diagnostics": confidence_result["diagnostics"],
    }


def save_snapshot_diagnostics(snapshot_id: str, confidence_result: dict) -> dict:
    diagnostics_record = build_snapshot_diagnostics_record(confidence_result)

    return SnapshotDiagnosticsLedger().save_diagnostics(
        snapshot_id=snapshot_id,
        diagnostics=diagnostics_record,
    )


def timestamp_quality_value(event: RawSecurityEvent) -> str:
    value = event.timestamp_quality

    if hasattr(value, "value"):
        return str(value.value)

    return str(value)


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


def ingest_source(
    payload: dict,
    validation_errors: list[str],
    connector,
    source_system: str,
    snapshot_prefix: str,
    work_item_id: str,
):
    if validation_errors:
        return {
            "status": "failed",
            "source_system": source_system,
            "events_normalized": 0,
            "errors": validation_errors,
        }

    events = connector.normalize_events(payload.get("events", []))
    adapter_result = MetricAdapter().build_snapshot(events)
    confidence_result = EvidenceConfidenceAdapter().build_confidence(events)

    snapshot_id = f"{snapshot_prefix}-{uuid4()}"

    snapshot = AdaptiveStateSnapshot(
        snapshot_id=snapshot_id,
        tenant_id="demo",
        work_item_id=work_item_id,
        status="VALID",
        adaptive_state=adapter_result.adaptive_state,
        evidence_confidence=confidence_result["evidence_confidence"],
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

    save_snapshot_diagnostics(
        snapshot_id=snapshot.snapshot_id,
        confidence_result=confidence_result,
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
        "source_system": source_system,
        "events_normalized": len(events),
        "snapshot_id": snapshot.snapshot_id,
        "snapshot_status": snapshot.status,
        "decision_id": decision_id,
        "selected_strategy": decision.selected_strategy,
        "kernel_decision": decision.kernel_decision,
        "reason": decision.reason,
        "evidence_confidence_score": confidence_result["confidence_score"],
        "evidence_confidence_band": confidence_result["confidence_band"],
        "evidence_confidence_factors": confidence_result[
            "evidence_confidence"
        ].factors,
    }


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/version")
def version():
    return {
        "version": "0.5.0",
        "release": "evidence-intelligence",
        "sprint": "3.4",
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
    confidence_result = EvidenceConfidenceAdapter().build_confidence(events)

    timestamp_quality_distribution = {
        "SOURCE_OCCURRED_AT": sum(
            1 for event in events if timestamp_quality_value(event) == "SOURCE_OCCURRED_AT"
        ),
        "BACKFILLED_FROM_CREATED_AT": sum(
            1 for event in events if timestamp_quality_value(event) == "BACKFILLED_FROM_CREATED_AT"
        ),
        "MISSING_TIMESTAMP": sum(
            1 for event in events if timestamp_quality_value(event) == "MISSING_TIMESTAMP"
        ),
    }

    status = (
        "INVALID"
        if timestamp_quality_distribution["MISSING_TIMESTAMP"] > 0
        else "VALID"
    )

    snapshot_id = str(uuid4())

    snapshot = AdaptiveStateSnapshot(
        snapshot_id=snapshot_id,
        tenant_id="demo",
        work_item_id="demo",
        status=status,
        adaptive_state=adapter_result.adaptive_state,
        evidence_confidence=confidence_result["evidence_confidence"],
        evidence=adapter_result.evidence,
        timestamp_quality_distribution=timestamp_quality_distribution,
    )

    SnapshotLedger().save_snapshot(
        snapshot,
        normalization_applied=adapter_result.normalization_applied,
    )

    save_snapshot_diagnostics(
        snapshot_id=snapshot.snapshot_id,
        confidence_result=confidence_result,
    )

    return snapshot


@app.post("/evidence/quality")
def score_evidence_quality(events: List[RawSecurityEvent]):
    return EvidenceQualityService().score_events(events)


@app.post("/evidence/agreement")
def evaluate_evidence_agreement(events: List[RawSecurityEvent]):
    return CrossSourceAgreementService().evaluate_agreement(events)


@app.post("/evidence/conflicts")
def detect_evidence_conflicts(events: List[RawSecurityEvent]):
    return EvidenceConflictService().detect_conflicts(events)


@app.post("/evidence/diagnostics")
def diagnose_evidence(events: List[RawSecurityEvent]):
    return EvidenceDiagnosticsService().diagnose_events(events)


@app.post("/evidence/confidence")
def build_evidence_confidence(events: List[RawSecurityEvent]):
    return EvidenceConfidenceAdapter().build_confidence(events)


@app.post("/governance/signals")
def classify_governance_signals(events: List[RawSecurityEvent]):
    return GovernanceSignalService().classify_events(events)


@app.post("/governance/signals/summary")
def summarize_governance_signals(events: List[RawSecurityEvent]):
    return GovernanceSignalSummaryService().summarize_events(events)


@app.post("/governance/signals/correlations")
def correlate_governance_signals(events: List[RawSecurityEvent]):
    return SignalCorrelationService().correlate_events(events)


@app.post("/governance/friction/signals")
def detect_friction_signals(events: List[RawSecurityEvent]):
    return FrictionSignalDetectionService().detect_events(events)


@app.post("/governance/debt/indicators")
def assess_governance_debt_indicators(events: List[RawSecurityEvent]):
    return GovernanceDebtIndicatorService().assess_events(events)


@app.get("/snapshots")
def list_snapshots():
    return SnapshotLedger().list_snapshots()


@app.get("/snapshot-diagnostics")
def list_snapshot_diagnostics():
    return {
        "status": "ok",
        "diagnostics": SnapshotDiagnosticsLedger().list_diagnostics(),
    }


@app.get("/snapshot-diagnostics/summary")
def snapshot_diagnostics_summary():
    return SnapshotDiagnosticsSummaryService().get_summary()


@app.get("/snapshot-diagnostics/risk")
def snapshot_diagnostics_risk():
    return SnapshotDiagnosticsRiskService().get_risk_summary()


@app.get("/snapshot-diagnostics/{snapshot_id}")
def get_snapshot_diagnostics(snapshot_id: str):
    diagnostics = SnapshotDiagnosticsLedger().get_diagnostics(snapshot_id)

    if diagnostics is None:
        return {
            "status": "failed",
            "error": "snapshot_diagnostics_not_found",
            "snapshot_id": snapshot_id,
        }

    return {
        "status": "ok",
        "snapshot_id": snapshot_id,
        "diagnostics": diagnostics,
    }


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


@app.get("/sources/categories")
def source_categories():
    return SourceCategoryService().get_category_summary()


@app.get("/sources/categories/{category}")
def source_category_detail(category: str):
    return SourceCategoryService().get_category_detail(category)


@app.get("/sources/coverage/gaps")
def source_coverage_gaps():
    return SourceCoverageService().get_coverage_gaps()


@app.get("/sources/coverage")
def source_coverage():
    return SourceCoverageService().get_coverage_summary()


@app.get("/sources/health")
def source_health():
    return SourceHealthService().get_health_summary()


@app.get("/sources/kernel-roles")
def source_kernel_roles():
    return SourceKernelRoleService().get_kernel_role_summary()


@app.get("/sources/kernel-roles/{kernel_role}")
def source_kernel_role_detail(kernel_role: str):
    return SourceKernelRoleService().get_kernel_role_detail(kernel_role)


@app.get("/sources/trust-tiers")
def source_trust_tiers():
    return SourceTrustTierService().get_trust_tier_summary()


@app.get("/sources/trust-tiers/{trust_tier}")
def source_trust_tier_detail(trust_tier: str):
    return SourceTrustTierService().get_trust_tier_detail(trust_tier)


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
    return ingest_source(
        payload=payload,
        validation_errors=validate_github_payload(payload),
        connector=GitHubConnector(),
        source_system="github",
        snapshot_prefix="github",
        work_item_id="github-ingestion",
    )


@app.post("/ingest/servicenow")
def ingest_servicenow(payload: dict):
    return ingest_source(
        payload=payload,
        validation_errors=validate_servicenow_payload(payload),
        connector=ServiceNowConnector(),
        source_system="servicenow",
        snapshot_prefix="servicenow",
        work_item_id="servicenow-ingestion",
    )


@app.post("/ingest/jira")
def ingest_jira(payload: dict):
    return ingest_source(
        payload=payload,
        validation_errors=validate_jira_payload(payload),
        connector=JiraConnector(),
        source_system="jira",
        snapshot_prefix="jira",
        work_item_id="jira-ingestion",
    )


@app.post("/ingest/okta")
def ingest_okta(payload: dict):
    return ingest_source(
        payload=payload,
        validation_errors=validate_okta_payload(payload),
        connector=OktaConnector(),
        source_system="okta",
        snapshot_prefix="okta",
        work_item_id="okta-ingestion",
    )


@app.post("/ingest/entra")
def ingest_entra(payload: dict):
    return ingest_source(
        payload=payload,
        validation_errors=validate_entra_payload(payload),
        connector=EntraConnector(),
        source_system="entra",
        snapshot_prefix="entra",
        work_item_id="entra-ingestion",
    )


@app.post("/ingest/sentinelone")
def ingest_sentinelone(payload: dict):
    return ingest_source(
        payload=payload,
        validation_errors=validate_sentinelone_payload(payload),
        connector=SentinelOneConnector(),
        source_system="sentinelone",
        snapshot_prefix="sentinelone",
        work_item_id="sentinelone-ingestion",
    )


@app.post("/ingest/defender")
def ingest_defender(payload: dict):
    return ingest_source(
        payload=payload,
        validation_errors=validate_defender_payload(payload),
        connector=DefenderConnector(),
        source_system="defender",
        snapshot_prefix="defender",
        work_item_id="defender-ingestion",
    )