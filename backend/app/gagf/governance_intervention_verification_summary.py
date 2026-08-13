from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from backend.app.gagf.governance_intervention_verification_set import (
    GovernanceInterventionVerificationSet,
)
from backend.app.gagf.scientific_authority_guard import (
    canonical_json,
    sha256_hex,
)


GOVERNANCE_INTERVENTION_VERIFICATION_SUMMARY_ID = (
    "governance-intervention-verification-summary"
)
GOVERNANCE_INTERVENTION_VERIFICATION_SUMMARY_VERSION = "0.1.0"
GOVERNANCE_INTERVENTION_VERIFICATION_SUMMARY_SCHEMA_VERSION = "1.0.0"


class GovernanceInterventionVerificationSummaryDisposition(
    str,
    Enum,
):
    VERIFIED = "VERIFIED"
    NOT_VERIFIED = "NOT_VERIFIED"
    INCONCLUSIVE = "INCONCLUSIVE"


class GovernanceInterventionVerificationSummaryError(ValueError):
    """Base error for intervention-level verification summaries."""


class GovernanceInterventionVerificationSummaryIntegrityError(
    GovernanceInterventionVerificationSummaryError
):
    """Raised when the supplied verification set is invalid."""


class GovernanceInterventionVerificationSummaryDispositionError(
    GovernanceInterventionVerificationSummaryError
):
    """Raised when an unsupported requirement-level disposition is found."""


@dataclass(frozen=True, slots=True)
class GovernanceInterventionVerificationSummary:
    """
    Immutable intervention-level summary derived from one complete and
    verified GEX-001I-E verification set.

    Aggregation precedence:

    NOT_VERIFIED > INCONCLUSIVE > VERIFIED

    Meaning:
    - VERIFIED:
      every governed verification obligation is VERIFIED.
    - NOT_VERIFIED:
      at least one governed verification obligation is NOT_VERIFIED.
    - INCONCLUSIVE:
      none are NOT_VERIFIED and at least one is INCONCLUSIVE.

    This artifact does not:
    - prove intervention success or failure;
    - establish causal attribution;
    - authorize future action;
    - order rollback or continuation;
    - recommend policy changes.
    """

    verification_summary_id: str
    version: str
    schema_version: str

    tenant_id: str
    contract_hash: str
    intervention_id: str
    intervention_type: str

    verification_set_hash: str

    required_count: int
    verified_count: int
    not_verified_count: int
    inconclusive_count: int

    verification_disposition: (
        GovernanceInterventionVerificationSummaryDisposition
    )

    verification_summary_hash: str

    def payload(self) -> dict[str, Any]:
        return {
            "verification_summary_id": self.verification_summary_id,
            "version": self.version,
            "schema_version": self.schema_version,
            "tenant_id": self.tenant_id,
            "contract_hash": self.contract_hash,
            "intervention_id": self.intervention_id,
            "intervention_type": self.intervention_type,
            "verification_set_hash": self.verification_set_hash,
            "required_count": self.required_count,
            "verified_count": self.verified_count,
            "not_verified_count": self.not_verified_count,
            "inconclusive_count": self.inconclusive_count,
            "verification_disposition": (
                self.verification_disposition.value
            ),
        }

    def verify(self) -> bool:
        return self.verification_summary_hash == sha256_hex(
            canonical_json(self.payload())
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            **self.payload(),
            "verification_summary_hash": self.verification_summary_hash,
        }


class GovernanceInterventionVerificationSummaryBuilder:
    """
    Deterministically aggregates one complete governed verification set.

    The builder performs no measurement, evaluation, causal attribution,
    execution, authorization, rollback, or policy recommendation.
    """

    @classmethod
    def build(
        cls,
        *,
        verification_set: GovernanceInterventionVerificationSet,
    ) -> GovernanceInterventionVerificationSummary:
        if not verification_set.verify():
            raise GovernanceInterventionVerificationSummaryIntegrityError(
                "verification set failed deterministic verification"
            )

        if verification_set.required_count < 1:
            raise GovernanceInterventionVerificationSummaryIntegrityError(
                "verification set must contain at least one requirement"
            )

        if (
            verification_set.result_count
            != verification_set.required_count
        ):
            raise GovernanceInterventionVerificationSummaryIntegrityError(
                "verification set result_count does not match required_count"
            )

        if (
            len(verification_set.entries)
            != verification_set.required_count
        ):
            raise GovernanceInterventionVerificationSummaryIntegrityError(
                "verification set entry count does not match required_count"
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

            raise GovernanceInterventionVerificationSummaryDispositionError(
                "unsupported requirement-level verification disposition"
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
                GOVERNANCE_INTERVENTION_VERIFICATION_SUMMARY_ID
            ),
            "version": (
                GOVERNANCE_INTERVENTION_VERIFICATION_SUMMARY_VERSION
            ),
            "schema_version": (
                GOVERNANCE_INTERVENTION_VERIFICATION_SUMMARY_SCHEMA_VERSION
            ),
            "tenant_id": verification_set.tenant_id,
            "contract_hash": verification_set.contract_hash,
            "intervention_id": verification_set.intervention_id,
            "intervention_type": verification_set.intervention_type,
            "verification_set_hash": (
                verification_set.verification_set_hash
            ),
            "required_count": verification_set.required_count,
            "verified_count": verified_count,
            "not_verified_count": not_verified_count,
            "inconclusive_count": inconclusive_count,
            "verification_disposition": (
                verification_disposition.value
            ),
        }

        return GovernanceInterventionVerificationSummary(
            verification_summary_id=payload[
                "verification_summary_id"
            ],
            version=payload["version"],
            schema_version=payload["schema_version"],
            tenant_id=payload["tenant_id"],
            contract_hash=payload["contract_hash"],
            intervention_id=payload["intervention_id"],
            intervention_type=payload["intervention_type"],
            verification_set_hash=payload[
                "verification_set_hash"
            ],
            required_count=payload["required_count"],
            verified_count=payload["verified_count"],
            not_verified_count=payload[
                "not_verified_count"
            ],
            inconclusive_count=payload[
                "inconclusive_count"
            ],
            verification_disposition=verification_disposition,
            verification_summary_hash=sha256_hex(
                canonical_json(payload)
            ),
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
            raise GovernanceInterventionVerificationSummaryIntegrityError(
                "verification disposition counts do not equal required_count"
            )

    @staticmethod
    def _aggregate(
        *,
        verified_count: int,
        not_verified_count: int,
        inconclusive_count: int,
    ) -> GovernanceInterventionVerificationSummaryDisposition:
        if not_verified_count > 0:
            return (
                GovernanceInterventionVerificationSummaryDisposition
                .NOT_VERIFIED
            )

        if inconclusive_count > 0:
            return (
                GovernanceInterventionVerificationSummaryDisposition
                .INCONCLUSIVE
            )

        if verified_count > 0:
            return (
                GovernanceInterventionVerificationSummaryDisposition
                .VERIFIED
            )

        raise GovernanceInterventionVerificationSummaryIntegrityError(
            "verification set produced no governed dispositions"
        )