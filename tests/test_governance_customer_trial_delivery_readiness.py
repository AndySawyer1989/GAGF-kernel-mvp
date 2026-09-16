from __future__ import annotations

from dataclasses import replace
from types import SimpleNamespace

import pytest

from backend.app.gagf.governance_commercial_paid_assessment_delivery_readiness import (
    CommercialPaidAssessmentDeliveryReadiness,
)
from backend.app.gagf.governance_customer_trial_delivery_readiness import (
    CONTROLLED_TRIAL_DELIVERY_READY,
    CustomerTrialDeliveryReadinessError,
    CustomerTrialDeliveryReadinessIdentityError,
    CustomerTrialDeliveryReadinessLineageError,
    CustomerTrialDeliveryReadinessStateError,
    GovernanceCustomerTrialDeliveryReadinessService,
)
from backend.app.gagf.governance_customer_trial_execution_observation_receipt_store import (
    CustomerTrialExecutionObservationReceipt,
)

from tests.test_governance_customer_trial_execution_observation_receipt_store import (
    build_observation,
)


BASE_OBSERVATION = build_observation()

HIERARCHY_KEY = (
    BASE_OBSERVATION.hierarchy_key
)

REPORT_ID = (
    BASE_OBSERVATION.report_id
)


class StubCommercialReadinessService:
    def __init__(
        self,
        *,
        report_id: str = REPORT_ID,
        hierarchy_key: str = HIERARCHY_KEY,
        repository_chain_valid: bool = True,
    ) -> None:
        (
            tenant_id,
            client_id,
            engagement_id,
            assessment_id,
        ) = hierarchy_key.split("/")

        execution_result = SimpleNamespace(
            report_id=report_id,
        )

        readiness = SimpleNamespace(
            delivery_readiness_status=(
                "ready_for_delivery_approval_review"
            ),
            recovery_disposition="executed",
            artifact_count=10,
            repository_chain_valid=(
                repository_chain_valid
            ),
            execution_result=(
                execution_result
            ),
        )

        self.result = CommercialPaidAssessmentDeliveryReadiness(
            tenant_id=tenant_id,
            client_id=client_id,
            engagement_id=engagement_id,
            assessment_id=assessment_id,
            execution_status_hash="1" * 64,
            operator_result_hash="2" * 64,
            operator_snapshot_hash="3" * 64,
            readiness=readiness,
        )

    def verify(
        self,
        *,
        tenant_id: str,
        client_id: str,
        engagement_id: str,
        assessment_id: str,
    ):
        return self.result


def build_receipt(
) -> CustomerTrialExecutionObservationReceipt:
    observation = build_observation()

    return CustomerTrialExecutionObservationReceipt(
        tenant_id=(
            observation.tenant_id
        ),
        client_id=(
            observation.client_id
        ),
        engagement_id=(
            observation.engagement_id
        ),
        assessment_id=(
            observation.assessment_id
        ),
        hierarchy_key=(
            observation.hierarchy_key
        ),
        observation_status=(
            observation.observation_status
        ),
        handoff_receipt_hash=(
            observation.handoff_receipt_hash
        ),
        handoff_lineage_hash=(
            observation.handoff_lineage_hash
        ),
        handoff_hash=(
            observation.handoff_hash
        ),
        assessment_execution_request_hash=(
            observation
            .assessment_execution_request_hash
        ),
        execution_result_hash=(
            observation.execution_result_hash
        ),
        application_hash=(
            observation.application_hash
        ),
        persistence_hash=(
            observation.persistence_hash
        ),
        report_id=(
            observation.report_id
        ),
        report_package_hash=(
            observation.report_package_hash
        ),
        observation_hash="4" * 64,
        receipt_hash="5" * 64,
    )


def build_service(
    *,
    readiness_service=None,
):
    service = (
        GovernanceCustomerTrialDeliveryReadinessService
        .__new__(
            GovernanceCustomerTrialDeliveryReadinessService
        )
    )

    service._commercial_readiness_service = (
        readiness_service
        if readiness_service is not None
        else StubCommercialReadinessService()
    )

    return service


def test_constructor_rejects_nonproduction_readiness_service():
    with pytest.raises(
        CustomerTrialDeliveryReadinessError,
        match="commercial_readiness_service",
    ):
        GovernanceCustomerTrialDeliveryReadinessService(
            commercial_readiness_service=object(),
        )


def test_verify_projects_existing_authoritative_readiness():
    receipt = build_receipt()
    service = build_service()

    result = service.verify(
        observation_receipt=receipt
    )

    assert (
        result.readiness_status
        == CONTROLLED_TRIAL_DELIVERY_READY
    )

    assert (
        result.hierarchy_key
        == receipt.hierarchy_key
    )

    assert (
        result.observation_receipt_hash
        == receipt.receipt_hash
    )

    assert (
        result.execution_result_hash
        == receipt.execution_result_hash
    )

    assert (
        result.report_id
        == receipt.report_id
    )

    assert (
        result.delivery_readiness_status
        == "ready_for_delivery_approval_review"
    )

    assert (
        result.repository_chain_valid
        is True
    )


def test_safe_projection_preserves_no_authority_boundaries():
    result = build_service().verify(
        observation_receipt=(
            build_receipt()
        )
    )

    payload = result.to_dict()

    boundaries = payload[
        "boundaries"
    ]

    assert (
        boundaries[
            "readiness_is_read_only"
        ]
        is True
    )

    assert (
        boundaries[
            "readiness_is_not_delivery_approval"
        ]
        is True
    )

    assert (
        boundaries[
            "readiness_is_not_approved_for_human_delivery"
        ]
        is True
    )

    assert (
        boundaries[
            "readiness_is_not_delivery"
        ]
        is True
    )

    assert (
        boundaries[
            "readiness_is_not_closeout_authority"
        ]
        is True
    )

    assert (
        boundaries[
            "readiness_is_not_intervention_authority"
        ]
        is True
    )

    assert (
        boundaries[
            "existing_commercial_delivery_readiness_is_authoritative"
        ]
        is True
    )

    assert (
        boundaries[
            "pa003_remains_delivery_readiness_authority"
        ]
        is True
    )


def test_verify_rejects_wrong_receipt_type():
    service = build_service()

    with pytest.raises(
        CustomerTrialDeliveryReadinessError,
        match="observation_receipt",
    ):
        service.verify(
            observation_receipt=object(),
        )


def test_verify_requires_execution_observed():
    receipt = replace(
        build_receipt(),
        observation_status=(
            "execution_not_observed"
        ),
    )

    with pytest.raises(
        CustomerTrialDeliveryReadinessStateError,
        match="execution must be observed",
    ):
        build_service().verify(
            observation_receipt=receipt
        )


def test_verify_rejects_hierarchy_mismatch():
    receipt = build_receipt()

    wrong_hierarchy = (
        "tenant-other/"
        + receipt.client_id
        + "/"
        + receipt.engagement_id
        + "/"
        + receipt.assessment_id
    )

    service = build_service(
        readiness_service=(
            StubCommercialReadinessService(
                hierarchy_key=(
                    wrong_hierarchy
                )
            )
        )
    )

    with pytest.raises(
        CustomerTrialDeliveryReadinessIdentityError,
        match="hierarchy",
    ):
        service.verify(
            observation_receipt=receipt
        )


def test_verify_rejects_report_mismatch():
    receipt = build_receipt()

    service = build_service(
        readiness_service=(
            StubCommercialReadinessService(
                report_id="report-other"
            )
        )
    )

    with pytest.raises(
        CustomerTrialDeliveryReadinessLineageError,
        match="report_id",
    ):
        service.verify(
            observation_receipt=receipt
        )


def test_verify_requires_valid_repository_chain():
    receipt = build_receipt()

    service = build_service(
        readiness_service=(
            StubCommercialReadinessService(
                repository_chain_valid=False
            )
        )
    )

    with pytest.raises(
        CustomerTrialDeliveryReadinessStateError,
        match="repository chain",
    ):
        service.verify(
            observation_receipt=receipt
        )


def test_correlate_uses_already_verified_commercial_readiness():
    receipt = build_receipt()

    commercial_readiness = (
        StubCommercialReadinessService()
        .result
    )

    service = build_service()

    result = service.correlate(
        observation_receipt=receipt,
        commercial_readiness=commercial_readiness,
    )

    assert (
        result.readiness_status
        == CONTROLLED_TRIAL_DELIVERY_READY
    )

    assert (
        result.execution_status_hash
        == commercial_readiness.execution_status_hash
    )

    assert (
        result.observation_receipt_hash
        == receipt.receipt_hash
    )

