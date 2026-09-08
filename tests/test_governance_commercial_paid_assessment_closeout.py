from __future__ import annotations

import json
from pathlib import Path

import pytest

from backend.app.gagf.governance_commercial_paid_assessment_client_response import (
    GovernanceCommercialPaidAssessmentClientResponseService,
)
from backend.app.gagf.governance_commercial_paid_assessment_closeout import (
    CommercialPaidAssessmentCloseoutError,
    GovernanceCommercialPaidAssessmentCloseoutService,
)
from backend.app.gagf.governance_paid_assessment_closeout import (
    PAID_ASSESSMENT_CLOSEOUT_ARTIFACT_TYPE,
)
from backend.app.gagf.governance_paid_assessment_lifecycle_persistence import (
    CLIENT_RESPONSE_ARTIFACT_TYPE,
)
from tests.test_governance_commercial_paid_assessment_client_response import (
    HIERARCHY,
    build_context,
    build_execution_service,
    build_repository,
    build_response_payload,
    persist_delivery,
    prepare_delivered_and_acknowledged,
    record_receipt,
)


def build_closeout_payload(
    **overrides,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "closed_by": "FIP Assessment Operator",
        "closeout_reason": (
            "Client response is recorded and "
            "administrative assessment processing "
            "is complete."
        ),
        "administrative_closeout_confirmed": True,
    }

    payload.update(overrides)

    return payload


def prepare_client_response(
    tmp_path: Path,
):
    execution_service, repository = (
        prepare_delivered_and_acknowledged(
            tmp_path
        )
    )

    response_result = (
        GovernanceCommercialPaidAssessmentClientResponseService(
            execution_service=execution_service
        ).record(
            **HIERARCHY,
            response_payload=build_response_payload(),
        )
    )

    assert (
        response_result.response_status
        == "client_response_recorded"
    )

    return (
        execution_service,
        repository,
        response_result,
    )


def build_service(
    execution_service,
) -> GovernanceCommercialPaidAssessmentCloseoutService:
    return GovernanceCommercialPaidAssessmentCloseoutService(
        execution_service=execution_service
    )


def test_records_explicit_governed_administrative_closeout(
    tmp_path: Path,
) -> None:
    (
        execution_service,
        repository,
        response_result,
    ) = prepare_client_response(
        tmp_path
    )

    responses = repository.list_artifacts(
        context=build_context(),
        artifact_type=CLIENT_RESPONSE_ARTIFACT_TYPE,
    )

    before = repository.list_artifacts(
        context=build_context(),
        artifact_type=(
            PAID_ASSESSMENT_CLOSEOUT_ARTIFACT_TYPE
        ),
    )

    assert len(responses) == 1
    assert len(before) == 0

    result = build_service(
        execution_service
    ).record(
        **HIERARCHY,
        closeout_payload=build_closeout_payload(),
    )

    assert result.closeout_status == (
        "assessment_closed"
    )

    assert result.report_id == "report-001"

    assert result.closed_by == (
        "FIP Assessment Operator"
    )

    assert result.closeout_reason == (
        "Client response is recorded and "
        "administrative assessment processing "
        "is complete."
    )

    assert response_result.report_id == (
        result.report_id
    )

    after = repository.list_artifacts(
        context=build_context(),
        artifact_type=(
            PAID_ASSESSMENT_CLOSEOUT_ARTIFACT_TYPE
        ),
    )

    assert len(after) == 1

    assert result.closeout_artifact_id == (
        after[0].artifact_id
    )

    assert result.closeout_artifact_hash == (
        after[0].artifact_hash
    )

    assert (
        after[0].payload["closeout_status"]
        == "assessment_closed"
    )

    assert (
        after[0].payload[
            "client_response_artifact_id"
        ]
        == responses[0].artifact_id
    )

    assert (
        after[0].payload[
            "client_response_artifact_hash"
        ]
        == responses[0].artifact_hash
    )

    assert repository.verify_chain(
        context=build_context()
    ) is True

    assert result.repository_chain_valid is True


def test_exact_closeout_retry_is_idempotent(
    tmp_path: Path,
) -> None:
    execution_service, repository, _ = (
        prepare_client_response(
            tmp_path
        )
    )

    service = build_service(
        execution_service
    )

    payload = build_closeout_payload()

    first = service.record(
        **HIERARCHY,
        closeout_payload=payload,
    )

    first_artifacts = repository.list_artifacts(
        context=build_context(),
        artifact_type=(
            PAID_ASSESSMENT_CLOSEOUT_ARTIFACT_TYPE
        ),
    )

    assert len(first_artifacts) == 1

    second = service.record(
        **HIERARCHY,
        closeout_payload=payload,
    )

    second_artifacts = repository.list_artifacts(
        context=build_context(),
        artifact_type=(
            PAID_ASSESSMENT_CLOSEOUT_ARTIFACT_TYPE
        ),
    )

    assert len(second_artifacts) == 1

    assert (
        second.closeout_artifact_id
        == first.closeout_artifact_id
    )

    assert (
        second.closeout_artifact_hash
        == first.closeout_artifact_hash
    )

    assert repository.verify_chain(
        context=build_context()
    ) is True


def test_rejects_closeout_before_client_response(
    tmp_path: Path,
) -> None:
    execution_service, repository = (
        prepare_delivered_and_acknowledged(
            tmp_path
        )
    )

    responses = repository.list_artifacts(
        context=build_context(),
        artifact_type=CLIENT_RESPONSE_ARTIFACT_TYPE,
    )

    assert responses == ()

    with pytest.raises(
        CommercialPaidAssessmentCloseoutError,
        match=(
            "governed closeout requires exactly one "
            "persisted client-response artifact"
        ),
    ):
        build_service(
            execution_service
        ).record(
            **HIERARCHY,
            closeout_payload=(
                build_closeout_payload()
            ),
        )


def test_rejects_closeout_before_receipt_and_response(
    tmp_path: Path,
) -> None:
    execution_service = build_execution_service(
        tmp_path
    )

    repository = build_repository(
        execution_service
    )

    persist_delivery(
        repository
    )

    with pytest.raises(
        CommercialPaidAssessmentCloseoutError,
        match=(
            "governed closeout requires exactly one "
            "persisted client-response artifact"
        ),
    ):
        build_service(
            execution_service
        ).record(
            **HIERARCHY,
            closeout_payload=(
                build_closeout_payload()
            ),
        )


def test_requires_explicit_administrative_confirmation(
    tmp_path: Path,
) -> None:
    execution_service, repository, _ = (
        prepare_client_response(
            tmp_path
        )
    )

    with pytest.raises(
        CommercialPaidAssessmentCloseoutError,
        match=(
            "administrative_closeout_confirmed "
            "must be true"
        ),
    ):
        build_service(
            execution_service
        ).record(
            **HIERARCHY,
            closeout_payload=(
                build_closeout_payload(
                    administrative_closeout_confirmed=False
                )
            ),
        )

    closeouts = repository.list_artifacts(
        context=build_context(),
        artifact_type=(
            PAID_ASSESSMENT_CLOSEOUT_ARTIFACT_TYPE
        ),
    )

    assert closeouts == ()


def test_browser_lineage_and_repository_fields_are_ignored(
    tmp_path: Path,
) -> None:
    execution_service, repository, _ = (
        prepare_client_response(
            tmp_path
        )
    )

    response = repository.list_artifacts(
        context=build_context(),
        artifact_type=CLIENT_RESPONSE_ARTIFACT_TYPE,
    )[0]

    result = build_service(
        execution_service
    ).record(
        **HIERARCHY,
        closeout_payload=(
            build_closeout_payload(
                tenant_id="forged-tenant",
                client_id="forged-client",
                engagement_id="forged-engagement",
                assessment_id="forged-assessment",
                report_id="forged-report",
                response_id="forged-response",
                response_hash="f" * 64,
                client_response_artifact_id=(
                    "forged-response-artifact"
                ),
                client_response_artifact_hash=(
                    "e" * 64
                ),
                database_path=(
                    "C:/forged/assessment.sqlite3"
                ),
                repository_path=(
                    "C:/forged/repository.sqlite3"
                ),
                closeout_status="forged-status",
                closeout_basis="forged-basis",
            )
        ),
    )

    assert result.tenant_id == (
        HIERARCHY["tenant_id"]
    )

    assert result.client_id == (
        HIERARCHY["client_id"]
    )

    assert result.engagement_id == (
        HIERARCHY["engagement_id"]
    )

    assert result.assessment_id == (
        HIERARCHY["assessment_id"]
    )

    assert result.report_id == "report-001"

    closeouts = repository.list_artifacts(
        context=build_context(),
        artifact_type=(
            PAID_ASSESSMENT_CLOSEOUT_ARTIFACT_TYPE
        ),
    )

    assert len(closeouts) == 1

    closeout = closeouts[0]

    assert closeout.payload["report_id"] == (
        "report-001"
    )

    assert (
        closeout.payload[
            "client_response_artifact_id"
        ]
        == response.artifact_id
    )

    assert (
        closeout.payload[
            "client_response_artifact_hash"
        ]
        == response.artifact_hash
    )

    serialized = json.dumps(
        closeout.payload
    )

    assert "forged-report" not in serialized
    assert "forged-response" not in serialized
    assert "C:/forged" not in serialized


def test_closeout_result_preserves_authority_boundaries(
    tmp_path: Path,
) -> None:
    execution_service, _, _ = (
        prepare_client_response(
            tmp_path
        )
    )

    payload = build_service(
        execution_service
    ).record(
        **HIERARCHY,
        closeout_payload=(
            build_closeout_payload()
        ),
    ).to_dict()

    assert (
        payload[
            "administrative_closeout_recorded"
        ]
        is True
    )

    boundaries = payload["boundaries"]

    assert (
        boundaries[
            "closeout_requires_explicit_human_confirmation"
        ]
        is True
    )

    assert (
        boundaries[
            "response_is_not_closeout"
        ]
        is True
    )

    assert (
        boundaries[
            "pa010_remains_closeout_authority"
        ]
        is True
    )

    assert (
        boundaries[
            "pa013_remains_operator_coordination_authority"
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
            "closeout_is_not_roi_verification"
        ]
        is True
    )

    assert (
        boundaries[
            "closeout_is_not_customer_outcome"
        ]
        is True
    )

    forbidden = (
        "findings_validated",
        "recommendation_implemented",
        "implementation_authorized",
        "intervention_requested",
        "intervention_authorized",
        "intervention_executed",
        "causal_success",
        "roi_verified",
        "remediation_success",
        "customer_outcome_verified",
    )

    for field_name in forbidden:
        assert field_name not in payload


def test_repository_chain_remains_valid_after_closeout(
    tmp_path: Path,
) -> None:
    execution_service, repository, _ = (
        prepare_client_response(
            tmp_path
        )
    )

    assert repository.verify_chain(
        context=build_context()
    ) is True

    result = build_service(
        execution_service
    ).record(
        **HIERARCHY,
        closeout_payload=(
            build_closeout_payload()
        ),
    )

    assert result.repository_chain_valid is True

    assert repository.verify_chain(
        context=build_context()
    ) is True


def test_missing_governed_repository_fails_closed(
    tmp_path: Path,
) -> None:
    execution_service = build_execution_service(
        tmp_path
    )

    with pytest.raises(
        CommercialPaidAssessmentCloseoutError,
        match=(
            "governed paid-assessment repository "
            "was not found"
        ),
    ):
        build_service(
            execution_service
        ).record(
            **HIERARCHY,
            closeout_payload=(
                build_closeout_payload()
            ),
        )
