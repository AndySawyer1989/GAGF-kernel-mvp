from dataclasses import FrozenInstanceError
from types import SimpleNamespace

import pytest

from backend.app.gagf.governance_paid_assessment_execution_coordinator import (
    GovernancePaidAssessmentExecutionCoordinator,
    PaidAssessmentExecutionCoordinatorError,
)
from backend.app.gagf.governance_paid_assessment_execution_handoff import (
    PaidAssessmentExecutionHandoff,
    PaidAssessmentExecutionHandoffStatus,
    canonical_json,
    sha256_text,
)


class StubRequest:
    def __init__(
        self,
        *,
        tenant_id="tenant-alpha",
        engagement_id="engagement-001",
        assessment_id="assessment-001",
        assessment_name="Governance Runway Assessment",
    ):
        self.context = SimpleNamespace(
            tenant_id=tenant_id,
            engagement_id=engagement_id,
            assessment_id=assessment_id,
            hierarchy_key="/".join(
                (
                    tenant_id,
                    engagement_id,
                    assessment_id,
                )
            ),
        )
        self.assessment_name = assessment_name

    def to_dict(self):
        return {
            "hierarchy_key": self.context.hierarchy_key,
            "assessment_name": self.assessment_name,
            "workflow_names": ["approval workflow"],
            "organizational_units": ["operations"],
            "period_start": "2026-08-01",
            "period_end": "2026-08-18",
            "objectives": ["Reduce governance friction"],
            "expected_outcomes": ["Identify constraints"],
            "evidence_requirement_count": 1,
            "evidence_input_count": 1,
            "client_display_name": "Example Client",
            "prepared_by": "FIP Operator",
            "exclusions": [],
            "maximum_priorities": 3,
        }


def request_hash(request):
    return sha256_text(
        canonical_json(request.to_dict())
    )


def build_handoff(
    request=None,
    **overrides,
):
    request = request or StubRequest()

    values = {
        "tenant_id": "tenant-alpha",
        "engagement_id": "engagement-001",
        "assessment_id": "assessment-001",
        "contract_execution_event_id": "contract-event-001",
        "contract_execution_event_hash": "a" * 64,
        "paid_work_authorization_id": "paid-auth-001",
        "paid_work_authorization_hash": "b" * 64,
        "assessment_execution_request_hash": request_hash(request),
        "status": PaidAssessmentExecutionHandoffStatus.READY,
        "handoff_hash": "c" * 64,
    }
    values.update(overrides)

    return PaidAssessmentExecutionHandoff(**values)


class FakeApplicationService:
    def __init__(
        self,
        *,
        hierarchy_key=(
            "tenant-alpha/engagement-001/assessment-001"
        ),
        request_hash_override=None,
        completed=True,
        persistence_demonstration_hash=None,
    ):
        self.calls = []
        self.hierarchy_key = hierarchy_key
        self.request_hash_override = request_hash_override
        self.completed_value = completed
        self.persistence_demonstration_hash = (
            persistence_demonstration_hash
        )

    def execute(self, *, request):
        self.calls.append(request)

        actual_request_hash = request_hash(request)
        demonstration_hash = "d" * 64

        persistence_demo_hash = (
            self.persistence_demonstration_hash
            if self.persistence_demonstration_hash is not None
            else demonstration_hash
        )

        demonstration = SimpleNamespace(
            hierarchy_key=self.hierarchy_key,
            demonstration_hash=demonstration_hash,
            report_package=SimpleNamespace(
                report_id="report-001"
            ),
        )

        persistence = SimpleNamespace(
            hierarchy_key=self.hierarchy_key,
            demonstration_hash=persistence_demo_hash,
            persistence_hash="e" * 64,
            artifact_count=10,
        )

        return SimpleNamespace(
            hierarchy_key=self.hierarchy_key,
            request_hash=(
                self.request_hash_override
                if self.request_hash_override is not None
                else actual_request_hash
            ),
            application_hash="f" * 64,
            demonstration=demonstration,
            persistence=persistence,
            completed=self.completed_value,
        )


def build_coordinator(service=None):
    return GovernancePaidAssessmentExecutionCoordinator(
        application_service=(
            service or FakeApplicationService()
        )
    )


def test_executes_exact_request_once():
    request = StubRequest()
    service = FakeApplicationService()

    result = build_coordinator(service).execute(
        handoff=build_handoff(request),
        request=request,
    )

    assert service.calls == [request]
    assert result.application_completed is True


def test_result_preserves_handoff_hierarchy():
    request = StubRequest()

    result = build_coordinator().execute(
        handoff=build_handoff(request),
        request=request,
    )

    assert result.hierarchy_key == (
        "tenant-alpha/engagement-001/assessment-001"
    )


def test_result_preserves_handoff_hash():
    request = StubRequest()
    handoff = build_handoff(request)

    result = build_coordinator().execute(
        handoff=handoff,
        request=request,
    )

    assert result.handoff_hash == handoff.handoff_hash


def test_result_preserves_request_hash():
    request = StubRequest()

    result = build_coordinator().execute(
        handoff=build_handoff(request),
        request=request,
    )

    assert (
        result.assessment_execution_request_hash
        == request_hash(request)
    )
    assert result.application_request_hash == request_hash(request)


def test_result_preserves_application_lineage():
    request = StubRequest()

    result = build_coordinator().execute(
        handoff=build_handoff(request),
        request=request,
    )

    assert result.application_hash == "f" * 64
    assert result.demonstration_hash == "d" * 64
    assert result.persistence_hash == "e" * 64
    assert result.report_id == "report-001"
    assert result.artifact_count == 10


def test_rejects_request_hash_mismatch_before_execution():
    authorized_request = StubRequest()
    changed_request = StubRequest(
        assessment_name="Changed Assessment"
    )
    service = FakeApplicationService()

    with pytest.raises(
        PaidAssessmentExecutionCoordinatorError,
        match="request hash does not match handoff",
    ):
        build_coordinator(service).execute(
            handoff=build_handoff(authorized_request),
            request=changed_request,
        )

    assert service.calls == []


def test_rejects_request_hierarchy_mismatch_before_execution():
    request = StubRequest(
        tenant_id="tenant-beta"
    )
    service = FakeApplicationService()

    handoff = build_handoff(
        request,
        tenant_id="tenant-alpha",
    )

    with pytest.raises(
        PaidAssessmentExecutionCoordinatorError,
        match="request hierarchy does not match handoff",
    ):
        build_coordinator(service).execute(
            handoff=handoff,
            request=request,
        )

    assert service.calls == []


def test_rejects_non_handoff_object():
    request = StubRequest()
    service = FakeApplicationService()

    with pytest.raises(
        PaidAssessmentExecutionCoordinatorError,
        match="PaidAssessmentExecutionHandoff",
    ):
        build_coordinator(service).execute(
            handoff=object(),
            request=request,
        )

    assert service.calls == []


def test_rejects_application_result_hierarchy_mismatch():
    request = StubRequest()

    service = FakeApplicationService(
        hierarchy_key=(
            "tenant-beta/engagement-001/assessment-001"
        )
    )

    with pytest.raises(
        PaidAssessmentExecutionCoordinatorError,
        match="application result hierarchy",
    ):
        build_coordinator(service).execute(
            handoff=build_handoff(request),
            request=request,
        )


def test_rejects_application_request_hash_mismatch():
    request = StubRequest()

    service = FakeApplicationService(
        request_hash_override="0" * 64
    )

    with pytest.raises(
        PaidAssessmentExecutionCoordinatorError,
        match="application result request hash",
    ):
        build_coordinator(service).execute(
            handoff=build_handoff(request),
            request=request,
        )


def test_rejects_incomplete_application_result():
    request = StubRequest()

    service = FakeApplicationService(
        completed=False
    )

    with pytest.raises(
        PaidAssessmentExecutionCoordinatorError,
        match="did not complete",
    ):
        build_coordinator(service).execute(
            handoff=build_handoff(request),
            request=request,
        )


def test_rejects_persistence_demonstration_mismatch():
    request = StubRequest()

    service = FakeApplicationService(
        persistence_demonstration_hash="9" * 64
    )

    with pytest.raises(
        PaidAssessmentExecutionCoordinatorError,
        match="does not reference",
    ):
        build_coordinator(service).execute(
            handoff=build_handoff(request),
            request=request,
        )


def test_execution_result_hash_is_deterministic():
    request = StubRequest()
    handoff = build_handoff(request)

    first = build_coordinator().execute(
        handoff=handoff,
        request=request,
    )
    second = build_coordinator().execute(
        handoff=handoff,
        request=request,
    )

    assert (
        first.execution_result_hash
        == second.execution_result_hash
    )


def test_request_change_cannot_reuse_handoff():
    original = StubRequest()
    changed = StubRequest(
        assessment_name="Different Assessment"
    )

    with pytest.raises(
        PaidAssessmentExecutionCoordinatorError
    ):
        build_coordinator().execute(
            handoff=build_handoff(original),
            request=changed,
        )


def test_result_is_immutable():
    request = StubRequest()

    result = build_coordinator().execute(
        handoff=build_handoff(request),
        request=request,
    )

    with pytest.raises(FrozenInstanceError):
        result.application_hash = "changed"


def test_serialized_result_does_not_claim_customer_outcome():
    request = StubRequest()

    payload = build_coordinator().execute(
        handoff=build_handoff(request),
        request=request,
    ).to_dict()

    assert payload["application_completed"] is True

    forbidden_keys = {
        "customer_outcome_verified",
        "intervention_success",
        "intervention_failure",
        "causation_established",
        "roi_verified",
        "remediation_authorized",
        "rollback_authorized",
        "future_action_authorized",
    }

    assert forbidden_keys.isdisjoint(payload)
