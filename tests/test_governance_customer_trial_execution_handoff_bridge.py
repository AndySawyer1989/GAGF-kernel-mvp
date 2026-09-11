from __future__ import annotations

from types import SimpleNamespace

import pytest

from backend.app.gagf.governance_customer_trial_engagement_package import (
    CustomerTrialEngagementPackage,
    CustomerTrialEvidenceRequirement,
)
from backend.app.gagf.governance_customer_trial_execution_handoff_bridge import (
    CustomerTrialExecutionHandoffBridgeError,
    GovernanceCustomerTrialExecutionHandoffBridge,
)
from backend.app.gagf.governance_customer_trial_preflight_receipt_store import (
    GovernanceCustomerTrialPreflightReceiptStore,
)
from backend.app.gagf.governance_customer_trial_preflight_service import (
    GovernanceCustomerTrialPreflightService,
)
from backend.app.gagf.governance_paid_assessment_execution_handoff import (
    PaidAssessmentExecutionHandoffStatus,
    PaidAssessmentWorkAuthorization,
)


EVALUATED_AT = "2026-09-11T03:30:00+00:00"


class StubAssessmentExecutionRequest:
    def __init__(
        self,
        *,
        tenant_id: str = "tenant-alpha",
        client_id: str = "client-customer-001",
        engagement_id: str = "engagement-trial-001",
        assessment_id: str = "assessment-trial-001",
    ) -> None:
        self.context = SimpleNamespace(
            tenant_id=tenant_id,
            client_id=client_id,
            engagement_id=engagement_id,
            assessment_id=assessment_id,
        )

    def to_dict(
        self,
    ):
        hierarchy_key = "/".join(
            (
                self.context.tenant_id,
                self.context.client_id,
                self.context.engagement_id,
                self.context.assessment_id,
            )
        )

        return {
            "hierarchy_key":
                hierarchy_key,
            "context": {
                "tenant_id":
                    self.context.tenant_id,
                "client_id":
                    self.context.client_id,
                "engagement_id":
                    self.context.engagement_id,
                "assessment_id":
                    self.context.assessment_id,
            },
            "assessment_name":
                "FIP Governance Assessment",
            "workflow_names": [
                "Production change approval"
            ],
            "organizational_units": [
                "Platform Engineering"
            ],
            "period_start":
                "2026-09-01",
            "period_end":
                "2026-09-30",
            "objectives": [
                "Measure governance friction"
            ],
            "expected_outcomes": [
                (
                    "Produce deterministic "
                    "assessment findings"
                )
            ],
            "evidence_requirements": [],
            "maximum_priorities":
                3,
        }


def build_package():
    return CustomerTrialEngagementPackage(
        tenant_id="tenant-alpha",
        client_id="client-customer-001",
        client_display_name="Customer 001",
        engagement_id="engagement-trial-001",
        assessment_id="assessment-trial-001",
        assessment_name=(
            "FIP Governance Assessment"
        ),
        period_start="2026-09-01",
        period_end="2026-09-30",
        workflows=(
            "Production change approval",
        ),
        organizational_units=(
            "Platform Engineering",
        ),
        objectives=(
            "Measure governance friction",
        ),
        expected_outcomes=(
            (
                "Produce deterministic "
                "assessment findings"
            ),
        ),
        evidence_requirements=(
            CustomerTrialEvidenceRequirement(
                requirement_id="EVID-001",
                description=(
                    "Governed workflow evidence"
                ),
                minimum_records=30,
                accepted_formats=("csv",),
            ),
        ),
        data_classification="sanitized",
        prepared_by="FIP Trial Operator",
        customer_deliverables=(
            "Governance assessment report",
        ),
        trial_boundaries=(
            (
                "Assessment ranking does not "
                "establish root cause."
            ),
            (
                "Recommendations do not "
                "authorize implementation."
            ),
            (
                "Assessment does not grant "
                "intervention authority."
            ),
        ),
        completion_criteria=(
            "Governed report delivered",
            "Client receipt recorded",
            "Client response recorded",
            (
                "Administrative closeout "
                "recorded"
            ),
        ),
    )


def build_contract_event():
    return {
        "status": "ok",
        "event_type": (
            "assessment_factory_lite_"
            "contract_execution_event"
        ),
        "package_name":
            "assessment_factory_lite",
        "release": (
            "assessment-factory-lite-"
            "scope-call-conversion"
        ),
        "version": "2.3.0",
        "event_stage":
            "contract_execution",
        "event_status":
            "contract_executed",
        "contract_execution_event_id":
            "contract-event-001",
        "recorded_at":
            "2026-09-11T03:20:00+00:00",
        "execution_evidence": {
            "executed_contract_reference":
                "contract-ref-001",
            "executed_at":
                "2026-09-11T03:15:00+00:00",
            "executed_contract_reference_recorded":
                True,
            "executed_at_recorded":
                True,
            "contract_execution_confirmed":
                True,
            "contract_executed":
                True,
        },
        "event_checklist": {
            "contract_execution_review_ready":
                True,
            "contract_execution_confirmed":
                True,
            "executed_contract_reference_recorded":
                True,
            "executed_at_recorded":
                True,
            "execution_method_recorded":
                True,
            "all_required_signatures_recorded":
                True,
            "human_operator_confirmed_execution":
                True,
            "signature_record_is_not_invoice":
                True,
            "signature_record_is_not_payment":
                True,
            "invoice_not_created":
                True,
            "payment_not_requested":
                True,
            "paid_assessment_not_authorized":
                True,
            "production_onboarding_not_started":
                True,
        },
        "event_blockers": [],
        "commercial_boundary": {
            "contract_execution_recorded":
                True,
            "contract_executed":
                True,
            "invoice_created":
                False,
            "payment_requested":
                False,
            "paid_assessment_authorized":
                False,
            "production_onboarding_authorized":
                False,
            "requires_separate_invoice":
                True,
            "requires_separate_payment_confirmation":
                True,
            "requires_final_paid_work_authorization":
                True,
            "requires_separate_production_onboarding":
                True,
        },
        "governance_boundary": {
            "deterministic_status_required":
                True,
            "gagf_kernel_authoritative":
                True,
            "ai_override_allowed":
                False,
            "human_boundary_required":
                True,
            "release_marker_preserved":
                True,
            "contract_execution_event_is_not_invoice":
                True,
            "contract_execution_event_is_not_payment":
                True,
            (
                "contract_execution_event_is_not_"
                "paid_work_authorization"
            ):
                True,
        },
    }


def build_authorization(
    **overrides,
):
    values = {
        "authorization_id":
            "paid-work-auth-001",
        "tenant_id":
            "tenant-alpha",
        "client_id":
            "client-customer-001",
        "engagement_id":
            "engagement-trial-001",
        "assessment_id":
            "assessment-trial-001",
        "contract_execution_event_id":
            "contract-event-001",
        "authorized_by":
            "FIP Trial Operator",
        "authorized_at":
            "2026-09-11T03:25:00+00:00",
        "paid_assessment_authorized":
            True,
    }

    values.update(
        overrides
    )

    return PaidAssessmentWorkAuthorization(
        **values
    )


def build_services(
    tmp_path,
):
    store = (
        GovernanceCustomerTrialPreflightReceiptStore(
            tmp_path
            / "customer-trial-preflight.sqlite3"
        )
    )

    preflight_service = (
        GovernanceCustomerTrialPreflightService(
            receipt_store=store
        )
    )

    bridge = (
        GovernanceCustomerTrialExecutionHandoffBridge(
            preflight_service=(
                preflight_service
            )
        )
    )

    return (
        preflight_service,
        bridge,
    )


def record_ready_preflight(
    service,
):
    return service.execute(
        package=build_package(),
        evaluated_at=EVALUATED_AT,
    )


def test_ready_preflight_delegates_to_existing_handoff(
    tmp_path,
):
    service, bridge = build_services(
        tmp_path
    )

    preflight = record_ready_preflight(
        service
    )

    result = bridge.prepare_handoff(
        tenant_id="tenant-alpha",
        client_id="client-customer-001",
        engagement_id="engagement-trial-001",
        assessment_id="assessment-trial-001",
        contract_execution_event=(
            build_contract_event()
        ),
        paid_work_authorization=(
            build_authorization()
        ),
        assessment_execution_request=(
            StubAssessmentExecutionRequest()
        ),
    )

    assert result.handoff.status is (
        PaidAssessmentExecutionHandoffStatus.READY
    )

    assert (
        result.preflight_receipt_hash
        == preflight.receipt.receipt_hash
    )

    assert (
        result.preflight_decision_payload_hash
        == (
            preflight.receipt
            .decision_payload_hash
        )
    )

    assert (
        result.preflight_package_hash
        == preflight.decision.package_hash
    )


def test_missing_preflight_receipt_blocks_handoff(
    tmp_path,
):
    _, bridge = build_services(
        tmp_path
    )

    with pytest.raises(
        CustomerTrialExecutionHandoffBridgeError,
        match="persisted preflight receipt",
    ):
        bridge.prepare_handoff(
            tenant_id="tenant-alpha",
            client_id="client-customer-001",
            engagement_id="engagement-trial-001",
            assessment_id="assessment-trial-001",
            contract_execution_event=(
                build_contract_event()
            ),
            paid_work_authorization=(
                build_authorization()
            ),
            assessment_execution_request=(
                StubAssessmentExecutionRequest()
            ),
        )


def test_cross_hierarchy_request_is_rejected(
    tmp_path,
):
    service, bridge = build_services(
        tmp_path
    )

    record_ready_preflight(
        service
    )

    request = (
        StubAssessmentExecutionRequest(
            client_id="client-other"
        )
    )

    with pytest.raises(
        CustomerTrialExecutionHandoffBridgeError,
        match="hierarchy does not match",
    ):
        bridge.prepare_handoff(
            tenant_id="tenant-alpha",
            client_id="client-customer-001",
            engagement_id="engagement-trial-001",
            assessment_id="assessment-trial-001",
            contract_execution_event=(
                build_contract_event()
            ),
            paid_work_authorization=(
                build_authorization()
            ),
            assessment_execution_request=(
                request
            ),
        )


def test_existing_paid_authorization_remains_required(
    tmp_path,
):
    service, _ = build_services(
        tmp_path
    )

    record_ready_preflight(
        service
    )

    with pytest.raises(
        ValueError,
        match="paid_assessment_authorized",
    ):
        build_authorization(
            paid_assessment_authorized=False
        )


def test_contract_event_binding_remains_authoritative(
    tmp_path,
):
    service, bridge = build_services(
        tmp_path
    )

    record_ready_preflight(
        service
    )

    authorization = (
        build_authorization(
            contract_execution_event_id=(
                "other-contract-event"
            )
        )
    )

    with pytest.raises(
        ValueError,
        match=(
            "different "
            "contract_execution_event_id"
        ),
    ):
        bridge.prepare_handoff(
            tenant_id="tenant-alpha",
            client_id="client-customer-001",
            engagement_id="engagement-trial-001",
            assessment_id="assessment-trial-001",
            contract_execution_event=(
                build_contract_event()
            ),
            paid_work_authorization=(
                authorization
            ),
            assessment_execution_request=(
                StubAssessmentExecutionRequest()
            ),
        )


def test_bridge_preserves_non_authority_boundaries(
    tmp_path,
):
    service, bridge = build_services(
        tmp_path
    )

    record_ready_preflight(
        service
    )

    payload = bridge.prepare_handoff(
        tenant_id="tenant-alpha",
        client_id="client-customer-001",
        engagement_id="engagement-trial-001",
        assessment_id="assessment-trial-001",
        contract_execution_event=(
            build_contract_event()
        ),
        paid_work_authorization=(
            build_authorization()
        ),
        assessment_execution_request=(
            StubAssessmentExecutionRequest()
        ),
    ).to_dict()

    boundaries = payload[
        "boundaries"
    ]

    assert (
        boundaries[
            "preflight_receipt_is_not_execution_authority"
        ]
        is True
    )

    assert (
        boundaries[
            "bridge_is_not_paid_work_authority"
        ]
        is True
    )

    assert (
        boundaries[
            "existing_paid_execution_handoff_remains_authoritative"
        ]
        is True
    )

    assert (
        boundaries[
            "intervention_authority_not_granted"
        ]
        is True
    )


def test_bridge_serialization_retains_exact_lineage(
    tmp_path,
):
    service, bridge = build_services(
        tmp_path
    )

    preflight = record_ready_preflight(
        service
    )

    payload = bridge.prepare_handoff(
        tenant_id="tenant-alpha",
        client_id="client-customer-001",
        engagement_id="engagement-trial-001",
        assessment_id="assessment-trial-001",
        contract_execution_event=(
            build_contract_event()
        ),
        paid_work_authorization=(
            build_authorization()
        ),
        assessment_execution_request=(
            StubAssessmentExecutionRequest()
        ),
    ).to_dict()

    lineage = payload[
        "preflight_lineage"
    ]

    assert (
        lineage["receipt_hash"]
        == preflight.receipt.receipt_hash
    )

    assert (
        lineage["decision_payload_hash"]
        == (
            preflight.receipt
            .decision_payload_hash
        )
    )

    assert (
        lineage["package_hash"]
        == preflight.decision.package_hash
    )

    assert (
        len(
            payload["handoff"][
                "handoff_hash"
            ]
        )
        == 64
    )
