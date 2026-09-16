from pathlib import Path

from backend.app.gagf.governance_customer_trial_administrative_closeout_observation_receipt_store import (
    GovernanceCustomerTrialAdministrativeCloseoutObservationReceiptStore,
)
from backend.app.gagf.governance_customer_trial_administrative_closeout_observation_service import (
    GovernanceCustomerTrialAdministrativeCloseoutObservationStatusService,
)

from tests.test_governance_customer_trial_administrative_closeout_observation_receipt_store import (
    build_observation,
)


def test_status_returns_incomplete_without_receipt(
    tmp_path: Path,
) -> None:
    store = (
        GovernanceCustomerTrialAdministrativeCloseoutObservationReceiptStore(
            tmp_path / "administrative-closeout-observation.sqlite3"
        )
    )

    result = (
        GovernanceCustomerTrialAdministrativeCloseoutObservationStatusService(
            receipt_store=store
        )
        .status(
            tenant_id="missing-tenant",
            client_id="missing-client",
            engagement_id="missing-engagement",
            assessment_id="missing-assessment",
        )
    )

    assert result.receipt_found is False
    assert result.controlled_trial_complete is False
    assert result.receipt is None
    assert result.hierarchy_key is None
    assert result.controlled_trial_status is None


def test_status_returns_complete_from_persisted_receipt(
    tmp_path: Path,
) -> None:
    store = (
        GovernanceCustomerTrialAdministrativeCloseoutObservationReceiptStore(
            tmp_path / "administrative-closeout-observation.sqlite3"
        )
    )

    written = store.put(
        observation=build_observation(
            tmp_path
        )
    )

    result = (
        GovernanceCustomerTrialAdministrativeCloseoutObservationStatusService(
            receipt_store=store
        )
        .status(
            tenant_id=written.tenant_id,
            client_id=written.client_id,
            engagement_id=written.engagement_id,
            assessment_id=written.assessment_id,
        )
    )

    assert result.receipt_found is True
    assert result.controlled_trial_complete is True
    assert result.receipt is not None

    assert (
        result.controlled_trial_status
        == "controlled_trial_complete"
    )

    assert (
        result.receipt.receipt_hash
        == written.receipt_hash
    )


def test_status_survives_restart(
    tmp_path: Path,
) -> None:
    database_path = (
        tmp_path / "administrative-closeout-observation.sqlite3"
    )

    first_store = (
        GovernanceCustomerTrialAdministrativeCloseoutObservationReceiptStore(
            database_path
        )
    )

    written = first_store.put(
        observation=build_observation(
            tmp_path
        )
    )

    restarted_store = (
        GovernanceCustomerTrialAdministrativeCloseoutObservationReceiptStore(
            database_path
        )
    )

    result = (
        GovernanceCustomerTrialAdministrativeCloseoutObservationStatusService(
            receipt_store=restarted_store
        )
        .status(
            tenant_id=written.tenant_id,
            client_id=written.client_id,
            engagement_id=written.engagement_id,
            assessment_id=written.assessment_id,
        )
    )

    assert result.receipt_found is True
    assert result.controlled_trial_complete is True

    assert (
        result.receipt.receipt_hash
        == written.receipt_hash
    )


def test_status_boundaries_are_read_only(
    tmp_path: Path,
) -> None:
    store = (
        GovernanceCustomerTrialAdministrativeCloseoutObservationReceiptStore(
            tmp_path / "administrative-closeout-observation.sqlite3"
        )
    )

    payload = (
        GovernanceCustomerTrialAdministrativeCloseoutObservationStatusService(
            receipt_store=store
        )
        .status(
            tenant_id="tenant",
            client_id="client",
            engagement_id="engagement",
            assessment_id="assessment",
        )
        .to_dict()
    )

    boundaries = payload["boundaries"]

    assert boundaries["status_is_read_only"] is True

    assert (
        boundaries[
            "status_does_not_recompute_pa010_closeout"
        ]
        is True
    )

    assert (
        boundaries[
            "status_does_not_infer_closeout_from_client_response"
        ]
        is True
    )

    assert (
        boundaries[
            "controlled_trial_complete_is_administrative_only"
        ]
        is True
    )

    assert (
        boundaries[
            "status_is_not_intervention_authority"
        ]
        is True
    )

    assert (
        boundaries[
            "status_is_not_roi_verification"
        ]
        is True
    )