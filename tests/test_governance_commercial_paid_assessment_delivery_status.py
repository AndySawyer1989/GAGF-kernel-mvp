from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

import backend.app.gagf.governance_commercial_paid_assessment_delivery_status as delivery_status_module
from backend.app.gagf.governance_commercial_paid_assessment_delivery_status import (
    CommercialPaidAssessmentDeliveryStatusError,
    GovernanceCommercialPaidAssessmentDeliveryStatusService,
)
from backend.app.gagf.governance_commercial_paid_assessment_execution import (
    GovernanceCommercialPaidAssessmentExecutionService,
)
from backend.app.gagf.governance_paid_assessment_lifecycle_persistence import (
    DELIVERY_ARTIFACT_TYPE,
)


TENANT_ID = "tenant-001"
CLIENT_ID = "client-001"
ENGAGEMENT_ID = "engagement-001"
ASSESSMENT_ID = "assessment-001"


class StubExecutionService(
    GovernanceCommercialPaidAssessmentExecutionService
):
    def __init__(
        self,
        database_path: Path,
    ) -> None:
        self._test_database_path = database_path

    def database_path_for_hierarchy(
        self,
        *,
        tenant_id: str,
        client_id: str,
        engagement_id: str,
        assessment_id: str,
    ) -> Path:
        assert tenant_id == TENANT_ID
        assert client_id == CLIENT_ID
        assert engagement_id == ENGAGEMENT_ID
        assert assessment_id == ASSESSMENT_ID

        return self._test_database_path


def delivery_payload(
    **overrides: object,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "tenant_id": TENANT_ID,
        "client_id": CLIENT_ID,
        "engagement_id": ENGAGEMENT_ID,
        "assessment_id": ASSESSMENT_ID,
        "delivery_status": "delivered",
        "delivery_completed": True,
        "report_id": "report-001",
        "delivered_by": "operator-001",
        "delivered_at": "2026-09-03T12:00:00Z",
        "delivery_method": "email",
        "delivery_reference": "message-001",
    }

    payload.update(overrides)

    return payload


class StubRepository:
    artifacts: tuple[SimpleNamespace, ...] = ()
    chain_valid = True
    assessment_error: Exception | None = None

    def __init__(
        self,
        database_path: Path,
    ) -> None:
        self.database_path = database_path

    def get_assessment(
        self,
        *,
        context: object,
    ) -> object:
        if self.assessment_error is not None:
            raise self.assessment_error

        return SimpleNamespace()

    def verify_chain(
        self,
        *,
        context: object,
    ) -> bool:
        return self.chain_valid

    def list_artifacts(
        self,
        *,
        context: object,
        artifact_type: str | None = None,
    ) -> tuple[SimpleNamespace, ...]:
        assert artifact_type == DELIVERY_ARTIFACT_TYPE
        return self.artifacts


def build_service(
    database_path: Path,
) -> GovernanceCommercialPaidAssessmentDeliveryStatusService:
    return GovernanceCommercialPaidAssessmentDeliveryStatusService(
        execution_service=StubExecutionService(
            database_path
        )
    )


def get_status(
    service: GovernanceCommercialPaidAssessmentDeliveryStatusService,
):
    return service.get_status(
        tenant_id=TENANT_ID,
        client_id=CLIENT_ID,
        engagement_id=ENGAGEMENT_ID,
        assessment_id=ASSESSMENT_ID,
    )


def test_returns_not_found_when_governed_database_does_not_exist(
    tmp_path: Path,
) -> None:
    database_path = (
        tmp_path /
        "missing-governed-assessment.sqlite3"
    )

    service = build_service(
        database_path
    )

    result = get_status(service)

    assert result.found is False
    assert result.delivery_recorded is False
    assert result.delivery_status is None
    assert result.report_id is None
    assert result.repository_chain_valid is False

    payload = result.to_dict()

    assert (
        payload["boundaries"][
            "delivery_status_is_read_only_projection"
        ]
        is True
    )
    assert (
        payload["boundaries"][
            "delivery_is_not_client_receipt"
        ]
        is True
    )


def test_returns_not_found_when_no_delivery_artifact_exists(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database_path = (
        tmp_path /
        "assessment.sqlite3"
    )
    database_path.touch()

    StubRepository.artifacts = ()
    StubRepository.chain_valid = True
    StubRepository.assessment_error = None

    monkeypatch.setattr(
        delivery_status_module,
        "GovernanceAssessmentRepository",
        StubRepository,
    )

    service = build_service(
        database_path
    )

    result = get_status(service)

    assert result.found is False
    assert result.delivery_recorded is False
    assert result.repository_chain_valid is True


def test_projects_persisted_delivery_as_restart_safe_status(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database_path = (
        tmp_path /
        "assessment.sqlite3"
    )
    database_path.touch()

    StubRepository.artifacts = (
        SimpleNamespace(
            artifact_type=DELIVERY_ARTIFACT_TYPE,
            payload=delivery_payload(),
        ),
    )
    StubRepository.chain_valid = True
    StubRepository.assessment_error = None

    monkeypatch.setattr(
        delivery_status_module,
        "GovernanceAssessmentRepository",
        StubRepository,
    )

    service = build_service(
        database_path
    )

    result = get_status(service)

    assert result.found is True
    assert result.delivery_recorded is True
    assert result.delivery_status == "delivered"
    assert result.report_id == "report-001"
    assert result.delivered_by == "operator-001"
    assert (
        result.delivered_at
        == "2026-09-03T12:00:00Z"
    )
    assert result.delivery_method == "email"
    assert result.delivery_reference == "message-001"
    assert result.repository_chain_valid is True

    payload = result.to_dict()

    assert "database_path" not in payload
    assert "operator_result" not in payload
    assert "approved_delivery_payload" not in payload
    assert (
        payload["boundaries"][
            "delivery_is_not_client_acknowledgment"
        ]
        is True
    )
    assert (
        payload["boundaries"][
            "delivery_is_not_client_response"
        ]
        is True
    )
    assert (
        payload["boundaries"][
            "delivery_is_not_closeout"
        ]
        is True
    )


def test_rejects_invalid_repository_chain(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database_path = (
        tmp_path /
        "assessment.sqlite3"
    )
    database_path.touch()

    StubRepository.artifacts = ()
    StubRepository.chain_valid = False
    StubRepository.assessment_error = None

    monkeypatch.setattr(
        delivery_status_module,
        "GovernanceAssessmentRepository",
        StubRepository,
    )

    service = build_service(
        database_path
    )

    with pytest.raises(
        CommercialPaidAssessmentDeliveryStatusError,
        match="repository chain is invalid",
    ):
        get_status(service)


def test_rejects_duplicate_delivery_artifacts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database_path = (
        tmp_path /
        "assessment.sqlite3"
    )
    database_path.touch()

    artifact = SimpleNamespace(
        artifact_type=DELIVERY_ARTIFACT_TYPE,
        payload=delivery_payload(),
    )

    StubRepository.artifacts = (
        artifact,
        artifact,
    )
    StubRepository.chain_valid = True
    StubRepository.assessment_error = None

    monkeypatch.setattr(
        delivery_status_module,
        "GovernanceAssessmentRepository",
        StubRepository,
    )

    service = build_service(
        database_path
    )

    with pytest.raises(
        CommercialPaidAssessmentDeliveryStatusError,
        match="exactly one persisted delivery artifact",
    ):
        get_status(service)


def test_rejects_delivery_hierarchy_mismatch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database_path = (
        tmp_path /
        "assessment.sqlite3"
    )
    database_path.touch()

    StubRepository.artifacts = (
        SimpleNamespace(
            artifact_type=DELIVERY_ARTIFACT_TYPE,
            payload=delivery_payload(
                assessment_id="other-assessment"
            ),
        ),
    )
    StubRepository.chain_valid = True
    StubRepository.assessment_error = None

    monkeypatch.setattr(
        delivery_status_module,
        "GovernanceAssessmentRepository",
        StubRepository,
    )

    service = build_service(
        database_path
    )

    with pytest.raises(
        CommercialPaidAssessmentDeliveryStatusError,
        match="persisted delivery hierarchy mismatch",
    ):
        get_status(service)


def test_rejects_incomplete_delivery_artifact(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database_path = (
        tmp_path /
        "assessment.sqlite3"
    )
    database_path.touch()

    StubRepository.artifacts = (
        SimpleNamespace(
            artifact_type=DELIVERY_ARTIFACT_TYPE,
            payload=delivery_payload(
                delivery_completed=False
            ),
        ),
    )
    StubRepository.chain_valid = True
    StubRepository.assessment_error = None

    monkeypatch.setattr(
        delivery_status_module,
        "GovernanceAssessmentRepository",
        StubRepository,
    )

    service = build_service(
        database_path
    )

    with pytest.raises(
        CommercialPaidAssessmentDeliveryStatusError,
        match="delivery_completed=true",
    ):
        get_status(service)


def test_rejects_blank_hierarchy_values(
    tmp_path: Path,
) -> None:
    service = build_service(
        tmp_path /
        "assessment.sqlite3"
    )

    with pytest.raises(
        CommercialPaidAssessmentDeliveryStatusError,
        match="tenant_id must be non-empty",
    ):
        service.get_status(
            tenant_id=" ",
            client_id=CLIENT_ID,
            engagement_id=ENGAGEMENT_ID,
            assessment_id=ASSESSMENT_ID,
        )