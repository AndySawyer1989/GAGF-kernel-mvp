from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from backend.app.gagf.governance_intervention_reverification_attempt import (
    GovernanceInterventionReverificationAttemptRecord,
    GovernanceInterventionReverificationAttemptState,
)
from backend.app.gagf.governance_intervention_reverification_work_order import (
    GovernanceInterventionReverificationWorkOrder,
)
from backend.app.gagf.governance_intervention_verification_requirement import (
    GovernanceInterventionVerificationRequirement,
)
from backend.app.gagf.scientific_authority_guard import (
    canonical_json,
    sha256_hex,
)


GOVERNANCE_INTERVENTION_REVERIFICATION_EVIDENCE_ID = (
    "governance-intervention-reverification-evidence"
)

GOVERNANCE_INTERVENTION_REVERIFICATION_EVIDENCE_VERSION = (
    "0.1.0"
)

GOVERNANCE_INTERVENTION_REVERIFICATION_EVIDENCE_SCHEMA_VERSION = (
    "1.0.0"
)


class GovernanceInterventionReverificationEvidenceError(
    ValueError
):
    """Base error for governed reverification evidence."""


class GovernanceInterventionReverificationEvidenceIntegrityError(
    GovernanceInterventionReverificationEvidenceError
):
    """Raised when governed lineage cannot be proven."""


class GovernanceInterventionReverificationEvidenceStateError(
    GovernanceInterventionReverificationEvidenceError
):
    """Raised when evidence is acquired outside an active attempt."""


class GovernanceInterventionReverificationEvidenceValueError(
    GovernanceInterventionReverificationEvidenceError
):
    """Raised when evidence metadata is incomplete or invalid."""


@dataclass(frozen=True, slots=True)
class GovernanceInterventionReverificationEvidence:
    """
    Immutable evidence acquired during one active reverification attempt.

    This artifact proves only that evidence was bound to:
    - one verified I-L work order;
    - one active I-N attempt;
    - one verified structured verification requirement; and
    - one declared evidence source.

    It is not:
    - an I-A outcome observation;
    - a quantitative measurement;
    - a requirement evaluation;
    - a verification disposition;
    - proof of intervention success or failure;
    - proof of causation;
    - authority to mutate verification lifecycle state.
    """

    evidence_id: str
    version: str
    schema_version: str

    tenant_id: str
    intervention_id: str
    verification_record_hash: str

    request_hash: str
    work_order_hash: str
    attempt_id: str
    attempt_execution_id: str
    reverification_scope: str

    requirement_id: str
    requirement_hash: str
    metric_id: str

    source_id: str
    source_kind: str
    acquired_at: str

    evidence_summary: str
    evidence_references: tuple[str, ...]
    record_count: int

    evidence_hash: str

    def payload(self) -> dict[str, Any]:
        return {
            "evidence_id": self.evidence_id,
            "version": self.version,
            "schema_version": self.schema_version,
            "tenant_id": self.tenant_id,
            "intervention_id": self.intervention_id,
            "verification_record_hash": (
                self.verification_record_hash
            ),
            "request_hash": self.request_hash,
            "work_order_hash": self.work_order_hash,
            "attempt_id": self.attempt_id,
            "attempt_execution_id": (
                self.attempt_execution_id
            ),
            "reverification_scope": (
                self.reverification_scope
            ),
            "requirement_id": self.requirement_id,
            "requirement_hash": self.requirement_hash,
            "metric_id": self.metric_id,
            "source_id": self.source_id,
            "source_kind": self.source_kind,
            "acquired_at": self.acquired_at,
            "evidence_summary": self.evidence_summary,
            "evidence_references": list(
                self.evidence_references
            ),
            "record_count": self.record_count,
        }

    def verify(self) -> bool:
        return (
            self.evidence_hash
            == sha256_hex(
                canonical_json(
                    self.payload()
                )
            )
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            **self.payload(),
            "evidence_hash": self.evidence_hash,
        }


class GovernanceInterventionReverificationEvidenceBuilder:
    """
    Builds deterministic evidence acquired during an active I-N attempt.

    Authority ends at evidence acquisition.

    The builder does not:
    - convert evidence into an I-A observation;
    - perform measurement;
    - evaluate a requirement;
    - issue a verification disposition;
    - complete the I-N attempt;
    - supersede a verification record;
    - mutate I-I lifecycle state;
    - authorize intervention activity;
    - infer causation.
    """

    @staticmethod
    def _required(
        value: str,
        field_name: str,
    ) -> str:
        normalized = value.strip()

        if not normalized:
            raise (
                GovernanceInterventionReverificationEvidenceValueError(
                    f"{field_name} is required"
                )
            )

        if normalized != value:
            raise (
                GovernanceInterventionReverificationEvidenceValueError(
                    f"{field_name} must already be canonical"
                )
            )

        return normalized

    @classmethod
    def _normalize_references(
        cls,
        values: Iterable[str],
    ) -> tuple[str, ...]:
        normalized = tuple(
            cls._required(
                value,
                "evidence_references",
            )
            for value in values
        )

        if not normalized:
            raise (
                GovernanceInterventionReverificationEvidenceValueError(
                    "at least one evidence reference is required"
                )
            )

        if len(normalized) != len(set(normalized)):
            raise (
                GovernanceInterventionReverificationEvidenceValueError(
                    "evidence_references must not contain duplicates"
                )
            )

        return normalized

    @classmethod
    def build(
        cls,
        *,
        work_order: (
            GovernanceInterventionReverificationWorkOrder
        ),
        attempt: (
            GovernanceInterventionReverificationAttemptRecord
        ),
        requirement: (
            GovernanceInterventionVerificationRequirement
        ),
        source_id: str,
        source_kind: str,
        acquired_at: str,
        evidence_summary: str,
        evidence_references: Iterable[str],
        record_count: int,
    ) -> GovernanceInterventionReverificationEvidence:
        cls._validate_lineage(
            work_order=work_order,
            attempt=attempt,
            requirement=requirement,
        )

        normalized_source_id = cls._required(
            source_id,
            "source_id",
        )

        normalized_source_kind = cls._required(
            source_kind,
            "source_kind",
        )

        normalized_acquired_at = cls._required(
            acquired_at,
            "acquired_at",
        )

        normalized_summary = cls._required(
            evidence_summary,
            "evidence_summary",
        )

        normalized_references = (
            cls._normalize_references(
                evidence_references
            )
        )

        if record_count < 1:
            raise (
                GovernanceInterventionReverificationEvidenceValueError(
                    "record_count must be at least 1"
                )
            )

        payload: dict[str, Any] = {
            "evidence_id": (
                GOVERNANCE_INTERVENTION_REVERIFICATION_EVIDENCE_ID
            ),
            "version": (
                GOVERNANCE_INTERVENTION_REVERIFICATION_EVIDENCE_VERSION
            ),
            "schema_version": (
                GOVERNANCE_INTERVENTION_REVERIFICATION_EVIDENCE_SCHEMA_VERSION
            ),
            "tenant_id": work_order.tenant_id,
            "intervention_id": (
                work_order.intervention_id
            ),
            "verification_record_hash": (
                work_order.verification_record_hash
            ),
            "request_hash": work_order.request_hash,
            "work_order_hash": (
                work_order.work_order_hash
            ),
            "attempt_id": work_order.attempt_id,
            "attempt_execution_id": (
                attempt.attempt_execution_id
            ),
            "reverification_scope": (
                work_order.reverification_scope
            ),
            "requirement_id": (
                requirement.requirement_id
            ),
            "requirement_hash": (
                requirement.requirement_hash
            ),
            "metric_id": requirement.metric_id,
            "source_id": normalized_source_id,
            "source_kind": normalized_source_kind,
            "acquired_at": normalized_acquired_at,
            "evidence_summary": normalized_summary,
            "evidence_references": list(
                normalized_references
            ),
            "record_count": record_count,
        }

        return GovernanceInterventionReverificationEvidence(
            evidence_id=payload["evidence_id"],
            version=payload["version"],
            schema_version=payload[
                "schema_version"
            ],
            tenant_id=payload["tenant_id"],
            intervention_id=payload[
                "intervention_id"
            ],
            verification_record_hash=payload[
                "verification_record_hash"
            ],
            request_hash=payload["request_hash"],
            work_order_hash=payload[
                "work_order_hash"
            ],
            attempt_id=payload["attempt_id"],
            attempt_execution_id=payload[
                "attempt_execution_id"
            ],
            reverification_scope=payload[
                "reverification_scope"
            ],
            requirement_id=payload[
                "requirement_id"
            ],
            requirement_hash=payload[
                "requirement_hash"
            ],
            metric_id=payload["metric_id"],
            source_id=payload["source_id"],
            source_kind=payload["source_kind"],
            acquired_at=payload["acquired_at"],
            evidence_summary=payload[
                "evidence_summary"
            ],
            evidence_references=tuple(
                payload["evidence_references"]
            ),
            record_count=payload["record_count"],
            evidence_hash=sha256_hex(
                canonical_json(payload)
            ),
        )

    @staticmethod
    def _validate_lineage(
        *,
        work_order: (
            GovernanceInterventionReverificationWorkOrder
        ),
        attempt: (
            GovernanceInterventionReverificationAttemptRecord
        ),
        requirement: (
            GovernanceInterventionVerificationRequirement
        ),
    ) -> None:
        if not work_order.verify():
            raise (
                GovernanceInterventionReverificationEvidenceIntegrityError(
                    "reverification work order failed "
                    "deterministic verification"
                )
            )

        if not requirement.verify():
            raise (
                GovernanceInterventionReverificationEvidenceIntegrityError(
                    "verification requirement failed "
                    "deterministic verification"
                )
            )

        if (
            attempt.current_state
            is not GovernanceInterventionReverificationAttemptState.STARTED
        ):
            raise (
                GovernanceInterventionReverificationEvidenceStateError(
                    "reverification evidence requires an "
                    "active STARTED attempt"
                )
            )

        expected_attempt = (
            work_order.tenant_id,
            work_order.intervention_id,
            work_order.verification_record_hash,
            work_order.request_hash,
            work_order.work_order_hash,
            work_order.attempt_id,
            work_order.reverification_scope,
        )

        actual_attempt = (
            attempt.tenant_id,
            attempt.intervention_id,
            attempt.verification_record_hash,
            attempt.request_hash,
            attempt.work_order_hash,
            attempt.attempt_id,
            attempt.reverification_scope,
        )

        if actual_attempt != expected_attempt:
            raise (
                GovernanceInterventionReverificationEvidenceIntegrityError(
                    "reverification attempt does not match "
                    "I-L work-order lineage"
                )
            )

        if (
            requirement.tenant_id
            != work_order.tenant_id
        ):
            raise (
                GovernanceInterventionReverificationEvidenceIntegrityError(
                    "verification requirement tenant does "
                    "not match work order"
                )
            )

        if (
            requirement.intervention_id
            != work_order.intervention_id
        ):
            raise (
                GovernanceInterventionReverificationEvidenceIntegrityError(
                    "verification requirement intervention_id "
                    "does not match work order"
                )
            )