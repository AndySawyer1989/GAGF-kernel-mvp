from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from backend.app.gagf.governance_intervention_verification_freshness import (
    GovernanceInterventionVerificationFreshnessDisposition,
    GovernanceInterventionVerificationFreshnessEvaluation,
)
from backend.app.gagf.governance_intervention_verification_lifecycle import (
    GovernanceInterventionVerificationLifecycleEntry,
    GovernanceInterventionVerificationLifecycleError,
    GovernanceInterventionVerificationLifecycleLedger,
    GovernanceInterventionVerificationLifecycleStatus,
)
from backend.app.gagf.scientific_authority_guard import (
    canonical_json,
    sha256_hex,
)


GOVERNANCE_INTERVENTION_VERIFICATION_FRESHNESS_TRANSITION_ID = (
    "governance-intervention-verification-freshness-transition"
)

GOVERNANCE_INTERVENTION_VERIFICATION_FRESHNESS_TRANSITION_VERSION = (
    "0.1.0"
)

GOVERNANCE_INTERVENTION_VERIFICATION_FRESHNESS_TRANSITION_SCHEMA_VERSION = (
    "1.0.0"
)


class GovernanceInterventionVerificationFreshnessTransitionError(
    RuntimeError
):
    """Base error for governed freshness-to-lifecycle transitions."""


class GovernanceInterventionVerificationFreshnessTransitionIntegrityError(
    GovernanceInterventionVerificationFreshnessTransitionError
):
    """Raised when a freshness evaluation fails deterministic integrity."""


class GovernanceInterventionVerificationFreshnessTransitionStateError(
    GovernanceInterventionVerificationFreshnessTransitionError
):
    """Raised when a freshness proposal is incompatible with lifecycle state."""


@dataclass(frozen=True, slots=True)
class GovernanceInterventionVerificationFreshnessTransitionResult:
    """
    Governed result of applying one I-J freshness evaluation.

    applied=False means the evaluation required no lifecycle mutation.
    This result does not perform or claim reverification.
    """

    transition_id: str
    version: str
    schema_version: str

    tenant_id: str
    intervention_id: str
    verification_record_hash: str

    freshness_evaluation_hash: str
    freshness_disposition: str

    prior_lifecycle_status: str | None
    proposed_lifecycle_status: str | None
    resulting_lifecycle_status: str | None

    applied: bool
    lifecycle_event_hash: str | None

    transition_result_hash: str

    def payload(self) -> dict[str, Any]:
        return {
            "transition_id": self.transition_id,
            "version": self.version,
            "schema_version": self.schema_version,
            "tenant_id": self.tenant_id,
            "intervention_id": self.intervention_id,
            "verification_record_hash": (
                self.verification_record_hash
            ),
            "freshness_evaluation_hash": (
                self.freshness_evaluation_hash
            ),
            "freshness_disposition": (
                self.freshness_disposition
            ),
            "prior_lifecycle_status": (
                self.prior_lifecycle_status
            ),
            "proposed_lifecycle_status": (
                self.proposed_lifecycle_status
            ),
            "resulting_lifecycle_status": (
                self.resulting_lifecycle_status
            ),
            "applied": self.applied,
            "lifecycle_event_hash": (
                self.lifecycle_event_hash
            ),
        }

    def verify(self) -> bool:
        return (
            self.transition_result_hash
            == sha256_hex(
                canonical_json(self.payload())
            )
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            **self.payload(),
            "transition_result_hash": (
                self.transition_result_hash
            ),
        }


class GovernanceInterventionVerificationFreshnessTransitionService:
    """
    Governed bridge between I-J freshness evaluation and I-I lifecycle state.

    This service:
    - requires a deterministically valid freshness evaluation;
    - checks the current I-I lifecycle state;
    - applies only the lifecycle state proposed by I-J;
    - never selects SUPERSEDED;
    - never performs reverification;
    - never executes or authorizes interventions;
    - never infers causation.
    """

    def __init__(
        self,
        *,
        database_path: str | Path,
    ) -> None:
        self._lifecycle = (
            GovernanceInterventionVerificationLifecycleLedger(
                database_path=database_path
            )
        )

    def apply(
        self,
        *,
        evaluation: GovernanceInterventionVerificationFreshnessEvaluation,
    ) -> GovernanceInterventionVerificationFreshnessTransitionResult:
        if not evaluation.verify():
            raise (
                GovernanceInterventionVerificationFreshnessTransitionIntegrityError(
                    "freshness evaluation failed deterministic verification"
                )
            )

        current = self._lifecycle.get_current_state(
            tenant_id=evaluation.tenant_id,
            verification_record_hash=(
                evaluation.verification_record_hash
            ),
        )

        prior_status = (
            None
            if current is None
            else current.lifecycle_status
        )

        disposition = (
            GovernanceInterventionVerificationFreshnessDisposition(
                evaluation.freshness_disposition
            )
        )

        if disposition == (
            GovernanceInterventionVerificationFreshnessDisposition.FRESH
        ):
            if evaluation.proposed_lifecycle_status is not None:
                raise (
                    GovernanceInterventionVerificationFreshnessTransitionIntegrityError(
                        "FRESH evaluation must not propose lifecycle mutation"
                    )
                )

            return self._build_result(
                evaluation=evaluation,
                prior_status=prior_status,
                resulting_status=prior_status,
                applied=False,
                lifecycle_entry=None,
            )

        if current is None:
            raise (
                GovernanceInterventionVerificationFreshnessTransitionStateError(
                    "freshness lifecycle transition requires an existing "
                    "ACTIVE lifecycle state"
                )
            )

        if (
            current.lifecycle_status
            == GovernanceInterventionVerificationLifecycleStatus.SUPERSEDED.value
        ):
            raise (
                GovernanceInterventionVerificationFreshnessTransitionStateError(
                    "freshness evaluation cannot transition a "
                    "SUPERSEDED verification record"
                )
            )

        lifecycle_entry: (
            GovernanceInterventionVerificationLifecycleEntry
            | None
        )

        if disposition == (
            GovernanceInterventionVerificationFreshnessDisposition.STALE
        ):
            if (
                evaluation.proposed_lifecycle_status
                != GovernanceInterventionVerificationLifecycleStatus.STALE.value
            ):
                raise (
                    GovernanceInterventionVerificationFreshnessTransitionIntegrityError(
                        "STALE freshness evaluation must propose STALE"
                    )
                )

            if (
                current.lifecycle_status
                == GovernanceInterventionVerificationLifecycleStatus.STALE.value
            ):
                return self._build_result(
                    evaluation=evaluation,
                    prior_status=prior_status,
                    resulting_status=prior_status,
                    applied=False,
                    lifecycle_entry=None,
                )

            if (
                current.lifecycle_status
                == GovernanceInterventionVerificationLifecycleStatus
                .REVERIFICATION_REQUIRED.value
            ):
                return self._build_result(
                    evaluation=evaluation,
                    prior_status=prior_status,
                    resulting_status=prior_status,
                    applied=False,
                    lifecycle_entry=None,
                )

            try:
                lifecycle_entry = self._lifecycle.mark_stale(
                    tenant_id=evaluation.tenant_id,
                    verification_record_hash=(
                        evaluation.verification_record_hash
                    ),
                )
            except GovernanceInterventionVerificationLifecycleError as exc:
                raise (
                    GovernanceInterventionVerificationFreshnessTransitionStateError(
                        "I-I rejected freshness STALE transition"
                    )
                ) from exc

        elif disposition == (
            GovernanceInterventionVerificationFreshnessDisposition
            .REVERIFICATION_REQUIRED
        ):
            if (
                evaluation.proposed_lifecycle_status
                != GovernanceInterventionVerificationLifecycleStatus
                .REVERIFICATION_REQUIRED.value
            ):
                raise (
                    GovernanceInterventionVerificationFreshnessTransitionIntegrityError(
                        "REVERIFICATION_REQUIRED evaluation must propose "
                        "REVERIFICATION_REQUIRED"
                    )
                )

            if (
                current.lifecycle_status
                == GovernanceInterventionVerificationLifecycleStatus
                .REVERIFICATION_REQUIRED.value
            ):
                return self._build_result(
                    evaluation=evaluation,
                    prior_status=prior_status,
                    resulting_status=prior_status,
                    applied=False,
                    lifecycle_entry=None,
                )

            try:
                lifecycle_entry = (
                    self._lifecycle.require_reverification(
                        tenant_id=evaluation.tenant_id,
                        verification_record_hash=(
                            evaluation.verification_record_hash
                        ),
                    )
                )
            except GovernanceInterventionVerificationLifecycleError as exc:
                raise (
                    GovernanceInterventionVerificationFreshnessTransitionStateError(
                        "I-I rejected freshness reverification transition"
                    )
                ) from exc

        else:
            raise (
                GovernanceInterventionVerificationFreshnessTransitionIntegrityError(
                    "unsupported freshness disposition"
                )
            )

        resulting = self._lifecycle.get_current_state(
            tenant_id=evaluation.tenant_id,
            verification_record_hash=(
                evaluation.verification_record_hash
            ),
        )

        if resulting is None:
            raise (
                GovernanceInterventionVerificationFreshnessTransitionIntegrityError(
                    "lifecycle transition completed without resulting state"
                )
            )

        return self._build_result(
            evaluation=evaluation,
            prior_status=prior_status,
            resulting_status=resulting.lifecycle_status,
            applied=True,
            lifecycle_entry=lifecycle_entry,
        )

    @staticmethod
    def _build_result(
        *,
        evaluation: GovernanceInterventionVerificationFreshnessEvaluation,
        prior_status: str | None,
        resulting_status: str | None,
        applied: bool,
        lifecycle_entry: (
            GovernanceInterventionVerificationLifecycleEntry
            | None
        ),
    ) -> GovernanceInterventionVerificationFreshnessTransitionResult:
        payload: dict[str, Any] = {
            "transition_id": (
                GOVERNANCE_INTERVENTION_VERIFICATION_FRESHNESS_TRANSITION_ID
            ),
            "version": (
                GOVERNANCE_INTERVENTION_VERIFICATION_FRESHNESS_TRANSITION_VERSION
            ),
            "schema_version": (
                GOVERNANCE_INTERVENTION_VERIFICATION_FRESHNESS_TRANSITION_SCHEMA_VERSION
            ),
            "tenant_id": evaluation.tenant_id,
            "intervention_id": evaluation.intervention_id,
            "verification_record_hash": (
                evaluation.verification_record_hash
            ),
            "freshness_evaluation_hash": (
                evaluation.freshness_evaluation_hash
            ),
            "freshness_disposition": (
                evaluation.freshness_disposition
            ),
            "prior_lifecycle_status": (
                prior_status
            ),
            "proposed_lifecycle_status": (
                evaluation.proposed_lifecycle_status
            ),
            "resulting_lifecycle_status": (
                resulting_status
            ),
            "applied": applied,
            "lifecycle_event_hash": (
                None
                if lifecycle_entry is None
                else lifecycle_entry.lifecycle_event_hash
            ),
        }

        return (
            GovernanceInterventionVerificationFreshnessTransitionResult(
                **payload,
                transition_result_hash=sha256_hex(
                    canonical_json(payload)
                ),
            )
        )