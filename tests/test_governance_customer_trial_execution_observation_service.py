from backend.app.gagf.governance_customer_trial_execution_observation import (
    CustomerTrialExecutionObservation,
    EXECUTION_OBSERVED,
)
from backend.app.gagf.governance_customer_trial_execution_observation_receipt_store import (
    GovernanceCustomerTrialExecutionObservationReceiptStore,
)
from backend.app.gagf.governance_customer_trial_execution_observation_service import (
    GovernanceCustomerTrialExecutionObservationStatusService,
)


def build_observation(
) -> CustomerTrialExecutionObservation:
    return CustomerTrialExecutionObservation(
        tenant_id="tenant-controlled",
        client_id="client-controlled",
        engagement_id="engagement-controlled",
        assessment_id="assessment-controlled",
        hierarchy_key=(
            "tenant-controlled/"
            "client-controlled/"
            "engagement-controlled/"
            "assessment-controlled"
        ),
        observation_status=
            EXECUTION_OBSERVED,
        handoff_receipt_hash=
            "handoff-receipt-hash",
        handoff_lineage_hash=
            "handoff-lineage-hash",
        handoff_hash=
            "handoff-hash",
        assessment_execution_request_hash=
            "execution-request-hash",
        execution_result_hash=
            "execution-result-hash",
        application_hash=
            "application-hash",
        persistence_hash=
            "persistence-hash",
        report_id=
            "report-controlled",
        report_package_hash=
            "report-package-hash",
        application_completed=True,
        repository_chain_valid=True,
    )


def test_status_returns_not_found_without_observation(
    tmp_path,
):
    store = (
        GovernanceCustomerTrialExecutionObservationReceiptStore(
            tmp_path / "observation.sqlite3"
        )
    )

    service = (
        GovernanceCustomerTrialExecutionObservationStatusService(
            receipt_store=store
        )
    )

    result = service.status(
        tenant_id="tenant-controlled",
        client_id="client-controlled",
        engagement_id="engagement-controlled",
        assessment_id="assessment-controlled",
    )

    assert result.receipt_found is False
    assert result.receipt is None
    assert result.hierarchy_key is None


def test_status_returns_durable_observation_receipt(
    tmp_path,
):
    store = (
        GovernanceCustomerTrialExecutionObservationReceiptStore(
            tmp_path / "observation.sqlite3"
        )
    )

    written = store.put(
        observation=
            build_observation()
    )

    service = (
        GovernanceCustomerTrialExecutionObservationStatusService(
            receipt_store=store
        )
    )

    result = service.status(
        tenant_id="tenant-controlled",
        client_id="client-controlled",
        engagement_id="engagement-controlled",
        assessment_id="assessment-controlled",
    )

    assert result.receipt_found is True
    assert result.receipt is not None
    assert result.receipt.receipt_hash == (
        written.receipt_hash
    )


def test_status_survives_store_restart(
    tmp_path,
):
    database_path = (
        tmp_path / "observation.sqlite3"
    )

    first_store = (
        GovernanceCustomerTrialExecutionObservationReceiptStore(
            database_path
        )
    )

    written = first_store.put(
        observation=
            build_observation()
    )

    restarted_store = (
        GovernanceCustomerTrialExecutionObservationReceiptStore(
            database_path
        )
    )

    service = (
        GovernanceCustomerTrialExecutionObservationStatusService(
            receipt_store=restarted_store
        )
    )

    result = service.status(
        tenant_id="tenant-controlled",
        client_id="client-controlled",
        engagement_id="engagement-controlled",
        assessment_id="assessment-controlled",
    )

    assert result.receipt_found is True
    assert result.receipt is not None
    assert result.receipt.receipt_hash == (
        written.receipt_hash
    )


def test_status_boundaries_are_read_only(
    tmp_path,
):
    store = (
        GovernanceCustomerTrialExecutionObservationReceiptStore(
            tmp_path / "observation.sqlite3"
        )
    )

    service = (
        GovernanceCustomerTrialExecutionObservationStatusService(
            receipt_store=store
        )
    )

    payload = service.status(
        tenant_id="tenant-controlled",
        client_id="client-controlled",
        engagement_id="engagement-controlled",
        assessment_id="assessment-controlled",
    ).to_dict()

    boundaries = payload[
        "boundaries"
    ]

    assert boundaries[
        "status_is_read_only"
    ] is True

    assert boundaries[
        "status_is_not_execution_authority"
    ] is True

    assert boundaries[
        "status_is_not_recovery_authority"
    ] is True

    assert boundaries[
        "status_is_not_delivery_authority"
    ] is True

    assert boundaries[
        "status_is_not_closeout_authority"
    ] is True

    assert boundaries[
        "status_is_not_intervention_authority"
    ] is True

    assert boundaries[
        "status_does_not_infer_execution_from_handoff"
    ] is True