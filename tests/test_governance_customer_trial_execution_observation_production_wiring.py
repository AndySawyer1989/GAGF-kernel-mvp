from backend.app.gagf.governance_commercial_paid_assessment_execution import (
    GovernanceCommercialPaidAssessmentExecutionService,
)
from backend.app.gagf.governance_customer_trial_execution_observation_recording_bridge import (
    GovernanceCustomerTrialExecutionObservationRecordingBridge,
)


def test_commercial_execution_service_recorder_disabled_by_default(
    tmp_path,
):
    service = (
        GovernanceCommercialPaidAssessmentExecutionService(
            execution_directory=(
                tmp_path / "executions"
            )
        )
    )

    assert (
        service._customer_trial_observation_recorder
        is None
    )


def test_commercial_execution_service_accepts_observation_recorder(
    tmp_path,
):
    class StubHandoffStore:
        def get(
            self,
            *,
            tenant_id,
            client_id,
            engagement_id,
            assessment_id,
        ):
            return None

    from backend.app.gagf.governance_customer_trial_execution_observation_receipt_store import (
        GovernanceCustomerTrialExecutionObservationReceiptStore,
    )

    service = (
        GovernanceCommercialPaidAssessmentExecutionService(
            execution_directory=(
                tmp_path / "executions"
            )
        )
    )

    recorder = (
        GovernanceCustomerTrialExecutionObservationRecordingBridge(
            handoff_receipt_store=
                StubHandoffStore(),
            observation_receipt_store=(
                GovernanceCustomerTrialExecutionObservationReceiptStore(
                    tmp_path / "observation.sqlite3"
                )
            ),
        )
    )

    service.configure_customer_trial_observation_recorder(
        recorder=recorder
    )

    assert (
        service._customer_trial_observation_recorder
        is recorder
    )


def test_main_exposes_same_observation_recorder_on_paid_service():
    from backend.app.main import app

    paid_service = (
        app.state
        .governance_commercial_paid_assessment_execution_service
    )

    recorder = (
        app.state
        .governance_customer_trial_execution_observation_recording_bridge
    )

    assert (
        paid_service
        ._customer_trial_observation_recorder
        is recorder
    )


def test_main_recorder_reuses_registered_customer_trial_stores():
    from backend.app.main import app

    recorder = (
        app.state
        .governance_customer_trial_execution_observation_recording_bridge
    )

    assert (
        recorder._handoff_receipt_store
        is app.state
        .governance_customer_trial_execution_handoff_receipt_store
    )

    assert (
        recorder._observation_receipt_store
        is app.state
        .governance_customer_trial_execution_observation_receipt_store
    )