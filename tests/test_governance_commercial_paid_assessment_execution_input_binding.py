from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from backend.app.gagf.governance_assessment_application import (
    AssessmentExecutionRequest,
    canonical_json,
    sha256_text,
)
from backend.app.gagf.governance_assessment_demonstration import (
    DemonstrationEvidenceInput,
)
from backend.app.gagf.governance_assessment_domain import (
    EvidenceSourceKind,
    EvidenceSourceReference,
)
from backend.app.gagf.governance_assessment_friction_aggregation import (
    ConstraintCategory,
)
from backend.app.gagf.governance_assessment_intervention_plan import (
    InterventionType,
)
from backend.app.gagf.governance_assessment_isolation import (
    CommercialHierarchyContext,
)
from backend.app.gagf.governance_assessment_scope_configuration import (
    EvidenceRequirement,
)
from backend.app.gagf.governance_commercial_paid_assessment_execution_input_binding import (
    COMMERCIAL_PAID_ASSESSMENT_EXECUTION_INPUT_BINDING_VERSION,
    CommercialPaidAssessmentExecutionInputBinding,
    CommercialPaidAssessmentExecutionInputBindingError,
    GovernanceCommercialPaidAssessmentExecutionInputBindingService,
)


def build_request(
    *,
    tenant_id: str = "tenant-1",
    client_id: str = "client-1",
    engagement_id: str = "engagement-1",
    assessment_id: str = "assessment-1",
    csv_text: str | None = None,
    include_tuning: bool = False,
) -> AssessmentExecutionRequest:
    source = EvidenceSourceReference(
        source_id="evidence-1",
        kind=EvidenceSourceKind.CSV,
        display_name="Assessment Evidence",
        source_location="operator-upload.csv",
    )

    evidence_input = DemonstrationEvidenceInput(
        source=source,
        csv_text=(
            csv_text
            if csv_text is not None
            else (
                "event_id,event_type,occurred_at\n"
                "evt-1,APPROVAL_DELAYED,"
                "2026-08-01T12:00:00+00:00\n"
            )
        ),
    )

    implementation_burdens = None
    reversibility_scores = None
    owner_roles = None

    if include_tuning:
        constraint = next(
            iter(
                ConstraintCategory
            )
        )

        intervention = next(
            iter(
                InterventionType
            )
        )

        implementation_burdens = {
            constraint: 2.5,
        }

        reversibility_scores = {
            constraint: 0.75,
        }

        owner_roles = {
            intervention: "Governance Lead",
        }

    return AssessmentExecutionRequest(
        context=CommercialHierarchyContext(
            tenant_id=tenant_id,
            client_id=client_id,
            engagement_id=engagement_id,
            assessment_id=assessment_id,
        ),
        assessment_name="Commercial Governance Assessment",
        workflow_names=(
            "Change Management",
        ),
        organizational_units=(
            "Operations",
        ),
        period_start=date(
            2026,
            8,
            1,
        ),
        period_end=date(
            2026,
            8,
            31,
        ),
        objectives=(
            "Evaluate governance friction",
        ),
        expected_outcomes=(
            "Produce deterministic diagnostic output",
        ),
        evidence_requirements=(
            EvidenceRequirement(
                requirement_id="req-1",
                source_kind=EvidenceSourceKind.CSV,
                description="Governance event evidence",
                required=True,
                minimum_record_count=1,
            ),
        ),
        evidence_inputs=(
            evidence_input,
        ),
        client_display_name=(
            "Client Organization"
        ),
        prepared_by=(
            "FIP Operator"
        ),
        exclusions=(
            "Out-of-scope workflow",
        ),
        implementation_burdens=(
            implementation_burdens
        ),
        reversibility_scores=(
            reversibility_scores
        ),
        owner_roles=(
            owner_roles
        ),
        maximum_priorities=5,
    )


def test_bind_persists_execution_input(
    tmp_path: Path,
):
    service = (
        GovernanceCommercialPaidAssessmentExecutionInputBindingService(
            binding_directory=tmp_path
        )
    )

    request = build_request()

    result = service.bind(
        request=request
    )

    assert result.hierarchy_key == (
        "tenant-1/client-1/"
        "engagement-1/assessment-1"
    )

    assert result.reused_existing is False

    assert result.schema_version == (
        COMMERCIAL_PAID_ASSESSMENT_EXECUTION_INPUT_BINDING_VERSION
    )

    assert (
        result.assessment_execution_request_payload
        == request.to_dict()
    )

    assert (
        result.assessment_execution_request_material[
            "assessment_name"
        ]
        == request.assessment_name
    )

    assert (
        result.assessment_execution_request_material[
            "evidence_requirements"
        ][0]
        == request.evidence_requirements[
            0
        ].to_dict()
    )

    assert len(
        result.evidence_inputs
    ) == 1

    evidence = (
        result.evidence_inputs[
            0
        ]
    )

    assert (
        evidence.evidence_id
        == "evidence-1"
    )

    assert (
        evidence.source_kind
        == "csv"
    )

    assert (
        evidence.csv_text
        == request.evidence_inputs[
            0
        ].csv_text
    )

    assert evidence.content_sha256
    assert result.execution_input_hash
    assert result.binding_hash

    assert (
        service.database_path.exists()
    )


def test_get_recovers_bound_request(
    tmp_path: Path,
):
    service = (
        GovernanceCommercialPaidAssessmentExecutionInputBindingService(
            binding_directory=tmp_path
        )
    )

    request = build_request()

    created = service.bind(
        request=request
    )

    recovered = service.get(
        hierarchy_key=(
            request.context.hierarchy_key
        )
    )

    assert (
        recovered.reused_existing
        is True
    )

    assert (
        recovered.binding_hash
        == created.binding_hash
    )

    assert (
        recovered.execution_input_hash
        == created.execution_input_hash
    )

    assert (
        recovered.assessment_execution_request_hash
        == created.assessment_execution_request_hash
    )

    assert (
        recovered.assessment_execution_request_payload
        == request.to_dict()
    )

    assert (
        recovered.assessment_execution_request_material
        == created.assessment_execution_request_material
    )

    assert (
        recovered.evidence_inputs[
            0
        ].csv_text
        == request.evidence_inputs[
            0
        ].csv_text
    )


def test_reconstruct_request_preserves_original_request(
    tmp_path: Path,
):
    service = (
        GovernanceCommercialPaidAssessmentExecutionInputBindingService(
            binding_directory=tmp_path
        )
    )

    original = build_request()

    binding = service.bind(
        request=original
    )

    recovered_binding = service.get(
        hierarchy_key=(
            original.context.hierarchy_key
        )
    )

    reconstructed = (
        service.reconstruct_request(
            binding=recovered_binding
        )
    )

    assert (
        reconstructed.to_dict()
        == original.to_dict()
    )

    assert (
        reconstructed.context.hierarchy_key
        == original.context.hierarchy_key
    )

    assert (
        reconstructed.evidence_inputs[
            0
        ].csv_text
        == original.evidence_inputs[
            0
        ].csv_text
    )

    assert (
        reconstructed.evidence_requirements[
            0
        ].to_dict()
        == original.evidence_requirements[
            0
        ].to_dict()
    )

    reconstructed_hash = sha256_text(
        canonical_json(
            reconstructed.to_dict()
        )
    )

    assert (
        reconstructed_hash
        == binding.assessment_execution_request_hash
    )


def test_reconstruct_request_preserves_tuning_maps(
    tmp_path: Path,
):
    service = (
        GovernanceCommercialPaidAssessmentExecutionInputBindingService(
            binding_directory=tmp_path
        )
    )

    original = build_request(
        include_tuning=True
    )

    binding = service.bind(
        request=original
    )

    reconstructed = (
        service.reconstruct_request(
            binding=service.get(
                hierarchy_key=(
                    original.context.hierarchy_key
                )
            )
        )
    )

    assert (
        reconstructed.implementation_burdens
        == original.implementation_burdens
    )

    assert (
        reconstructed.reversibility_scores
        == original.reversibility_scores
    )

    assert (
        reconstructed.owner_roles
        == original.owner_roles
    )

    assert (
        reconstructed.maximum_priorities
        == original.maximum_priorities
    )


def test_identical_binding_is_reused(
    tmp_path: Path,
):
    service = (
        GovernanceCommercialPaidAssessmentExecutionInputBindingService(
            binding_directory=tmp_path
        )
    )

    request = build_request()

    first = service.bind(
        request=request
    )

    second = service.bind(
        request=request
    )

    assert (
        first.reused_existing
        is False
    )

    assert (
        second.reused_existing
        is True
    )

    assert (
        second.binding_hash
        == first.binding_hash
    )

    assert (
        second.execution_input_hash
        == first.execution_input_hash
    )

    assert (
        second.created_at
        == first.created_at
    )


def test_different_request_for_same_hierarchy_is_rejected(
    tmp_path: Path,
):
    service = (
        GovernanceCommercialPaidAssessmentExecutionInputBindingService(
            binding_directory=tmp_path
        )
    )

    first = build_request()

    second = build_request(
        csv_text=(
            "event_id,event_type,occurred_at\n"
            "evt-2,WORK_BLOCKED,"
            "2026-08-02T12:00:00+00:00\n"
        )
    )

    service.bind(
        request=first
    )

    with pytest.raises(
        CommercialPaidAssessmentExecutionInputBindingError,
        match="different execution input hash",
    ):
        service.bind(
            request=second
        )


def test_different_hierarchies_can_bind_independently(
    tmp_path: Path,
):
    service = (
        GovernanceCommercialPaidAssessmentExecutionInputBindingService(
            binding_directory=tmp_path
        )
    )

    first = build_request(
        assessment_id="assessment-1"
    )

    second = build_request(
        assessment_id="assessment-2"
    )

    first_result = service.bind(
        request=first
    )

    second_result = service.bind(
        request=second
    )

    assert (
        first_result.hierarchy_key
        != second_result.hierarchy_key
    )

    assert (
        first_result.execution_input_hash
        != second_result.execution_input_hash
    )

    assert (
        first_result.binding_hash
        != second_result.binding_hash
    )


def test_missing_binding_is_rejected(
    tmp_path: Path,
):
    service = (
        GovernanceCommercialPaidAssessmentExecutionInputBindingService(
            binding_directory=tmp_path
        )
    )

    with pytest.raises(
        CommercialPaidAssessmentExecutionInputBindingError,
        match="binding database does not exist",
    ):
        service.get(
            hierarchy_key=(
                "tenant-1/client-1/"
                "engagement-1/missing"
            )
        )


def test_corrupted_reconstruction_material_is_rejected(
    tmp_path: Path,
):
    service = (
        GovernanceCommercialPaidAssessmentExecutionInputBindingService(
            binding_directory=tmp_path
        )
    )

    original = build_request()

    binding = service.bind(
        request=original
    )

    corrupted_material = dict(
        binding.assessment_execution_request_material
    )

    corrupted_material.pop(
        "assessment_name"
    )

    corrupted = (
        CommercialPaidAssessmentExecutionInputBinding(
            hierarchy_key=(
                binding.hierarchy_key
            ),
            assessment_execution_request_hash=(
                binding.assessment_execution_request_hash
            ),
            execution_input_hash=(
                binding.execution_input_hash
            ),
            assessment_execution_request_payload=(
                binding.assessment_execution_request_payload
            ),
            assessment_execution_request_material=(
                corrupted_material
            ),
            evidence_inputs=(
                binding.evidence_inputs
            ),
            binding_hash=(
                binding.binding_hash
            ),
            created_at=(
                binding.created_at
            ),
            reused_existing=True,
            schema_version=(
                binding.schema_version
            ),
        )
    )

    with pytest.raises(
        CommercialPaidAssessmentExecutionInputBindingError,
        match="cannot reconstruct",
    ):
        service.reconstruct_request(
            binding=corrupted
        )


def test_binding_boundaries_do_not_create_authority(
    tmp_path: Path,
):
    service = (
        GovernanceCommercialPaidAssessmentExecutionInputBindingService(
            binding_directory=tmp_path
        )
    )

    result = service.bind(
        request=build_request()
    )

    boundaries = (
        result.to_dict()[
            "boundaries"
        ]
    )

    assert boundaries == {
        "binding_is_not_contract_execution": True,
        "binding_is_not_paid_work_authorization": True,
        "binding_is_not_execution_evidence_approval": True,
        "binding_is_not_execution_authority": True,
        "binding_is_not_recovery_authority": True,
        "binding_is_not_delivery_approval": True,
        "binding_does_not_record_delivery": True,
    }