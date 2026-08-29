from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from backend.app.gagf.governance_paid_assessment_execution_handoff import (
    PaidAssessmentWorkAuthorization,
)
from backend.app.gagf.governance_real_paid_assessment_execution_evidence import (
    RealAssessmentExecutionEvidenceApproval,
)
from backend.app.gagf.governance_real_paid_assessment_readiness import (
    ALLOWED_PILOT_CLASSIFICATIONS,
    EvidenceDataClassification,
    RealAssessmentEvidenceDeclaration,
    RealAssessmentStorageDeclaration,
    RealPaidAssessmentIntake,
)


COMMERCIAL_PAID_ASSESSMENT_ADAPTER_VERSION = "0.1.0"


class CommercialPaidAssessmentAdapterError(ValueError):
    """Raised when commercial operator input cannot enter the governed pilot path."""


def _require_text(value: Any, field_name: str) -> str:
    normalized = str(value).strip()

    if not normalized:
        raise CommercialPaidAssessmentAdapterError(
            f"{field_name} must not be empty"
        )

    return normalized


def _require_bool(value: Any, field_name: str) -> bool:
    if not isinstance(value, bool):
        raise CommercialPaidAssessmentAdapterError(
            f"{field_name} must be a boolean"
        )

    return value


@dataclass(frozen=True, slots=True)
class CommercialEvidenceDeclarationInput:
    evidence_id: str
    source_kind: str
    description: str
    classification: str

    client_authorized_for_assessment: bool
    minimization_review_completed: bool
    direct_identifiers_removed: bool

    def __post_init__(self) -> None:
        _require_text(
            self.evidence_id,
            "evidence_id",
        )
        _require_text(
            self.source_kind,
            "source_kind",
        )
        _require_text(
            self.description,
            "description",
        )
        _require_text(
            self.classification,
            "classification",
        )

        _require_bool(
            self.client_authorized_for_assessment,
            "client_authorized_for_assessment",
        )
        _require_bool(
            self.minimization_review_completed,
            "minimization_review_completed",
        )
        _require_bool(
            self.direct_identifiers_removed,
            "direct_identifiers_removed",
        )


@dataclass(frozen=True, slots=True)
class CommercialStorageDeclarationInput:
    repository_path: str

    operator_controlled_location: bool
    access_restricted: bool
    storage_protection_confirmed: bool
    backup_plan_recorded: bool
    retention_period_recorded: bool
    deletion_plan_recorded: bool

    def __post_init__(self) -> None:
        _require_text(
            self.repository_path,
            "repository_path",
        )

        for field_name in (
            "operator_controlled_location",
            "access_restricted",
            "storage_protection_confirmed",
            "backup_plan_recorded",
            "retention_period_recorded",
            "deletion_plan_recorded",
        ):
            _require_bool(
                getattr(self, field_name),
                field_name,
            )


@dataclass(frozen=True, slots=True)
class CommercialPaidWorkAuthorizationInput:
    authorization_id: str
    tenant_id: str
    client_id: str
    engagement_id: str
    assessment_id: str
    contract_execution_event_id: str
    authorized_by: str
    authorized_at: str
    paid_assessment_authorized: bool

    def __post_init__(self) -> None:
        for field_name in (
            "authorization_id",
            "tenant_id",
            "client_id",
            "engagement_id",
            "assessment_id",
            "contract_execution_event_id",
            "authorized_by",
            "authorized_at",
        ):
            _require_text(
                getattr(self, field_name),
                field_name,
            )

        _require_bool(
            self.paid_assessment_authorized,
            "paid_assessment_authorized",
        )

        if self.paid_assessment_authorized is not True:
            raise CommercialPaidAssessmentAdapterError(
                "paid_assessment_authorized must be true"
            )


@dataclass(frozen=True, slots=True)
class CommercialContractExecutionEventInput:
    contract_execution_event_id: str

    contract_executed: bool
    contract_execution_review_ready: bool
    contract_execution_confirmed: bool
    executed_contract_reference_recorded: bool
    executed_at_recorded: bool
    all_required_signatures_recorded: bool
    human_operator_confirmed_execution: bool

    requires_final_paid_work_authorization: bool
    human_boundary_required: bool
    gagf_kernel_authoritative: bool
    ai_override_allowed: bool

    def __post_init__(self) -> None:
        _require_text(
            self.contract_execution_event_id,
            "contract_execution_event_id",
        )

        for field_name in (
            "contract_executed",
            "contract_execution_review_ready",
            "contract_execution_confirmed",
            "executed_contract_reference_recorded",
            "executed_at_recorded",
            "all_required_signatures_recorded",
            "human_operator_confirmed_execution",
            "requires_final_paid_work_authorization",
            "human_boundary_required",
            "gagf_kernel_authoritative",
            "ai_override_allowed",
        ):
            _require_bool(
                getattr(self, field_name),
                field_name,
            )

        for field_name in (
            "contract_executed",
            "contract_execution_review_ready",
            "contract_execution_confirmed",
            "executed_contract_reference_recorded",
            "executed_at_recorded",
            "all_required_signatures_recorded",
            "human_operator_confirmed_execution",
            "requires_final_paid_work_authorization",
            "human_boundary_required",
            "gagf_kernel_authoritative",
        ):
            if getattr(self, field_name) is not True:
                raise CommercialPaidAssessmentAdapterError(
                    f"{field_name} must be true"
                )

        if self.ai_override_allowed is not False:
            raise CommercialPaidAssessmentAdapterError(
                "ai_override_allowed must be false"
            )


@dataclass(frozen=True, slots=True)
class CommercialExecutionEvidenceApprovalInput:
    evidence_id: str
    approved_content_sha256: str
    approved_by: str
    approved_at: str
    execution_evidence_approved: bool

    def __post_init__(self) -> None:
        for field_name in (
            "evidence_id",
            "approved_content_sha256",
            "approved_by",
            "approved_at",
        ):
            _require_text(
                getattr(self, field_name),
                field_name,
            )

        _require_bool(
            self.execution_evidence_approved,
            "execution_evidence_approved",
        )

        if self.execution_evidence_approved is not True:
            raise CommercialPaidAssessmentAdapterError(
                "execution_evidence_approved must be true"
            )


@dataclass(frozen=True, slots=True)
class CommercialPaidAssessmentIntakeInput:
    tenant_id: str
    client_id: str
    engagement_id: str
    assessment_id: str

    client_display_name: str
    assessment_name: str

    operator_name: str
    client_contact_name: str

    assessment_scope_confirmed: bool
    evidence_scope_confirmed: bool
    client_data_use_confirmed: bool
    operator_readiness_confirmed: bool

    evidence: tuple[
        CommercialEvidenceDeclarationInput,
        ...,
    ]
    storage: CommercialStorageDeclarationInput

    def __post_init__(self) -> None:
        for field_name in (
            "tenant_id",
            "client_id",
            "engagement_id",
            "assessment_id",
            "client_display_name",
            "assessment_name",
            "operator_name",
            "client_contact_name",
        ):
            _require_text(
                getattr(self, field_name),
                field_name,
            )

        for field_name in (
            "assessment_scope_confirmed",
            "evidence_scope_confirmed",
            "client_data_use_confirmed",
            "operator_readiness_confirmed",
        ):
            _require_bool(
                getattr(self, field_name),
                field_name,
            )

        if not self.evidence:
            raise CommercialPaidAssessmentAdapterError(
                "at least one evidence declaration is required"
            )

        if not isinstance(
            self.storage,
            CommercialStorageDeclarationInput,
        ):
            raise CommercialPaidAssessmentAdapterError(
                "storage must be a CommercialStorageDeclarationInput"
            )


class GovernanceCommercialPaidAssessmentAdapter:
    """
    Convert explicit commercial operator input into existing governed
    real-paid-assessment domain contracts.

    This adapter does not:
    - create paid-work authority from intake,
    - infer paid-work authorization,
    - infer contract execution,
    - infer execution-evidence approval,
    - approve evidence automatically,
    - establish execution authority,
    - authorize execution or recovery,
    - execute an assessment,
    - approve delivery,
    - record delivery.
    """

    def build_execution_evidence_approval(
        self,
        *,
        payload: CommercialExecutionEvidenceApprovalInput,
    ) -> RealAssessmentExecutionEvidenceApproval:
        if not isinstance(
            payload,
            CommercialExecutionEvidenceApprovalInput,
        ):
            raise CommercialPaidAssessmentAdapterError(
                "payload must be a "
                "CommercialExecutionEvidenceApprovalInput"
            )

        try:
            return RealAssessmentExecutionEvidenceApproval(
                evidence_id=payload.evidence_id,
                approved_content_sha256=(
                    payload.approved_content_sha256
                ),
                approved_by=payload.approved_by,
                approved_at=payload.approved_at,
                execution_evidence_approved=(
                    payload.execution_evidence_approved
                ),
            )
        except Exception as exc:
            raise CommercialPaidAssessmentAdapterError(
                "execution-evidence approval is invalid: "
                f"{exc}"
            ) from exc

    def build_contract_execution_event(
        self,
        *,
        payload: CommercialContractExecutionEventInput,
    ) -> dict[str, Any]:
        if not isinstance(
            payload,
            CommercialContractExecutionEventInput,
        ):
            raise CommercialPaidAssessmentAdapterError(
                "payload must be a "
                "CommercialContractExecutionEventInput"
            )

        return {
            "status": "ok",
            "event_type": (
                "assessment_factory_lite_contract_execution_event"
            ),
            "event_status": "contract_executed",
            "contract_execution_event_id": (
                payload.contract_execution_event_id
            ),
            "execution_evidence": {
                "contract_executed": (
                    payload.contract_executed
                ),
            },
            "event_checklist": {
                "contract_execution_review_ready": (
                    payload.contract_execution_review_ready
                ),
                "contract_execution_confirmed": (
                    payload.contract_execution_confirmed
                ),
                "executed_contract_reference_recorded": (
                    payload.executed_contract_reference_recorded
                ),
                "executed_at_recorded": (
                    payload.executed_at_recorded
                ),
                "all_required_signatures_recorded": (
                    payload.all_required_signatures_recorded
                ),
                "human_operator_confirmed_execution": (
                    payload.human_operator_confirmed_execution
                ),
            },
            "commercial_boundary": {
                "contract_executed": True,
                "paid_assessment_authorized": False,
                "requires_final_paid_work_authorization": (
                    payload.requires_final_paid_work_authorization
                ),
            },
            "governance_boundary": {
                "human_boundary_required": (
                    payload.human_boundary_required
                ),
                "gagf_kernel_authoritative": (
                    payload.gagf_kernel_authoritative
                ),
                "ai_override_allowed": (
                    payload.ai_override_allowed
                ),
                (
                    "contract_execution_event_is_not_"
                    "paid_work_authorization"
                ): True,
            },
            "event_blockers": [],
        }

    def build_paid_work_authorization(
        self,
        *,
        payload: CommercialPaidWorkAuthorizationInput,
    ) -> PaidAssessmentWorkAuthorization:
        if not isinstance(
            payload,
            CommercialPaidWorkAuthorizationInput,
        ):
            raise CommercialPaidAssessmentAdapterError(
                "payload must be a "
                "CommercialPaidWorkAuthorizationInput"
            )

        try:
            return PaidAssessmentWorkAuthorization(
                authorization_id=payload.authorization_id,
                tenant_id=payload.tenant_id,
                client_id=payload.client_id,
                engagement_id=payload.engagement_id,
                assessment_id=payload.assessment_id,
                contract_execution_event_id=(
                    payload.contract_execution_event_id
                ),
                authorized_by=payload.authorized_by,
                authorized_at=payload.authorized_at,
                paid_assessment_authorized=(
                    payload.paid_assessment_authorized
                ),
            )
        except Exception as exc:
            raise CommercialPaidAssessmentAdapterError(
                "paid-work authorization is invalid: "
                f"{exc}"
            ) from exc

    def build_intake(
        self,
        *,
        payload: CommercialPaidAssessmentIntakeInput,
    ) -> RealPaidAssessmentIntake:
        if not isinstance(
            payload,
            CommercialPaidAssessmentIntakeInput,
        ):
            raise CommercialPaidAssessmentAdapterError(
                "payload must be a CommercialPaidAssessmentIntakeInput"
            )

        evidence = tuple(
            self._build_evidence_declaration(item)
            for item in payload.evidence
        )

        storage = RealAssessmentStorageDeclaration(
            repository_path=payload.storage.repository_path,
            operator_controlled_location=(
                payload.storage.operator_controlled_location
            ),
            access_restricted=(
                payload.storage.access_restricted
            ),
            storage_protection_confirmed=(
                payload.storage.storage_protection_confirmed
            ),
            backup_plan_recorded=(
                payload.storage.backup_plan_recorded
            ),
            retention_period_recorded=(
                payload.storage.retention_period_recorded
            ),
            deletion_plan_recorded=(
                payload.storage.deletion_plan_recorded
            ),
        )

        return RealPaidAssessmentIntake(
            tenant_id=payload.tenant_id,
            client_id=payload.client_id,
            engagement_id=payload.engagement_id,
            assessment_id=payload.assessment_id,
            client_display_name=payload.client_display_name,
            assessment_name=payload.assessment_name,
            operator_name=payload.operator_name,
            client_contact_name=payload.client_contact_name,
            assessment_scope_confirmed=(
                payload.assessment_scope_confirmed
            ),
            evidence_scope_confirmed=(
                payload.evidence_scope_confirmed
            ),
            client_data_use_confirmed=(
                payload.client_data_use_confirmed
            ),
            operator_readiness_confirmed=(
                payload.operator_readiness_confirmed
            ),
            evidence=evidence,
            storage=storage,
        )

    def _build_evidence_declaration(
        self,
        payload: CommercialEvidenceDeclarationInput,
    ) -> RealAssessmentEvidenceDeclaration:
        try:
            classification = EvidenceDataClassification(
                payload.classification
            )
        except ValueError as exc:
            raise CommercialPaidAssessmentAdapterError(
                "classification is not recognized: "
                f"{payload.classification}"
            ) from exc

        if classification not in ALLOWED_PILOT_CLASSIFICATIONS:
            raise CommercialPaidAssessmentAdapterError(
                "classification is not permitted for the current "
                f"paid-assessment pilot: {classification.value}"
            )

        return RealAssessmentEvidenceDeclaration(
            evidence_id=payload.evidence_id,
            source_kind=payload.source_kind,
            description=payload.description,
            classification=classification,
            client_authorized_for_assessment=(
                payload.client_authorized_for_assessment
            ),
            minimization_review_completed=(
                payload.minimization_review_completed
            ),
            direct_identifiers_removed=(
                payload.direct_identifiers_removed
            ),
        )