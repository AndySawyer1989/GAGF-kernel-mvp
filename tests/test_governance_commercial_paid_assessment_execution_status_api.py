from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.app.gagf.governance_commercial_paid_assessment_api import (
    create_governance_commercial_paid_assessment_router,
)
from backend.app.gagf.governance_commercial_paid_assessment_execution_status import (
    GovernanceCommercialPaidAssessmentExecutionStatusStore,
)


@dataclass(frozen=True)
class FakeBinding:
    hierarchy_key: str
    binding_hash: str
    assessment_execution_request_hash: str


class FakeBindingService:
    def __init__(
        self,
        binding: FakeBinding,
    ) -> None:
        self.binding = binding

    def get(
        self,
        *,
        hierarchy_key: str,
    ) -> FakeBinding:
        assert (
            hierarchy_key
            == self.binding.hierarchy_key
        )

        return self.binding


class FakePaidExecutionService:
    def __init__(
        self,
        *,
        status_store: (
            GovernanceCommercialPaidAssessmentExecutionStatusStore
        ),
    ) -> None:
        self.status_store = status_store


HIERARCHY = (
    "tenant-001/"
    "client-001/"
    "engagement-001/"
    "assessment-001"
)

STATUS_PATH = (
    "/api/v1/governance-paid-assessments/"
    "tenant-001/"
    "client-001/"
    "engagement-001/"
    "assessment-001/"
    "execution-status"
)


def build_client(
    tmp_path: Path,
    *,
    binding_hash: str = "binding-hash-001",
    request_hash: str = "request-hash-001",
) -> tuple[
    TestClient,
    GovernanceCommercialPaidAssessmentExecutionStatusStore,
]:
    status_store = (
        GovernanceCommercialPaidAssessmentExecutionStatusStore(
            tmp_path
            / "paid-execution-status.sqlite3"
        )
    )

    service = FakePaidExecutionService(
        status_store=status_store
    )

    binding_service = FakeBindingService(
        FakeBinding(
            hierarchy_key=HIERARCHY,
            binding_hash=binding_hash,
            assessment_execution_request_hash=(
                request_hash
            ),
        )
    )

    app = FastAPI()

    router = (
        create_governance_commercial_paid_assessment_router(
            service=service,  # type: ignore[arg-type]
            execution_input_binding_service=(
                binding_service  # type: ignore[arg-type]
            ),
        )
    )

    app.include_router(
        router
    )

    return (
        TestClient(app),
        status_store,
    )


def record_status(
    store: GovernanceCommercialPaidAssessmentExecutionStatusStore,
    *,
    disposition: str = "executed",
    binding_hash: str = "binding-hash-001",
    request_hash: str = "request-hash-001",
    artifact_count_before: int = 0,
    artifact_count_after: int = 10,
) -> None:
    status = store.build_status(
        tenant_id="tenant-001",
        client_id="client-001",
        engagement_id="engagement-001",
        assessment_id="assessment-001",
        disposition=disposition,
        attempt_hash="attempt-hash-001",
        attempt_record_hash="attempt-record-hash-001",
        assessment_execution_request_hash=(
            request_hash
        ),
        execution_input_binding_hash=(
            binding_hash
        ),
        artifact_count_before=(
            artifact_count_before
        ),
        artifact_count_after=(
            artifact_count_after
        ),
        recorded_at=datetime(
            2026,
            9,
            2,
            2,
            30,
            tzinfo=timezone.utc,
        ),
    )

    store.record_status(
        status=status
    )


def test_missing_execution_status_is_safe_not_found(
    tmp_path: Path,
) -> None:
    client, _ = build_client(
        tmp_path
    )

    response = client.get(
        STATUS_PATH
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload == {
        "found": False,
        "hierarchy_key": HIERARCHY,
        "status": None,
        "boundaries": {
            "status_is_read_only": True,
            "status_is_not_execution_authority": True,
            "status_is_not_recovery_authority": True,
            "raw_execution_evidence_not_exposed": True,
            "browser_cannot_select_execution_repository": True,
        },
    }


def test_execution_status_returns_safe_governed_metadata(
    tmp_path: Path,
) -> None:
    client, store = build_client(
        tmp_path
    )

    record_status(
        store
    )

    response = client.get(
        STATUS_PATH
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["found"] is True
    assert payload["hierarchy_key"] == HIERARCHY

    status = payload["status"]

    assert status["disposition"] == "executed"
    assert status["artifact_count_before"] == 0
    assert status["artifact_count_after"] == 10

    assert (
        status["attempt_hash"]
        == "attempt-hash-001"
    )

    assert (
        status["attempt_record_hash"]
        == "attempt-record-hash-001"
    )

    assert (
        status[
            "assessment_execution_request_hash"
        ]
        == "request-hash-001"
    )

    assert (
        status[
            "execution_input_binding_hash"
        ]
        == "binding-hash-001"
    )

    assert (
        status["schema_version"]
        == "1.0.0"
    )

    assert "database_path" not in status
    assert "csv_text" not in status
    assert "evidence" not in status
    assert "assessment_execution_request" not in status

    assert payload["boundaries"] == {
        "status_is_read_only": True,
        "status_is_not_execution_authority": True,
        "status_is_not_recovery_authority": True,
        "raw_execution_evidence_not_exposed": True,
        "browser_cannot_select_execution_repository": True,
    }


def test_reconciled_status_is_restored(
    tmp_path: Path,
) -> None:
    client, store = build_client(
        tmp_path
    )

    record_status(
        store,
        disposition="reconciled",
        artifact_count_before=10,
        artifact_count_after=10,
    )

    response = client.get(
        STATUS_PATH
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["found"] is True

    assert (
        payload["status"]["disposition"]
        == "reconciled"
    )

    assert (
        payload["status"]["artifact_count_before"]
        == 10
    )

    assert (
        payload["status"]["artifact_count_after"]
        == 10
    )


def test_status_binding_hash_mismatch_fails_closed(
    tmp_path: Path,
) -> None:
    client, store = build_client(
        tmp_path,
        binding_hash="binding-hash-current",
    )

    record_status(
        store,
        binding_hash="binding-hash-stored",
    )

    response = client.get(
        STATUS_PATH
    )

    assert response.status_code == 409

    payload = response.json()

    assert (
        payload["detail"]["code"]
        == (
            "COMMERCIAL_PAID_ASSESSMENT_"
            "EXECUTION_STATUS_ERROR"
        )
    )

    assert (
        "binding hash"
        in payload["detail"]["message"]
    )


def test_status_request_hash_mismatch_fails_closed(
    tmp_path: Path,
) -> None:
    client, store = build_client(
        tmp_path,
        request_hash="request-hash-current",
    )

    record_status(
        store,
        request_hash="request-hash-stored",
    )

    response = client.get(
        STATUS_PATH
    )

    assert response.status_code == 409

    payload = response.json()

    assert (
        payload["detail"]["code"]
        == (
            "COMMERCIAL_PAID_ASSESSMENT_"
            "EXECUTION_STATUS_ERROR"
        )
    )

    assert (
        "request hash"
        in payload["detail"]["message"]
    )


def test_status_read_does_not_mutate_status_record(
    tmp_path: Path,
) -> None:
    client, store = build_client(
        tmp_path
    )

    record_status(
        store
    )

    before = store.get_status(
        tenant_id="tenant-001",
        client_id="client-001",
        engagement_id="engagement-001",
        assessment_id="assessment-001",
    )

    assert before is not None

    response = client.get(
        STATUS_PATH
    )

    assert response.status_code == 200

    after = store.get_status(
        tenant_id="tenant-001",
        client_id="client-001",
        engagement_id="engagement-001",
        assessment_id="assessment-001",
    )

    assert after is not None

    assert (
        after.to_dict()
        == before.to_dict()
    )
