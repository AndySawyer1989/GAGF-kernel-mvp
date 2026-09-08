from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

import backend.app.gagf.governance_commercial_paid_assessment_closeout_status as closeout_status_module
from backend.app.gagf.governance_commercial_paid_assessment_closeout_status import (
    CommercialPaidAssessmentCloseoutStatusError,
    GovernanceCommercialPaidAssessmentCloseoutStatusService,
)
from backend.app.gagf.governance_commercial_paid_assessment_execution import (
    GovernanceCommercialPaidAssessmentExecutionService,
)
from backend.app.gagf.governance_paid_assessment_closeout import (
    PAID_ASSESSMENT_CLOSEOUT_ARTIFACT_TYPE,
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


def closeout_payload(
    **overrides: object,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "tenant_id": TENANT_ID,
        "client_id": CLIENT_ID,
        "engagement_id": ENGAGEMENT_ID,
        "assessment_id": ASSESSMENT_ID,
        "report_id": "report-001",
        "closed_by": "operator-001",
        "closed_at": "2026-09-08T14:00:00+00:00",
        "closeout_reason": (
            "Client response recorded and "
            "administrative processing complete."
        ),
        "administrative_closeout_confirmed": True,
        "closeout_status": "assessment_closed",
        "client_response_artifact_id": (
            "response-artifact-001"
        ),
        "client_response_artifact_hash": "a" * 64,
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
        assert (
            artifact_type
            == PAID_ASSESSMENT_CLOSEOUT_ARTIFACT_TYPE
        )

        return self.artifacts


def build_service(
    database_path: Path,
) -> GovernanceCommercialPaidAssessmentCloseoutStatusService:
    return GovernanceCommercialPaidAssessmentCloseoutStatusService(
        execution_service=StubExecutionService(
            database_path
        )
    )


def get_status(
    service: GovernanceCommercialPaidAssessmentCloseoutStatusService,
):
    return service.get_status(
        tenant_id=TENANT_ID,
        client_id=CLIENT_ID,
        engagement_id=ENGAGEMENT_ID,
        assessment_id=ASSESSMENT_ID,
    )


def test_returns_not_found_when_governed_database_missing(
    tmp_path: Path,
) -> None:
    service = build_service(
        tmp_path / "missing.sqlite3"
    )

    result = get_status(
        service
    )

    assert result.found is False
    assert result.closeout_recorded is False
    assert result.closeout_status is None
    assert result.report_id is None
    assert result.repository_chain_valid is False


def test_returns_not_found_when_closeout_not_recorded(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database_path = (
        tmp_path / "assessment.sqlite3"
    )

    database_path.touch()

    StubRepository.artifacts = ()
    StubRepository.chain_valid = True
    StubRepository.assessment_error = None

    monkeypatch.setattr(
        closeout_status_module,
        "GovernanceAssessmentRepository",
        StubRepository,
    )

    result = get_status(
        build_service(
            database_path
        )
    )

    assert result.found is False
    assert result.closeout_recorded is False
    assert result.repository_chain_valid is True


def test_projects_persisted_closeout_as_restart_safe_status(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database_path = (
        tmp_path / "assessment.sqlite3"
    )

    database_path.touch()

    StubRepository.artifacts = (
        SimpleNamespace(
            artifact_type=(
                PAID_ASSESSMENT_CLOSEOUT_ARTIFACT_TYPE
            ),
            payload=closeout_payload(),
        ),
    )

    StubRepository.chain_valid = True
    StubRepository.assessment_error = None

    monkeypatch.setattr(
        closeout_status_module,
        "GovernanceAssessmentRepository",
        StubRepository,
    )

    result = get_status(
        build_service(
            database_path
        )
    )

    assert result.found is True
    assert result.closeout_recorded is True
    assert (
        result.closeout_status
        == "assessment_closed"
    )
    assert result.report_id == "report-001"
    assert result.closed_by == "operator-001"
    assert (
        result.closed_at
        == "2026-09-08T14:00:00+00:00"
    )
    assert result.closeout_reason == (
        "Client response recorded and "
        "administrative processing complete."
    )
    assert result.repository_chain_valid is True

    payload = result.to_dict()

    assert "database_path" not in payload
    assert "repository_path" not in payload
    assert (
        "client_response_artifact_id"
        not in payload
    )
    assert (
        "client_response_artifact_hash"
        not in payload
    )
    assert "operator_result" not in payload

    boundaries = payload["boundaries"]

    assert (
        boundaries[
            "closeout_status_is_read_only_projection"
        ]
        is True
    )
    assert (
        boundaries[
            "client_response_is_not_closeout"
        ]
        is True
    )
    assert (
        boundaries[
            "closeout_is_not_intervention_authorization"
        ]
        is True
    )
    assert (
        boundaries[
            "pa010_remains_closeout_authority"
        ]
        is True
    )


def test_rejects_invalid_repository_chain(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database_path = (
        tmp_path / "assessment.sqlite3"
    )

    database_path.touch()

    StubRepository.artifacts = ()
    StubRepository.chain_valid = False
    StubRepository.assessment_error = None

    monkeypatch.setattr(
        closeout_status_module,
        "GovernanceAssessmentRepository",
        StubRepository,
    )

    with pytest.raises(
        CommercialPaidAssessmentCloseoutStatusError,
        match="repository chain is invalid",
    ):
        get_status(
            build_service(
                database_path
            )
        )


def test_rejects_duplicate_closeout_artifacts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database_path = (
        tmp_path / "assessment.sqlite3"
    )

    database_path.touch()

    artifact = SimpleNamespace(
        artifact_type=(
            PAID_ASSESSMENT_CLOSEOUT_ARTIFACT_TYPE
        ),
        payload=closeout_payload(),
    )

    StubRepository.artifacts = (
        artifact,
        artifact,
    )

    StubRepository.chain_valid = True
    StubRepository.assessment_error = None

    monkeypatch.setattr(
        closeout_status_module,
        "GovernanceAssessmentRepository",
        StubRepository,
    )

    with pytest.raises(
        CommercialPaidAssessmentCloseoutStatusError,
        match=(
            "exactly one persisted closeout artifact"
        ),
    ):
        get_status(
            build_service(
                database_path
            )
        )


def test_rejects_closeout_hierarchy_mismatch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database_path = (
        tmp_path / "assessment.sqlite3"
    )

    database_path.touch()

    StubRepository.artifacts = (
        SimpleNamespace(
            artifact_type=(
                PAID_ASSESSMENT_CLOSEOUT_ARTIFACT_TYPE
            ),
            payload=closeout_payload(
                assessment_id="wrong-assessment"
            ),
        ),
    )

    StubRepository.chain_valid = True
    StubRepository.assessment_error = None

    monkeypatch.setattr(
        closeout_status_module,
        "GovernanceAssessmentRepository",
        StubRepository,
    )

    with pytest.raises(
        CommercialPaidAssessmentCloseoutStatusError,
        match=(
            "persisted closeout hierarchy mismatch"
        ),
    ):
        get_status(
            build_service(
                database_path
            )
        )


def test_rejects_invalid_closeout_status(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database_path = (
        tmp_path / "assessment.sqlite3"
    )

    database_path.touch()

    StubRepository.artifacts = (
        SimpleNamespace(
            artifact_type=(
                PAID_ASSESSMENT_CLOSEOUT_ARTIFACT_TYPE
            ),
            payload=closeout_payload(
                closeout_status="not-closed"
            ),
        ),
    )

    StubRepository.chain_valid = True
    StubRepository.assessment_error = None

    monkeypatch.setattr(
        closeout_status_module,
        "GovernanceAssessmentRepository",
        StubRepository,
    )

    with pytest.raises(
        CommercialPaidAssessmentCloseoutStatusError,
        match=(
            "closeout_status=assessment_closed"
        ),
    ):
        get_status(
            build_service(
                database_path
            )
        )


def test_rejects_closeout_without_explicit_confirmation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database_path = (
        tmp_path / "assessment.sqlite3"
    )

    database_path.touch()

    StubRepository.artifacts = (
        SimpleNamespace(
            artifact_type=(
                PAID_ASSESSMENT_CLOSEOUT_ARTIFACT_TYPE
            ),
            payload=closeout_payload(
                administrative_closeout_confirmed=False
            ),
        ),
    )

    StubRepository.chain_valid = True
    StubRepository.assessment_error = None

    monkeypatch.setattr(
        closeout_status_module,
        "GovernanceAssessmentRepository",
        StubRepository,
    )

    with pytest.raises(
        CommercialPaidAssessmentCloseoutStatusError,
        match=(
            "administrative_closeout_confirmed=true"
        ),
    ):
        get_status(
            build_service(
                database_path
            )
        )


def test_rejects_blank_hierarchy_values(
    tmp_path: Path,
) -> None:
    service = build_service(
        tmp_path / "assessment.sqlite3"
    )

    with pytest.raises(
        CommercialPaidAssessmentCloseoutStatusError,
        match="tenant_id must be non-empty",
    ):
        service.get_status(
            tenant_id=" ",
            client_id=CLIENT_ID,
            engagement_id=ENGAGEMENT_ID,
            assessment_id=ASSESSMENT_ID,
        )
