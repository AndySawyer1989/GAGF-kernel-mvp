from dataclasses import replace
from types import SimpleNamespace

import pytest

from backend.app.gagf.governance_customer_trial_execution_handoff_receipt_store import (
    CustomerTrialExecutionHandoffReceipt,
)
from backend.app.gagf.governance_customer_trial_execution_observation import (
    CustomerTrialExecutionObservationLineageError,
)
from backend.app.gagf.governance_customer_trial_execution_observation_receipt_store import (
    GovernanceCustomerTrialExecutionObservationReceiptStore,
)
from backend.app.gagf.governance_customer_trial_execution_observation_recording_bridge import (
    OBSERVATION_NOT_APPLICABLE,
    OBSERVATION_RECORDED,
    CustomerTrialExecutionObservationRecordingBridgeError,
    GovernanceCustomerTrialExecutionObservationRecordingBridge,
)
from backend.app.gagf.governance_real_paid_assessment_execution import (
    REAL_EXECUTION_STATUS_COMPLETE,
    RealPaidAssessmentExecutionResult,
)


TENANT_ID = "tenant-controlled"
CLIENT_ID = "client-controlled"
ENGAGEMENT_ID = "engagement-controlled"
ASSESSMENT_ID = "assessment-controlled"

HIERARCHY_KEY = (
    f"{TENANT_ID}/"
    f"{CLIENT_ID}/"
    f"{ENGAGEMENT_ID}/"
    f"{ASSESSMENT_ID}"
)

HANDOFF_HASH = "handoff-hash-controlled"
REQUEST_HASH = "execution-request-hash-controlled"


class StubHandoffReceiptStore:
    def __init__(
        self,
        receipt:
            CustomerTrialExecutionHandoffReceipt
            | None,
    ) -> None:
        self._receipt = receipt

    def get(
        self,
        *,
        tenant_id: str,
        client_id: str,
        engagement_id: str,
        assessment_id: str,
    ) -> CustomerTrialExecutionHandoffReceipt | None:
        if self._receipt is None:
            return None

        expected = (
            self._receipt.tenant_id,
            self._receipt.client_id,
            self._receipt.engagement_id,
            self._receipt.assessment_id,
        )

        actual = (
            tenant_id,
            client_id,
            engagement_id,
            assessment_id,
        )

        if actual != expected:
            return None

        return self._receipt


def build_handoff_receipt(
) -> CustomerTrialExecutionHandoffReceipt:
    return CustomerTrialExecutionHandoffReceipt(
        tenant_id=TENANT_ID,
        client_id=CLIENT_ID,
        engagement_id=ENGAGEMENT_ID,
        assessment_id=ASSESSMENT_ID,
        hierarchy_key=HIERARCHY_KEY,
        preflight_receipt_hash=
            "preflight-receipt-hash",
        preflight_decision_payload_hash=
            "preflight-decision-hash",
        preflight_package_hash=
            "preflight-package-hash",
        contract_execution_event_hash=
            "contract-event-hash",
        paid_work_authorization_hash=
            "paid-work-authorization-hash",
        assessment_execution_request_hash=
            REQUEST_HASH,
        handoff_hash=
            HANDOFF_HASH,
        lineage_hash=
            "handoff-lineage-hash",
        receipt_hash=
            "handoff-receipt-hash",
    )


def build_execution_result(
) -> RealPaidAssessmentExecutionResult:
    return RealPaidAssessmentExecutionResult(
        tenant_id=TENANT_ID,
        client_id=CLIENT_ID,
        engagement_id=ENGAGEMENT_ID,
        assessment_id=ASSESSMENT_ID,
        execution_status=
            REAL_EXECUTION_STATUS_COMPLETE,
        handoff_hash=
            HANDOFF_HASH,
        assessment_execution_request_hash=
            REQUEST_HASH,
        application_request_hash=
            "application-request-hash",
        execution_result_hash=
            "execution-result-hash",
        application_hash=
            "application-hash",
        demonstration_hash=
            "demonstration-hash",
        persistence_hash=
            "persistence-hash",
        report_id=
            "report-controlled",
        report_package_hash=
            "report-package-hash",
        artifact_count=10,
        application_completed=True,
        repository_chain_valid=True,
    )


def build_pa015_result(
    *,
    execution_result:
        RealPaidAssessmentExecutionResult
        | None = None,
):
    return SimpleNamespace(
        attempt=SimpleNamespace(
            tenant_id=TENANT_ID,
            client_id=CLIENT_ID,
            engagement_id=ENGAGEMENT_ID,
            assessment_id=ASSESSMENT_ID,
        ),
        execution_result=(
            execution_result
            if execution_result is not None
            else build_execution_result()
        ),
    )


def build_bridge(
    tmp_path,
    *,
    handoff_receipt:
        CustomerTrialExecutionHandoffReceipt
        | None,
):
    observation_store = (
        GovernanceCustomerTrialExecutionObservationReceiptStore(
            tmp_path / "observation.sqlite3"
        )
    )

    bridge = (
        GovernanceCustomerTrialExecutionObservationRecordingBridge(
            handoff_receipt_store=(
                StubHandoffReceiptStore(
                    handoff_receipt
                )
            ),
            observation_receipt_store=(
                observation_store
            ),
        )
    )

    return (
        bridge,
        observation_store,
    )


def test_capture_without_trial_handoff_is_not_applicable(
    tmp_path,
):
    bridge, observation_store = (
        build_bridge(
            tmp_path,
            handoff_receipt=None,
        )
    )

    result = bridge.capture(
        result=
            build_pa015_result()
    )

    assert result.recording_status == (
        OBSERVATION_NOT_APPLICABLE
    )

    assert result.handoff_receipt_found is False
    assert result.observation_receipt is None

    stored = observation_store.get(
        tenant_id=TENANT_ID,
        client_id=CLIENT_ID,
        engagement_id=ENGAGEMENT_ID,
        assessment_id=ASSESSMENT_ID,
    )

    assert stored is None


def test_capture_records_matching_controlled_trial(
    tmp_path,
):
    bridge, observation_store = (
        build_bridge(
            tmp_path,
            handoff_receipt=
                build_handoff_receipt(),
        )
    )

    result = bridge.capture(
        result=
            build_pa015_result()
    )

    assert result.recording_status == (
        OBSERVATION_RECORDED
    )

    assert result.handoff_receipt_found is True
    assert result.observation_receipt is not None

    stored = observation_store.get(
        tenant_id=TENANT_ID,
        client_id=CLIENT_ID,
        engagement_id=ENGAGEMENT_ID,
        assessment_id=ASSESSMENT_ID,
    )

    assert stored is not None

    assert stored.receipt_hash == (
        result.observation_receipt.receipt_hash
    )

    assert stored.handoff_hash == (
        HANDOFF_HASH
    )

    assert stored.assessment_execution_request_hash == (
        REQUEST_HASH
    )


def test_capture_is_idempotent_for_same_pa015_result(
    tmp_path,
):
    bridge, _ = build_bridge(
        tmp_path,
        handoff_receipt=
            build_handoff_receipt(),
    )

    pa015_result = (
        build_pa015_result()
    )

    first = bridge.capture(
        result=pa015_result
    )

    second = bridge.capture(
        result=pa015_result
    )

    assert first.observation_receipt is not None
    assert second.observation_receipt is not None

    assert (
        second.observation_receipt.receipt_hash
        == first.observation_receipt.receipt_hash
    )


def test_capture_fails_closed_on_handoff_hash_mismatch(
    tmp_path,
):
    bridge, _ = build_bridge(
        tmp_path,
        handoff_receipt=
            build_handoff_receipt(),
    )

    execution_result = replace(
        build_execution_result(),
        handoff_hash=
            "different-handoff-hash",
    )

    with pytest.raises(
        CustomerTrialExecutionObservationLineageError
    ):
        bridge.capture(
            result=
                build_pa015_result(
                    execution_result=
                        execution_result
                )
        )


def test_capture_fails_closed_on_request_hash_mismatch(
    tmp_path,
):
    bridge, _ = build_bridge(
        tmp_path,
        handoff_receipt=
            build_handoff_receipt(),
    )

    execution_result = replace(
        build_execution_result(),
        assessment_execution_request_hash=
            "different-request-hash",
    )

    with pytest.raises(
        CustomerTrialExecutionObservationLineageError
    ):
        bridge.capture(
            result=
                build_pa015_result(
                    execution_result=
                        execution_result
                )
        )


def test_capture_requires_pa015_execution_result(
    tmp_path,
):
    bridge, _ = build_bridge(
        tmp_path,
        handoff_receipt=
            build_handoff_receipt(),
    )

    malformed = SimpleNamespace(
        attempt=SimpleNamespace(
            tenant_id=TENANT_ID,
            client_id=CLIENT_ID,
            engagement_id=ENGAGEMENT_ID,
            assessment_id=ASSESSMENT_ID,
        ),
        execution_result=None,
    )

    with pytest.raises(
        CustomerTrialExecutionObservationRecordingBridgeError
    ):
        bridge.capture(
            result=malformed
        )


def test_recording_bridge_boundaries_preserve_pa015_authority(
    tmp_path,
):
    bridge, _ = build_bridge(
        tmp_path,
        handoff_receipt=
            build_handoff_receipt(),
    )

    result = bridge.capture(
        result=
            build_pa015_result()
    )

    boundaries = result.boundaries

    assert boundaries[
        "bridge_is_post_execution_only"
    ] is True

    assert boundaries[
        "bridge_is_not_execution_authority"
    ] is True

    assert boundaries[
        "bridge_is_not_recovery_authority"
    ] is True

    assert boundaries[
        "bridge_is_not_delivery_authority"
    ] is True

    assert boundaries[
        "bridge_is_not_closeout_authority"
    ] is True

    assert boundaries[
        "bridge_is_not_intervention_authority"
    ] is True

    assert boundaries[
        "missing_trial_handoff_does_not_create_observation"
    ] is True

    assert boundaries[
        "pa015_result_is_reused_without_reexecution"
    ] is True