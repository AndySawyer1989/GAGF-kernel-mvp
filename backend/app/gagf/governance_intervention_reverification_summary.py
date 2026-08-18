from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from backend.app.gagf.governance_intervention_reverification_verification_set import (
    GovernanceInterventionReverificationVerificationSet,
)
from backend.app.gagf.scientific_authority_guard import (
    canonical_json,
    sha256_hex,
)


GOVERNANCE_INTERVENTION_REVERIFICATION_SUMMARY_ID = (
    "governance-intervention-reverification-summary"
)

GOVERNANCE_INTERVENTION_REVERIFICATION_SUMMARY_VERSION = (
    "0.1.0"
)

GOVERNANCE_INTERVENTION_REVERIFICATION_SUMMARY_SCHEMA_VERSION = (
    "1.0.0"
)


class GovernanceInterventionReverificationSummaryDisposition(
    str,
    Enum,
):
    VERIFIED = "VERIFIED"
    NOT_VERIFIED = "NOT_VERIFIED"
    INCONCLUSIVE = "INCONCLUSIVE"


class GovernanceInterventionReverificationSummaryError(
    ValueError
):
    """Base error for governed reverification summaries."""


class GovernanceInterventionReverificationSummaryIntegrityError(
    GovernanceInterventionReverificationSummaryError
):
    """Raised when the supplied reverification set is invalid."""


class GovernanceInterventionReverificationSummaryDispositionError(
    GovernanceInterventionReverificationSummaryError
):
    """Raised when a set contains an unsupported governed disposition."""


@dataclass(frozen=True, slots=True)
class GovernanceInterventionReverificationSummary:
    """
    Immutable intervention-level reverification summary derived from one
    complete and verified I-S reverification verification set.

    Aggregation precedence:

    NOT_VERIFIED > INCONCLUSIVE > VERIFIED

    Meaning:
    - VERIFIED:
      every governed reverification obligation is VERIFIED.
    - NOT_VERIFIED:
      at least one governed reverification obligation is NOT_VERIFIED.
    - INCONCLUSIVE:
      none are NOT_VERIFIED and at least one is INCONCLUSIVE.

    This artifact does not:
    - determine intervention success or failure;
    - establish causal attribution;
    - complete the reverification attempt;
    - supersede a verification record;
    - mutate verification lifecycle state;
    - authorize future intervention activity;
    - order rollback, continuation, or remediation;
    - recommend policy changes.
    """

    verification_summary_id: str
    version: str
    schema_version: str

    tenant_id: str
    actuation_contract_hash: str
    intervention_id: str
    intervention_type: str

    verification_record_hash: str
    request_hash: str
    work_order_hash: str
    attempt_id: str
    attempt_execution_id: str
    reverification_scope: str

    verification_set_hash: str

    required_count: int
    verified_count: int
    not_verified_count: int
    inconclusive_count: int

    verification_disposition: (
        GovernanceInterventionReverificationSummaryDisposition
    )

    verification_summary_hash: str

    def payload(self) -> dict[str, Any]:
        return {
            "verification_summary_id": (
                self.verification_summary_id
            ),
            "version": self.version,
            "schema_version": self.schema_version,
            "tenant_id": self.tenant_id,
            "actuation_contract_hash": (
                self.actuation_contract_hash
            ),
            "intervention_id": self.intervention_id,
            "intervention_type": self.intervention_type,
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
            "verification_set_hash": (
                self.verification_set_hash
            ),
            "required_count": self.required_count,
            "verified_count": self.verified_count,
            "not_verified_count": (
                self.not_verified_count
            ),
            "inconclusive_count": (
                self.inconclusive_count
            ),
            "verification_disposition": (
                self.verification_disposition.value
            ),
        }

    def verify(self) -> bool:
        return (
            self.verification_summary_hash
            == sha256_hex(
                canonical_json(
                    self.payload()
                )
            )
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            **self.payload(),
            "verification_summary_hash": (
                self.verification_summary_hash
            ),
        }


class GovernanceInterventionReverificationSummaryBuilder:
    """
    Deterministically aggregates one complete governed I-S reverification
    verification set.

    The builder performs no measurement, evaluation, causal attribution,
    execution, lifecycle mutation, supersession, authorization, rollback,
    continuation, remediation, or policy recommendation.
    """

    @classmethod
    def build(
        cls,
        *,
        verification_set: (
            GovernanceInterventionReverificationVerificationSet
        ),
    ) -> GovernanceInterventionReverificationSummary:
        if not verification_set.verify():
            raise (
                GovernanceInterventionReverificationSummaryIntegrityError(
                    "reverification verification set failed "
                    "deterministic verification"
                )
            )

        if verification_set.required_count < 1:
            raise (
                GovernanceInterventionReverificationSummaryIntegrityError(
                    "reverification verification set must contain "
                    "at least one requirement"
                )
            )

        if (
            verification_set.result_count
            != verification_set.required_count
        ):
            raise (
                GovernanceInterventionReverificationSummaryIntegrityError(
                    "reverification verification set result_count "
                    "does not match required_count"
                )
            )

        if (
            len(verification_set.entries)
            != verification_set.required_count
        ):
            raise (
                GovernanceInterventionReverificationSummaryIntegrityError(
                    "reverification verification set entry count "
                    "does not match required_count"
                )
            )

        verified_count = 0
        not_verified_count = 0
        inconclusive_count = 0

        for entry in verification_set.entries:
            disposition = entry.verification_disposition

            if disposition == "VERIFIED":
                verified_count += 1
                continue

            if disposition == "NOT_VERIFIED":
                not_verified_count += 1
                continue

            if disposition == "INCONCLUSIVE":
                inconclusive_count += 1
                continue

            raise (
                GovernanceInterventionReverificationSummaryDispositionError(
                    "unsupported requirement-level "
                    "reverification verification disposition"
                )
            )

        cls._validate_counts(
            required_count=verification_set.required_count,
            verified_count=verified_count,
            not_verified_count=not_verified_count,
            inconclusive_count=inconclusive_count,
        )

        verification_disposition = cls._aggregate(
            verified_count=verified_count,
            not_verified_count=not_verified_count,
            inconclusive_count=inconclusive_count,
        )

        payload: dict[str, Any] = {
            "verification_summary_id": (
                GOVERNANCE_INTERVENTION_REVERIFICATION_SUMMARY_ID
            ),
            "version": (
                GOVERNANCE_INTERVENTION_REVERIFICATION_SUMMARY_VERSION
            ),
            "schema_version": (
                GOVERNANCE_INTERVENTION_REVERIFICATION_SUMMARY_SCHEMA_VERSION
            ),
            "tenant_id": verification_set.tenant_id,
            "actuation_contract_hash": (
                verification_set.actuation_contract_hash
            ),
            "intervention_id": (
                verification_set.intervention_id
            ),
            "intervention_type": (
                verification_set.intervention_type
            ),
            "verification_record_hash": (
                verification_set.verification_record_hash
            ),
            "request_hash": (
                verification_set.request_hash
            ),
            "work_order_hash": (
                verification_set.work_order_hash
            ),
            "attempt_id": (
                verification_set.attempt_id
            ),
            "attempt_execution_id": (
                verification_set.attempt_execution_id
            ),
            "reverification_scope": (
                verification_set.reverification_scope
            ),
            "verification_set_hash": (
                verification_set.verification_set_hash
            ),
            "required_count": (
                verification_set.required_count
            ),
            "verified_count": verified_count,
            "not_verified_count": (
                not_verified_count
            ),
            "inconclusive_count": (
                inconclusive_count
            ),
            "verification_disposition": (
                verification_disposition.value
            ),
        }

        return (
            GovernanceInterventionReverificationSummary(
                verification_summary_id=payload[
                    "verification_summary_id"
                ],
                version=payload["version"],
                schema_version=payload[
                    "schema_version"
                ],
                tenant_id=payload[
                    "tenant_id"
                ],
                actuation_contract_hash=payload[
                    "actuation_contract_hash"
                ],
                intervention_id=payload[
                    "intervention_id"
                ],
                intervention_type=payload[
                    "intervention_type"
                ],
                verification_record_hash=payload[
                    "verification_record_hash"
                ],
                request_hash=payload[
                    "request_hash"
                ],
                work_order_hash=payload[
                    "work_order_hash"
                ],
                attempt_id=payload[
                    "attempt_id"
                ],
                attempt_execution_id=payload[
                    "attempt_execution_id"
                ],
                reverification_scope=payload[
                    "reverification_scope"
                ],
                verification_set_hash=payload[
                    "verification_set_hash"
                ],
                required_count=payload[
                    "required_count"
                ],
                verified_count=payload[
                    "verified_count"
                ],
                not_verified_count=payload[
                    "not_verified_count"
                ],
                inconclusive_count=payload[
                    "inconclusive_count"
                ],
                verification_disposition=(
                    verification_disposition
                ),
                verification_summary_hash=sha256_hex(
                    canonical_json(payload)
                ),
            )
        )

    @staticmethod
    def _validate_counts(
        *,
        required_count: int,
        verified_count: int,
        not_verified_count: int,
        inconclusive_count: int,
    ) -> None:
        if (
            verified_count
            + not_verified_count
            + inconclusive_count
            != required_count
        ):
            raise (
                GovernanceInterventionReverificationSummaryIntegrityError(
                    "reverification verification disposition counts "
                    "do not equal required_count"
                )
            )

    @staticmethod
    def _aggregate(
        *,
        verified_count: int,
        not_verified_count: int,
        inconclusive_count: int,
    ) -> (
        GovernanceInterventionReverificationSummaryDisposition
    ):
        if not_verified_count > 0:
            return (
                GovernanceInterventionReverificationSummaryDisposition
                .NOT_VERIFIED
            )

        if inconclusive_count > 0:
            return (
                GovernanceInterventionReverificationSummaryDisposition
                .INCONCLUSIVE
            )

        if verified_count > 0:
            return (
                GovernanceInterventionReverificationSummaryDisposition
                .VERIFIED
            )

        raise (
            GovernanceInterventionReverificationSummaryIntegrityError(
                "reverification verification set produced "
                "no governed dispositions"
            )
        )