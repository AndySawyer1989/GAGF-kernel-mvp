from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from backend.app.gagf.governance_assessment_application import (
    AssessmentExecutionRequest,
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


COMMERCIAL_PAID_ASSESSMENT_EXECUTION_INPUT_BINDING_VERSION = "1.2.0"

COMMERCIAL_PAID_ASSESSMENT_EXECUTION_INPUT_BINDING_DATABASE = (
    "commercial-paid-assessment-execution-input-bindings.sqlite3"
)


class CommercialPaidAssessmentExecutionInputBindingError(
    RuntimeError
):
    """
    Raised when a commercial paid-assessment execution input
    cannot be immutably bound, verified, or reconstructed.
    """


def canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


def sha256_text(value: str) -> str:
    return hashlib.sha256(
        value.encode("utf-8")
    ).hexdigest()


def utc_now_iso() -> str:
    return datetime.now(
        timezone.utc
    ).isoformat()


@dataclass(frozen=True, slots=True)
class CommercialPaidAssessmentEvidenceInputBinding:
    evidence_id: str
    source_id: str
    source_kind: str
    display_name: str
    source_location: str
    csv_text: str
    content_sha256: str

    def __post_init__(self) -> None:
        if not self.evidence_id.strip():
            raise CommercialPaidAssessmentExecutionInputBindingError(
                "evidence_id must not be empty"
            )

        if not self.source_id.strip():
            raise CommercialPaidAssessmentExecutionInputBindingError(
                "source_id must not be empty"
            )

        if not self.source_kind.strip():
            raise CommercialPaidAssessmentExecutionInputBindingError(
                "source_kind must not be empty"
            )

        if not isinstance(
            self.csv_text,
            str,
        ):
            raise CommercialPaidAssessmentExecutionInputBindingError(
                "csv_text must be text"
            )

        if not self.csv_text.strip():
            raise CommercialPaidAssessmentExecutionInputBindingError(
                "csv_text must not be empty"
            )

        expected_hash = sha256_text(
            self.csv_text
        )

        if self.content_sha256 != expected_hash:
            raise CommercialPaidAssessmentExecutionInputBindingError(
                "content_sha256 does not match csv_text"
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "evidence_id": self.evidence_id,
            "source_id": self.source_id,
            "source_kind": self.source_kind,
            "display_name": self.display_name,
            "source_location": self.source_location,
            "csv_text": self.csv_text,
            "content_sha256": self.content_sha256,
        }

    def commitment_dict(self) -> dict[str, Any]:
        return {
            "evidence_id": self.evidence_id,
            "source_id": self.source_id,
            "source_kind": self.source_kind,
            "display_name": self.display_name,
            "source_location": self.source_location,
            "content_sha256": self.content_sha256,
        }


@dataclass(frozen=True, slots=True)
class CommercialPaidAssessmentExecutionInputBinding:
    hierarchy_key: str
    assessment_execution_request_hash: str
    execution_input_hash: str
    assessment_execution_request_payload: dict[str, Any]
    assessment_execution_request_material: dict[str, Any]
    evidence_inputs: tuple[
        CommercialPaidAssessmentEvidenceInputBinding,
        ...,
    ]
    binding_hash: str
    created_at: str
    reused_existing: bool
    schema_version: str = (
        COMMERCIAL_PAID_ASSESSMENT_EXECUTION_INPUT_BINDING_VERSION
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "hierarchy_key": self.hierarchy_key,
            "assessment_execution_request_hash": (
                self.assessment_execution_request_hash
            ),
            "execution_input_hash": self.execution_input_hash,
            "assessment_execution_request_payload": (
                self.assessment_execution_request_payload
            ),
            "assessment_execution_request_material": (
                self.assessment_execution_request_material
            ),
            "evidence_inputs": [
                item.to_dict()
                for item in self.evidence_inputs
            ],
            "binding_hash": self.binding_hash,
            "created_at": self.created_at,
            "reused_existing": self.reused_existing,
            "schema_version": self.schema_version,
            "boundaries": {
                "binding_is_not_contract_execution": True,
                "binding_is_not_paid_work_authorization": True,
                "binding_is_not_execution_evidence_approval": True,
                "binding_is_not_execution_authority": True,
                "binding_is_not_recovery_authority": True,
                "binding_is_not_delivery_approval": True,
                "binding_does_not_record_delivery": True,
            },
        }


class GovernanceCommercialPaidAssessmentExecutionInputBindingService:
    """
    Persist exact execution-capable assessment input separately from the
    ordinary ten-artifact governance-assessment chain.

    The binding preserves enough material to reconstruct the original
    AssessmentExecutionRequest server-side without asking the browser to
    resend authoritative execution evidence.

    assessment_execution_request_hash remains the existing canonical
    AssessmentExecutionRequest.to_dict() commitment.

    execution_input_hash covers the complete reconstructable request
    material plus exact raw evidence.

    This service does not:
    - establish contract execution,
    - establish paid-work authorization,
    - approve execution evidence,
    - establish execution authority,
    - establish recovery authority,
    - execute an assessment,
    - approve delivery,
    - record delivery.

    PA015 remains the authoritative execution/recovery path.
    """

    def __init__(
        self,
        *,
        binding_directory: str | Path,
    ) -> None:
        directory = Path(
            binding_directory
        )

        if not str(directory).strip():
            raise CommercialPaidAssessmentExecutionInputBindingError(
                "binding_directory must not be empty"
            )

        self.binding_directory = directory

        self.database_path = (
            directory
            / COMMERCIAL_PAID_ASSESSMENT_EXECUTION_INPUT_BINDING_DATABASE
        )

    def bind(
        self,
        *,
        request: AssessmentExecutionRequest,
    ) -> CommercialPaidAssessmentExecutionInputBinding:
        if not isinstance(
            request,
            AssessmentExecutionRequest,
        ):
            raise CommercialPaidAssessmentExecutionInputBindingError(
                "request must be an AssessmentExecutionRequest"
            )

        hierarchy_key = (
            request.context.hierarchy_key.strip()
        )

        if not hierarchy_key:
            raise CommercialPaidAssessmentExecutionInputBindingError(
                "request hierarchy_key must not be empty"
            )

        request_payload = (
            request.to_dict()
        )

        request_material = (
            self._request_material(
                request=request
            )
        )

        assessment_execution_request_hash = sha256_text(
            canonical_json(
                request_payload
            )
        )

        evidence_inputs = tuple(
            self._build_evidence_binding(
                evidence_input=evidence_input,
            )
            for evidence_input in request.evidence_inputs
        )

        if not evidence_inputs:
            raise CommercialPaidAssessmentExecutionInputBindingError(
                "at least one evidence input is required"
            )

        execution_input_payload = (
            self._execution_input_payload(
                hierarchy_key=hierarchy_key,
                assessment_execution_request_material=(
                    request_material
                ),
                evidence_inputs=evidence_inputs,
            )
        )

        execution_input_hash = sha256_text(
            canonical_json(
                execution_input_payload
            )
        )

        binding_payload = (
            self._binding_payload(
                hierarchy_key=hierarchy_key,
                assessment_execution_request_hash=(
                    assessment_execution_request_hash
                ),
                execution_input_hash=(
                    execution_input_hash
                ),
                evidence_inputs=evidence_inputs,
            )
        )

        binding_hash = sha256_text(
            canonical_json(
                binding_payload
            )
        )

        self.binding_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        self._initialize_database()

        with self._connect() as connection:
            existing = connection.execute(
                """
                SELECT
                    hierarchy_key,
                    assessment_execution_request_hash,
                    execution_input_hash,
                    assessment_execution_request_payload_json,
                    assessment_execution_request_material_json,
                    evidence_inputs_json,
                    binding_hash,
                    created_at,
                    schema_version
                FROM commercial_paid_assessment_execution_input_bindings
                WHERE hierarchy_key = ?
                """,
                (
                    hierarchy_key,
                ),
            ).fetchone()

            if existing is not None:
                return self._validate_existing(
                    row=existing,
                    expected_request_hash=(
                        assessment_execution_request_hash
                    ),
                    expected_execution_input_hash=(
                        execution_input_hash
                    ),
                    expected_request_payload=(
                        request_payload
                    ),
                    expected_request_material=(
                        request_material
                    ),
                    expected_evidence_inputs=(
                        evidence_inputs
                    ),
                    expected_binding_hash=(
                        binding_hash
                    ),
                )

            created_at = utc_now_iso()

            connection.execute(
                """
                INSERT INTO
                commercial_paid_assessment_execution_input_bindings (
                    hierarchy_key,
                    assessment_execution_request_hash,
                    execution_input_hash,
                    assessment_execution_request_payload_json,
                    assessment_execution_request_material_json,
                    evidence_inputs_json,
                    binding_hash,
                    created_at,
                    schema_version
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    hierarchy_key,
                    assessment_execution_request_hash,
                    execution_input_hash,
                    canonical_json(
                        request_payload
                    ),
                    canonical_json(
                        request_material
                    ),
                    canonical_json(
                        [
                            item.to_dict()
                            for item in evidence_inputs
                        ]
                    ),
                    binding_hash,
                    created_at,
                    (
                        COMMERCIAL_PAID_ASSESSMENT_EXECUTION_INPUT_BINDING_VERSION
                    ),
                ),
            )

            connection.commit()

        return CommercialPaidAssessmentExecutionInputBinding(
            hierarchy_key=hierarchy_key,
            assessment_execution_request_hash=(
                assessment_execution_request_hash
            ),
            execution_input_hash=(
                execution_input_hash
            ),
            assessment_execution_request_payload=(
                request_payload
            ),
            assessment_execution_request_material=(
                request_material
            ),
            evidence_inputs=evidence_inputs,
            binding_hash=binding_hash,
            created_at=created_at,
            reused_existing=False,
        )

    def get(
        self,
        *,
        hierarchy_key: str,
    ) -> CommercialPaidAssessmentExecutionInputBinding:
        normalized_hierarchy = (
            hierarchy_key.strip()
        )

        if not normalized_hierarchy:
            raise CommercialPaidAssessmentExecutionInputBindingError(
                "hierarchy_key must not be empty"
            )

        if not self.database_path.exists():
            raise CommercialPaidAssessmentExecutionInputBindingError(
                "commercial paid-assessment execution-input "
                "binding database does not exist"
            )

        self._initialize_database()

        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT
                    hierarchy_key,
                    assessment_execution_request_hash,
                    execution_input_hash,
                    assessment_execution_request_payload_json,
                    assessment_execution_request_material_json,
                    evidence_inputs_json,
                    binding_hash,
                    created_at,
                    schema_version
                FROM commercial_paid_assessment_execution_input_bindings
                WHERE hierarchy_key = ?
                """,
                (
                    normalized_hierarchy,
                ),
            ).fetchone()

        if row is None:
            raise CommercialPaidAssessmentExecutionInputBindingError(
                "commercial paid-assessment execution-input "
                "binding does not exist for hierarchy"
            )

        return self._binding_from_row(
            row=row,
            reused_existing=True,
        )

    def reconstruct_request(
        self,
        *,
        binding: CommercialPaidAssessmentExecutionInputBinding,
    ) -> AssessmentExecutionRequest:
        if not isinstance(
            binding,
            CommercialPaidAssessmentExecutionInputBinding,
        ):
            raise CommercialPaidAssessmentExecutionInputBindingError(
                "binding must be a "
                "CommercialPaidAssessmentExecutionInputBinding"
            )

        material = (
            binding.assessment_execution_request_material
        )

        try:
            context_payload = material[
                "context"
            ]

            context = CommercialHierarchyContext(
                tenant_id=str(
                    context_payload[
                        "tenant_id"
                    ]
                ),
                client_id=str(
                    context_payload[
                        "client_id"
                    ]
                ),
                engagement_id=str(
                    context_payload[
                        "engagement_id"
                    ]
                ),
                assessment_id=str(
                    context_payload[
                        "assessment_id"
                    ]
                ),
            )

            evidence_requirements = tuple(
                EvidenceRequirement(
                    requirement_id=str(
                        item[
                            "requirement_id"
                        ]
                    ),
                    source_kind=EvidenceSourceKind(
                        item[
                            "source_kind"
                        ]
                    ),
                    description=str(
                        item[
                            "description"
                        ]
                    ),
                    required=bool(
                        item[
                            "required"
                        ]
                    ),
                    minimum_record_count=int(
                        item[
                            "minimum_record_count"
                        ]
                    ),
                )
                for item in material[
                    "evidence_requirements"
                ]
            )

            evidence_inputs = tuple(
                DemonstrationEvidenceInput(
                    source=EvidenceSourceReference(
                        source_id=(
                            item.source_id
                        ),
                        kind=EvidenceSourceKind(
                            item.source_kind
                        ),
                        display_name=(
                            item.display_name
                        ),
                        source_location=(
                            item.source_location
                            if item.source_location
                            else None
                        ),
                    ),
                    csv_text=item.csv_text,
                )
                for item in binding.evidence_inputs
            )

            implementation_burdens_payload = (
                material[
                    "implementation_burdens"
                ]
            )

            reversibility_scores_payload = (
                material[
                    "reversibility_scores"
                ]
            )

            owner_roles_payload = (
                material[
                    "owner_roles"
                ]
            )

            implementation_burdens = (
                {
                    ConstraintCategory(
                        key
                    ): float(
                        value
                    )
                    for key, value
                    in implementation_burdens_payload.items()
                }
                if implementation_burdens_payload
                is not None
                else None
            )

            reversibility_scores = (
                {
                    ConstraintCategory(
                        key
                    ): float(
                        value
                    )
                    for key, value
                    in reversibility_scores_payload.items()
                }
                if reversibility_scores_payload
                is not None
                else None
            )

            owner_roles = (
                {
                    InterventionType(
                        key
                    ): str(
                        value
                    )
                    for key, value
                    in owner_roles_payload.items()
                }
                if owner_roles_payload
                is not None
                else None
            )

            request = AssessmentExecutionRequest(
                context=context,
                assessment_name=str(
                    material[
                        "assessment_name"
                    ]
                ),
                workflow_names=tuple(
                    str(value)
                    for value in material[
                        "workflow_names"
                    ]
                ),
                organizational_units=tuple(
                    str(value)
                    for value in material[
                        "organizational_units"
                    ]
                ),
                period_start=date.fromisoformat(
                    str(
                        material[
                            "period_start"
                        ]
                    )
                ),
                period_end=date.fromisoformat(
                    str(
                        material[
                            "period_end"
                        ]
                    )
                ),
                objectives=tuple(
                    str(value)
                    for value in material[
                        "objectives"
                    ]
                ),
                expected_outcomes=tuple(
                    str(value)
                    for value in material[
                        "expected_outcomes"
                    ]
                ),
                evidence_requirements=(
                    evidence_requirements
                ),
                evidence_inputs=(
                    evidence_inputs
                ),
                client_display_name=str(
                    material[
                        "client_display_name"
                    ]
                ),
                prepared_by=str(
                    material[
                        "prepared_by"
                    ]
                ),
                exclusions=tuple(
                    str(value)
                    for value in material[
                        "exclusions"
                    ]
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
                maximum_priorities=int(
                    material[
                        "maximum_priorities"
                    ]
                ),
            )

        except (
            KeyError,
            TypeError,
            ValueError,
        ) as exc:
            raise CommercialPaidAssessmentExecutionInputBindingError(
                "stored execution-input binding cannot "
                "reconstruct AssessmentExecutionRequest"
            ) from exc

        if (
            request.context.hierarchy_key
            != binding.hierarchy_key
        ):
            raise CommercialPaidAssessmentExecutionInputBindingError(
                "reconstructed request hierarchy does not "
                "match execution-input binding"
            )

        reconstructed_request_hash = sha256_text(
            canonical_json(
                request.to_dict()
            )
        )

        if (
            reconstructed_request_hash
            != binding.assessment_execution_request_hash
        ):
            raise CommercialPaidAssessmentExecutionInputBindingError(
                "reconstructed assessment execution request "
                "hash does not match binding"
            )

        reconstructed_material = (
            self._request_material(
                request=request
            )
        )

        if (
            canonical_json(
                reconstructed_material
            )
            != canonical_json(
                binding.assessment_execution_request_material
            )
        ):
            raise CommercialPaidAssessmentExecutionInputBindingError(
                "reconstructed assessment execution request "
                "material does not match binding"
            )

        return request

    def _build_evidence_binding(
        self,
        *,
        evidence_input: Any,
    ) -> CommercialPaidAssessmentEvidenceInputBinding:
        source = evidence_input.source
        csv_text = evidence_input.csv_text

        if not isinstance(
            csv_text,
            str,
        ):
            raise CommercialPaidAssessmentExecutionInputBindingError(
                "evidence csv_text must be text"
            )

        if not csv_text.strip():
            raise CommercialPaidAssessmentExecutionInputBindingError(
                "evidence csv_text must not be empty"
            )

        source_id = str(
            source.source_id
        ).strip()

        if not source_id:
            raise CommercialPaidAssessmentExecutionInputBindingError(
                "evidence source_id must not be empty"
            )

        source_kind = (
            source.kind.value
            if hasattr(
                source.kind,
                "value",
            )
            else str(
                source.kind
            )
        )

        return CommercialPaidAssessmentEvidenceInputBinding(
            evidence_id=source_id,
            source_id=source_id,
            source_kind=str(
                source_kind
            ),
            display_name=str(
                source.display_name
            ).strip(),
            source_location=(
                str(
                    source.source_location
                ).strip()
                if source.source_location
                is not None
                else ""
            ),
            csv_text=csv_text,
            content_sha256=sha256_text(
                csv_text
            ),
        )

    def _request_material(
        self,
        *,
        request: AssessmentExecutionRequest,
    ) -> dict[str, Any]:
        def serialize_constraint_map(
            value: dict[
                ConstraintCategory,
                float,
            ] | None,
        ) -> dict[str, float] | None:
            if value is None:
                return None

            return {
                (
                    key.value
                    if hasattr(
                        key,
                        "value",
                    )
                    else str(
                        key
                    )
                ): float(
                    item
                )
                for key, item
                in value.items()
            }

        def serialize_owner_roles(
            value: dict[
                InterventionType,
                str,
            ] | None,
        ) -> dict[str, str] | None:
            if value is None:
                return None

            return {
                (
                    key.value
                    if hasattr(
                        key,
                        "value",
                    )
                    else str(
                        key
                    )
                ): str(
                    item
                )
                for key, item
                in value.items()
            }

        return {
            "context": {
                "tenant_id": (
                    request.context.tenant_id
                ),
                "client_id": (
                    request.context.client_id
                ),
                "engagement_id": (
                    request.context.engagement_id
                ),
                "assessment_id": (
                    request.context.assessment_id
                ),
            },
            "assessment_name": (
                request.assessment_name
            ),
            "workflow_names": list(
                request.workflow_names
            ),
            "organizational_units": list(
                request.organizational_units
            ),
            "period_start": (
                request.period_start.isoformat()
            ),
            "period_end": (
                request.period_end.isoformat()
            ),
            "objectives": list(
                request.objectives
            ),
            "expected_outcomes": list(
                request.expected_outcomes
            ),
            "evidence_requirements": [
                requirement.to_dict()
                for requirement
                in request.evidence_requirements
            ],
            "client_display_name": (
                request.client_display_name
            ),
            "prepared_by": (
                request.prepared_by
            ),
            "exclusions": list(
                request.exclusions
            ),
            "implementation_burdens": (
                serialize_constraint_map(
                    request.implementation_burdens
                )
            ),
            "reversibility_scores": (
                serialize_constraint_map(
                    request.reversibility_scores
                )
            ),
            "owner_roles": (
                serialize_owner_roles(
                    request.owner_roles
                )
            ),
            "maximum_priorities": (
                request.maximum_priorities
            ),
        }

    def _execution_input_payload(
        self,
        *,
        hierarchy_key: str,
        assessment_execution_request_material: dict[str, Any],
        evidence_inputs: tuple[
            CommercialPaidAssessmentEvidenceInputBinding,
            ...,
        ],
    ) -> dict[str, Any]:
        return {
            "hierarchy_key": hierarchy_key,
            "assessment_execution_request_material": (
                assessment_execution_request_material
            ),
            "evidence_inputs": [
                item.to_dict()
                for item in evidence_inputs
            ],
            "schema_version": (
                COMMERCIAL_PAID_ASSESSMENT_EXECUTION_INPUT_BINDING_VERSION
            ),
        }

    def _binding_payload(
        self,
        *,
        hierarchy_key: str,
        assessment_execution_request_hash: str,
        execution_input_hash: str,
        evidence_inputs: tuple[
            CommercialPaidAssessmentEvidenceInputBinding,
            ...,
        ],
    ) -> dict[str, Any]:
        return {
            "hierarchy_key": hierarchy_key,
            "assessment_execution_request_hash": (
                assessment_execution_request_hash
            ),
            "execution_input_hash": (
                execution_input_hash
            ),
            "evidence_commitments": [
                item.commitment_dict()
                for item in evidence_inputs
            ],
            "schema_version": (
                COMMERCIAL_PAID_ASSESSMENT_EXECUTION_INPUT_BINDING_VERSION
            ),
            "boundaries": {
                "binding_is_not_contract_execution": True,
                "binding_is_not_paid_work_authorization": True,
                "binding_is_not_execution_evidence_approval": True,
                "binding_is_not_execution_authority": True,
                "binding_is_not_recovery_authority": True,
                "binding_is_not_delivery_approval": True,
                "binding_does_not_record_delivery": True,
            },
        }

    def _validate_existing(
        self,
        *,
        row: sqlite3.Row,
        expected_request_hash: str,
        expected_execution_input_hash: str,
        expected_request_payload: dict[str, Any],
        expected_request_material: dict[str, Any],
        expected_evidence_inputs: tuple[
            CommercialPaidAssessmentEvidenceInputBinding,
            ...,
        ],
        expected_binding_hash: str,
    ) -> CommercialPaidAssessmentExecutionInputBinding:
        existing = self._binding_from_row(
            row=row,
            reused_existing=True,
        )

        if (
            existing.assessment_execution_request_hash
            != expected_request_hash
        ):
            raise CommercialPaidAssessmentExecutionInputBindingError(
                "immutable execution-input binding already "
                "exists with a different assessment request hash"
            )

        if (
            existing.execution_input_hash
            != expected_execution_input_hash
        ):
            raise CommercialPaidAssessmentExecutionInputBindingError(
                "immutable execution-input binding already "
                "exists with a different execution input hash"
            )

        if (
            canonical_json(
                existing.assessment_execution_request_payload
            )
            != canonical_json(
                expected_request_payload
            )
        ):
            raise CommercialPaidAssessmentExecutionInputBindingError(
                "immutable execution-input binding already "
                "exists with a different request payload"
            )

        if (
            canonical_json(
                existing.assessment_execution_request_material
            )
            != canonical_json(
                expected_request_material
            )
        ):
            raise CommercialPaidAssessmentExecutionInputBindingError(
                "immutable execution-input binding already "
                "exists with different request material"
            )

        if (
            tuple(
                item.to_dict()
                for item in existing.evidence_inputs
            )
            != tuple(
                item.to_dict()
                for item in expected_evidence_inputs
            )
        ):
            raise CommercialPaidAssessmentExecutionInputBindingError(
                "immutable execution-input binding already "
                "exists with different evidence bindings"
            )

        if (
            existing.binding_hash
            != expected_binding_hash
        ):
            raise CommercialPaidAssessmentExecutionInputBindingError(
                "immutable execution-input binding hash mismatch"
            )

        return existing

    def _binding_from_row(
        self,
        *,
        row: sqlite3.Row,
        reused_existing: bool,
    ) -> CommercialPaidAssessmentExecutionInputBinding:
        schema_version = str(
            row[
                "schema_version"
            ]
        )

        if (
            schema_version
            != COMMERCIAL_PAID_ASSESSMENT_EXECUTION_INPUT_BINDING_VERSION
        ):
            raise CommercialPaidAssessmentExecutionInputBindingError(
                "execution-input binding schema version "
                "is not supported"
            )

        try:
            request_payload = json.loads(
                str(
                    row[
                        "assessment_execution_request_payload_json"
                    ]
                )
            )

            request_material = json.loads(
                str(
                    row[
                        "assessment_execution_request_material_json"
                    ]
                )
            )

            evidence_payload = json.loads(
                str(
                    row[
                        "evidence_inputs_json"
                    ]
                )
            )

        except json.JSONDecodeError as exc:
            raise CommercialPaidAssessmentExecutionInputBindingError(
                "execution-input binding contains invalid JSON"
            ) from exc

        if not isinstance(
            request_payload,
            dict,
        ):
            raise CommercialPaidAssessmentExecutionInputBindingError(
                "stored assessment execution request payload "
                "must be an object"
            )

        if not isinstance(
            request_material,
            dict,
        ):
            raise CommercialPaidAssessmentExecutionInputBindingError(
                "stored assessment execution request material "
                "must be an object"
            )

        if not isinstance(
            evidence_payload,
            list,
        ):
            raise CommercialPaidAssessmentExecutionInputBindingError(
                "stored evidence input binding payload "
                "must be a list"
            )

        try:
            evidence_inputs = tuple(
                CommercialPaidAssessmentEvidenceInputBinding(
                    evidence_id=str(
                        item[
                            "evidence_id"
                        ]
                    ),
                    source_id=str(
                        item[
                            "source_id"
                        ]
                    ),
                    source_kind=str(
                        item[
                            "source_kind"
                        ]
                    ),
                    display_name=str(
                        item[
                            "display_name"
                        ]
                    ),
                    source_location=str(
                        item[
                            "source_location"
                        ]
                    ),
                    csv_text=str(
                        item[
                            "csv_text"
                        ]
                    ),
                    content_sha256=str(
                        item[
                            "content_sha256"
                        ]
                    ),
                )
                for item in evidence_payload
            )

        except (
            KeyError,
            TypeError,
        ) as exc:
            raise CommercialPaidAssessmentExecutionInputBindingError(
                "stored evidence input binding payload is invalid"
            ) from exc

        hierarchy_key = str(
            row[
                "hierarchy_key"
            ]
        )

        request_hash = str(
            row[
                "assessment_execution_request_hash"
            ]
        )

        execution_input_hash = str(
            row[
                "execution_input_hash"
            ]
        )

        binding_hash = str(
            row[
                "binding_hash"
            ]
        )

        recomputed_request_hash = sha256_text(
            canonical_json(
                request_payload
            )
        )

        if (
            recomputed_request_hash
            != request_hash
        ):
            raise CommercialPaidAssessmentExecutionInputBindingError(
                "stored assessment execution request hash "
                "does not match its payload"
            )

        recomputed_execution_input_hash = sha256_text(
            canonical_json(
                self._execution_input_payload(
                    hierarchy_key=(
                        hierarchy_key
                    ),
                    assessment_execution_request_material=(
                        request_material
                    ),
                    evidence_inputs=(
                        evidence_inputs
                    ),
                )
            )
        )

        if (
            recomputed_execution_input_hash
            != execution_input_hash
        ):
            raise CommercialPaidAssessmentExecutionInputBindingError(
                "stored execution input hash does not verify"
            )

        expected_binding_hash = sha256_text(
            canonical_json(
                self._binding_payload(
                    hierarchy_key=(
                        hierarchy_key
                    ),
                    assessment_execution_request_hash=(
                        request_hash
                    ),
                    execution_input_hash=(
                        execution_input_hash
                    ),
                    evidence_inputs=(
                        evidence_inputs
                    ),
                )
            )
        )

        if (
            expected_binding_hash
            != binding_hash
        ):
            raise CommercialPaidAssessmentExecutionInputBindingError(
                "stored execution-input binding hash "
                "does not verify"
            )

        return CommercialPaidAssessmentExecutionInputBinding(
            hierarchy_key=(
                hierarchy_key
            ),
            assessment_execution_request_hash=(
                request_hash
            ),
            execution_input_hash=(
                execution_input_hash
            ),
            assessment_execution_request_payload=(
                request_payload
            ),
            assessment_execution_request_material=(
                request_material
            ),
            evidence_inputs=(
                evidence_inputs
            ),
            binding_hash=(
                binding_hash
            ),
            created_at=str(
                row[
                    "created_at"
                ]
            ),
            reused_existing=(
                reused_existing
            ),
            schema_version=(
                schema_version
            ),
        )

    def _initialize_database(
        self,
    ) -> None:
        self.binding_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS
                commercial_paid_assessment_execution_input_bindings (
                    hierarchy_key TEXT PRIMARY KEY,
                    assessment_execution_request_hash TEXT NOT NULL,
                    execution_input_hash TEXT NOT NULL,
                    assessment_execution_request_payload_json TEXT NOT NULL,
                    assessment_execution_request_material_json TEXT NOT NULL,
                    evidence_inputs_json TEXT NOT NULL,
                    binding_hash TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    schema_version TEXT NOT NULL
                )
                """
            )

            columns = {
                str(
                    row[
                        "name"
                    ]
                )
                for row in connection.execute(
                    """
                    PRAGMA table_info(
                        commercial_paid_assessment_execution_input_bindings
                    )
                    """
                ).fetchall()
            }

            if (
                "execution_input_hash"
                not in columns
            ):
                raise CommercialPaidAssessmentExecutionInputBindingError(
                    "existing execution-input binding database "
                    "uses an incompatible pre-1.1 schema"
                )

            if (
                "assessment_execution_request_material_json"
                not in columns
            ):
                raise CommercialPaidAssessmentExecutionInputBindingError(
                    "existing execution-input binding database "
                    "uses an incompatible pre-1.2 schema"
                )

            connection.commit()

    def _connect(
        self,
    ) -> sqlite3.Connection:
        connection = sqlite3.connect(
            self.database_path
        )

        connection.row_factory = (
            sqlite3.Row
        )

        return connection