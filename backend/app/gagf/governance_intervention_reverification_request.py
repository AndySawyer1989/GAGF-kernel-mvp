from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from backend.app.gagf.governance_intervention_verification_freshness import (
    GovernanceInterventionVerificationFreshnessDisposition,
    GovernanceInterventionVerificationFreshnessEvaluation,
)
from backend.app.gagf.governance_intervention_verification_lifecycle import (
    GovernanceInterventionVerificationLifecycleState,
    GovernanceInterventionVerificationLifecycleStatus,
)
from backend.app.gagf.governance_intervention_verification_ledger import (
    GovernanceInterventionVerificationRecord,
)
from backend.app.gagf.scientific_authority_guard import (
    canonical_json,
    sha256_hex,
)


GOVERNANCE_INTERVENTION_REVERIFICATION_REQUEST_ID = (
    "governance-intervention-reverification-request"
)

GOVERNANCE_INTERVENTION_REVERIFICATION_REQUEST_VERSION = (
    "0.1.0"
)

GOVERNANCE_INTERVENTION_REVERIFICATION_REQUEST_SCHEMA_VERSION = (
    "1.0.0"
)


class GovernanceInterventionReverificationRequestError(
    ValueError
):
    """Base error for governed reverification request construction."""


class GovernanceInterventionReverificationRequestIntegrityError(
    GovernanceInterventionReverificationRequestError
):
    """Raised when request inputs fail deterministic integrity checks."""


class GovernanceInterventionReverificationScope(
    str,
    Enum,
):
    FULL = "FULL"
    REQUIREMENTS = "REQUIREMENTS"
    OBSERVATIONS = "OBSERVATIONS"
    POLICY = "POLICY"
    CONTRACT = "CONTRACT"


@dataclass(frozen=True, slots=True)
class GovernanceInterventionReverificationRequest:
    """
    Immutable request for future reverification work.

    This artifact records that reverification is required and defines the
    requested scope. It does not perform reverification, authorize execution,
    alter historical verification, infer causation, or select future action.
    """

    request_id: str
    version: str
    schema_version: str

    tenant_id: str
    intervention_id: str
    verification_record_hash: str

    lifecycle_event_hash: str
    freshness_evaluation_hash: str

    reverification_scope: str
    trigger_codes: tuple[str, ...]

    request_hash: str

    def payload(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "version": self.version,
            "schema_version": self.schema_version,
            "tenant_id": self.tenant_id,
            "intervention_id": self.intervention_id,
            "verification_record_hash": (
                self.verification_record_hash
            ),
            "lifecycle_event_hash": (
                self.lifecycle_event_hash
            ),
            "freshness_evaluation_hash": (
                self.freshness_evaluation_hash
            ),
            "reverification_scope": (
                self.reverification_scope
            ),
            "trigger_codes": list(
                self.trigger_codes
            ),
        }

    def verify(self) -> bool:
        return (
            self.request_hash
            == sha256_hex(
                canonical_json(
                    self.payload()
                )
            )
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            **self.payload(),
            "request_hash": self.request_hash,
        }


class GovernanceInterventionReverificationRequestBuilder:
    """
    Deterministically builds a governed reverification request.

    Preconditions:
    - immutable I-G verification record is valid;
    - I-J freshness evaluation is valid and requires reverification;
    - I-I lifecycle state is REVERIFICATION_REQUIRED;
    - all three artifacts bind to the same tenant/intervention/record.

    The builder has no execution or lifecycle mutation authority.
    """

    @classmethod
    def build(
        cls,
        *,
        record: GovernanceInterventionVerificationRecord,
        freshness_evaluation: (
            GovernanceInterventionVerificationFreshnessEvaluation
        ),
        lifecycle_state: (
            GovernanceInterventionVerificationLifecycleState
        ),
    ) -> GovernanceInterventionReverificationRequest:
        cls._validate_inputs(
            record=record,
            freshness_evaluation=freshness_evaluation,
            lifecycle_state=lifecycle_state,
        )

        scope = cls._derive_scope(
            trigger_codes=(
                freshness_evaluation.trigger_codes
            )
        )

        payload: dict[str, Any] = {
            "request_id": (
                GOVERNANCE_INTERVENTION_REVERIFICATION_REQUEST_ID
            ),
            "version": (
                GOVERNANCE_INTERVENTION_REVERIFICATION_REQUEST_VERSION
            ),
            "schema_version": (
                GOVERNANCE_INTERVENTION_REVERIFICATION_REQUEST_SCHEMA_VERSION
            ),
            "tenant_id": record.tenant_id,
            "intervention_id": record.intervention_id,
            "verification_record_hash": (
                record.record_hash
            ),
            "lifecycle_event_hash": (
                lifecycle_state.lifecycle_event_hash
            ),
            "freshness_evaluation_hash": (
                freshness_evaluation.freshness_evaluation_hash
            ),
            "reverification_scope": scope.value,
            "trigger_codes": list(
                freshness_evaluation.trigger_codes
            ),
        }

        return GovernanceInterventionReverificationRequest(
            request_id=payload["request_id"],
            version=payload["version"],
            schema_version=payload["schema_version"],
            tenant_id=payload["tenant_id"],
            intervention_id=payload["intervention_id"],
            verification_record_hash=payload[
                "verification_record_hash"
            ],
            lifecycle_event_hash=payload[
                "lifecycle_event_hash"
            ],
            freshness_evaluation_hash=payload[
                "freshness_evaluation_hash"
            ],
            reverification_scope=payload[
                "reverification_scope"
            ],
            trigger_codes=tuple(
                payload["trigger_codes"]
            ),
            request_hash=sha256_hex(
                canonical_json(payload)
            ),
        )

    @staticmethod
    def _validate_inputs(
        *,
        record: GovernanceInterventionVerificationRecord,
        freshness_evaluation: (
            GovernanceInterventionVerificationFreshnessEvaluation
        ),
        lifecycle_state: (
            GovernanceInterventionVerificationLifecycleState
        ),
    ) -> None:
        if not record.verify():
            raise (
                GovernanceInterventionReverificationRequestIntegrityError(
                    "verification record failed deterministic verification"
                )
            )

        if not freshness_evaluation.verify():
            raise (
                GovernanceInterventionReverificationRequestIntegrityError(
                    "freshness evaluation failed deterministic verification"
                )
            )

        if (
            freshness_evaluation.freshness_disposition
            != GovernanceInterventionVerificationFreshnessDisposition
            .REVERIFICATION_REQUIRED.value
        ):
            raise GovernanceInterventionReverificationRequestError(
                "freshness evaluation does not require reverification"
            )

        if (
            freshness_evaluation.proposed_lifecycle_status
            != GovernanceInterventionVerificationLifecycleStatus
            .REVERIFICATION_REQUIRED.value
        ):
            raise (
                GovernanceInterventionReverificationRequestIntegrityError(
                    "freshness evaluation does not propose "
                    "REVERIFICATION_REQUIRED"
                )
            )

        if (
            lifecycle_state.lifecycle_status
            != GovernanceInterventionVerificationLifecycleStatus
            .REVERIFICATION_REQUIRED.value
        ):
            raise GovernanceInterventionReverificationRequestError(
                "lifecycle state is not REVERIFICATION_REQUIRED"
            )

        bindings = (
            (
                freshness_evaluation.tenant_id,
                record.tenant_id,
                "freshness tenant",
            ),
            (
                lifecycle_state.tenant_id,
                record.tenant_id,
                "lifecycle tenant",
            ),
            (
                freshness_evaluation.intervention_id,
                record.intervention_id,
                "freshness intervention",
            ),
            (
                lifecycle_state.intervention_id,
                record.intervention_id,
                "lifecycle intervention",
            ),
            (
                freshness_evaluation.verification_record_hash,
                record.record_hash,
                "freshness verification record",
            ),
            (
                lifecycle_state.verification_record_hash,
                record.record_hash,
                "lifecycle verification record",
            ),
        )

        for actual, expected, label in bindings:
            if actual != expected:
                raise (
                    GovernanceInterventionReverificationRequestIntegrityError(
                        f"{label} binding does not match verification record"
                    )
                )

        if not lifecycle_state.lifecycle_event_hash.strip():
            raise (
                GovernanceInterventionReverificationRequestIntegrityError(
                    "lifecycle event hash is required"
                )
            )

        if not freshness_evaluation.trigger_codes:
            raise (
                GovernanceInterventionReverificationRequestIntegrityError(
                    "reverification request requires at least one trigger"
                )
            )

    @staticmethod
    def _derive_scope(
        *,
        trigger_codes: tuple[str, ...],
    ) -> GovernanceInterventionReverificationScope:
        trigger_set = set(
            trigger_codes
        )

        if (
            "CONTRACT_CHANGED" in trigger_set
        ):
            return GovernanceInterventionReverificationScope.FULL

        if (
            "REQUIREMENTS_CHANGED" in trigger_set
        ):
            return GovernanceInterventionReverificationScope.REQUIREMENTS

        if (
            "REQUIRED_OBSERVATION_INVALIDATED"
            in trigger_set
        ):
            return GovernanceInterventionReverificationScope.OBSERVATIONS

        if (
            "POLICY_CHANGED" in trigger_set
        ):
            return GovernanceInterventionReverificationScope.POLICY

        raise GovernanceInterventionReverificationRequestIntegrityError(
            "no supported reverification trigger was present"
        )