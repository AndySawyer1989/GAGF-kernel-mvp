from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from backend.app.gagf.governance_intervention_verification_lifecycle import (
    GovernanceInterventionVerificationLifecycleStatus,
)
from backend.app.gagf.governance_intervention_verification_ledger import (
    GovernanceInterventionVerificationRecord,
)
from backend.app.gagf.scientific_authority_guard import (
    canonical_json,
    sha256_hex,
)


GOVERNANCE_INTERVENTION_VERIFICATION_FRESHNESS_ID = (
    "governance-intervention-verification-freshness"
)

GOVERNANCE_INTERVENTION_VERIFICATION_FRESHNESS_VERSION = (
    "0.1.0"
)

GOVERNANCE_INTERVENTION_VERIFICATION_FRESHNESS_SCHEMA_VERSION = (
    "1.0.0"
)


class GovernanceInterventionVerificationFreshnessError(
    ValueError
):
    """Base error for deterministic verification freshness evaluation."""


class GovernanceInterventionVerificationFreshnessIntegrityError(
    GovernanceInterventionVerificationFreshnessError
):
    """Raised when freshness evidence cannot be trusted."""


class GovernanceInterventionVerificationFreshnessTrigger(
    str,
    Enum,
):
    POLICY_CHANGED = "POLICY_CHANGED"
    SOURCE_EVIDENCE_CHANGED = "SOURCE_EVIDENCE_CHANGED"
    VERIFICATION_WINDOW_EXPIRED = "VERIFICATION_WINDOW_EXPIRED"
    MEASUREMENT_THRESHOLD_DRIFT = "MEASUREMENT_THRESHOLD_DRIFT"
    REQUIRED_OBSERVATION_INVALIDATED = (
        "REQUIRED_OBSERVATION_INVALIDATED"
    )
    REQUIREMENTS_CHANGED = "REQUIREMENTS_CHANGED"
    CONTRACT_CHANGED = "CONTRACT_CHANGED"


class GovernanceInterventionVerificationFreshnessDisposition(
    str,
    Enum,
):
    FRESH = "FRESH"
    STALE = "STALE"
    REVERIFICATION_REQUIRED = "REVERIFICATION_REQUIRED"


@dataclass(frozen=True, slots=True)
class GovernanceInterventionVerificationFreshnessEvidence:
    """
    Explicit deterministic evidence used to assess whether an immutable
    verification record remains operationally current.

    The evaluator does not retrieve external state or read the system clock.
    All comparison state must be supplied explicitly.
    """

    tenant_id: str
    intervention_id: str
    verification_record_hash: str

    baseline_policy_hash: str
    current_policy_hash: str

    baseline_source_evidence_hash: str
    current_source_evidence_hash: str

    baseline_requirements_hash: str
    current_requirements_hash: str

    baseline_contract_hash: str
    current_contract_hash: str

    verification_window_end: str
    observed_at: str

    required_observations_valid: bool
    measurement_threshold_drifted: bool

    def payload(self) -> dict[str, Any]:
        return {
            "tenant_id": self.tenant_id,
            "intervention_id": self.intervention_id,
            "verification_record_hash": (
                self.verification_record_hash
            ),
            "baseline_policy_hash": self.baseline_policy_hash,
            "current_policy_hash": self.current_policy_hash,
            "baseline_source_evidence_hash": (
                self.baseline_source_evidence_hash
            ),
            "current_source_evidence_hash": (
                self.current_source_evidence_hash
            ),
            "baseline_requirements_hash": (
                self.baseline_requirements_hash
            ),
            "current_requirements_hash": (
                self.current_requirements_hash
            ),
            "baseline_contract_hash": (
                self.baseline_contract_hash
            ),
            "current_contract_hash": (
                self.current_contract_hash
            ),
            "verification_window_end": (
                self.verification_window_end
            ),
            "observed_at": self.observed_at,
            "required_observations_valid": (
                self.required_observations_valid
            ),
            "measurement_threshold_drifted": (
                self.measurement_threshold_drifted
            ),
        }


@dataclass(frozen=True, slots=True)
class GovernanceInterventionVerificationFreshnessEvaluation:
    """
    Deterministic I-J freshness evaluation.

    proposed_lifecycle_status is advisory to the I-I lifecycle authority.
    This artifact cannot mutate lifecycle state or perform reverification.
    """

    freshness_id: str
    version: str
    schema_version: str

    tenant_id: str
    intervention_id: str
    verification_record_hash: str

    freshness_disposition: str
    proposed_lifecycle_status: str | None
    trigger_codes: tuple[str, ...]

    evidence_hash: str
    freshness_evaluation_hash: str

    def payload(self) -> dict[str, Any]:
        return {
            "freshness_id": self.freshness_id,
            "version": self.version,
            "schema_version": self.schema_version,
            "tenant_id": self.tenant_id,
            "intervention_id": self.intervention_id,
            "verification_record_hash": (
                self.verification_record_hash
            ),
            "freshness_disposition": (
                self.freshness_disposition
            ),
            "proposed_lifecycle_status": (
                self.proposed_lifecycle_status
            ),
            "trigger_codes": list(self.trigger_codes),
            "evidence_hash": self.evidence_hash,
        }

    def verify(self) -> bool:
        return (
            self.freshness_evaluation_hash
            == sha256_hex(
                canonical_json(self.payload())
            )
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            **self.payload(),
            "freshness_evaluation_hash": (
                self.freshness_evaluation_hash
            ),
        }


class GovernanceInterventionVerificationFreshnessEvaluator:
    """
    Deterministically evaluates operational freshness of one persisted
    verification record.

    It does not:
    - mutate the I-G verification ledger;
    - mutate the I-I lifecycle ledger;
    - perform reverification;
    - execute or authorize an intervention;
    - infer causation;
    - select rollback or continuation actions.
    """

    @classmethod
    def evaluate(
        cls,
        *,
        record: GovernanceInterventionVerificationRecord,
        evidence: GovernanceInterventionVerificationFreshnessEvidence,
    ) -> GovernanceInterventionVerificationFreshnessEvaluation:
        cls._validate_record(
            record=record,
            evidence=evidence,
        )

        window_end = cls._parse_timestamp(
            evidence.verification_window_end,
            field_name="verification_window_end",
        )

        observed_at = cls._parse_timestamp(
            evidence.observed_at,
            field_name="observed_at",
        )

        triggers: list[
            GovernanceInterventionVerificationFreshnessTrigger
        ] = []

        if (
            evidence.baseline_policy_hash
            != evidence.current_policy_hash
        ):
            triggers.append(
                GovernanceInterventionVerificationFreshnessTrigger
                .POLICY_CHANGED
            )

        if (
            evidence.baseline_source_evidence_hash
            != evidence.current_source_evidence_hash
        ):
            triggers.append(
                GovernanceInterventionVerificationFreshnessTrigger
                .SOURCE_EVIDENCE_CHANGED
            )

        if observed_at > window_end:
            triggers.append(
                GovernanceInterventionVerificationFreshnessTrigger
                .VERIFICATION_WINDOW_EXPIRED
            )

        if evidence.measurement_threshold_drifted:
            triggers.append(
                GovernanceInterventionVerificationFreshnessTrigger
                .MEASUREMENT_THRESHOLD_DRIFT
            )

        if not evidence.required_observations_valid:
            triggers.append(
                GovernanceInterventionVerificationFreshnessTrigger
                .REQUIRED_OBSERVATION_INVALIDATED
            )

        if (
            evidence.baseline_requirements_hash
            != evidence.current_requirements_hash
        ):
            triggers.append(
                GovernanceInterventionVerificationFreshnessTrigger
                .REQUIREMENTS_CHANGED
            )

        if (
            evidence.baseline_contract_hash
            != evidence.current_contract_hash
        ):
            triggers.append(
                GovernanceInterventionVerificationFreshnessTrigger
                .CONTRACT_CHANGED
            )

        trigger_set = frozenset(triggers)

        reverification_triggers = frozenset(
            {
                GovernanceInterventionVerificationFreshnessTrigger
                .POLICY_CHANGED,
                GovernanceInterventionVerificationFreshnessTrigger
                .REQUIRED_OBSERVATION_INVALIDATED,
                GovernanceInterventionVerificationFreshnessTrigger
                .REQUIREMENTS_CHANGED,
                GovernanceInterventionVerificationFreshnessTrigger
                .CONTRACT_CHANGED,
            }
        )

        stale_triggers = frozenset(
            {
                GovernanceInterventionVerificationFreshnessTrigger
                .SOURCE_EVIDENCE_CHANGED,
                GovernanceInterventionVerificationFreshnessTrigger
                .VERIFICATION_WINDOW_EXPIRED,
                GovernanceInterventionVerificationFreshnessTrigger
                .MEASUREMENT_THRESHOLD_DRIFT,
            }
        )

        if trigger_set & reverification_triggers:
            disposition = (
                GovernanceInterventionVerificationFreshnessDisposition
                .REVERIFICATION_REQUIRED
            )
            proposed_lifecycle_status = (
                GovernanceInterventionVerificationLifecycleStatus
                .REVERIFICATION_REQUIRED
                .value
            )

        elif trigger_set & stale_triggers:
            disposition = (
                GovernanceInterventionVerificationFreshnessDisposition
                .STALE
            )
            proposed_lifecycle_status = (
                GovernanceInterventionVerificationLifecycleStatus
                .STALE
                .value
            )

        else:
            disposition = (
                GovernanceInterventionVerificationFreshnessDisposition
                .FRESH
            )
            proposed_lifecycle_status = None

        canonical_triggers = tuple(
            trigger.value
            for trigger in (
                GovernanceInterventionVerificationFreshnessTrigger
            )
            if trigger in trigger_set
        )

        evidence_hash = sha256_hex(
            canonical_json(
                evidence.payload()
            )
        )

        payload: dict[str, Any] = {
            "freshness_id": (
                GOVERNANCE_INTERVENTION_VERIFICATION_FRESHNESS_ID
            ),
            "version": (
                GOVERNANCE_INTERVENTION_VERIFICATION_FRESHNESS_VERSION
            ),
            "schema_version": (
                GOVERNANCE_INTERVENTION_VERIFICATION_FRESHNESS_SCHEMA_VERSION
            ),
            "tenant_id": record.tenant_id,
            "intervention_id": record.intervention_id,
            "verification_record_hash": (
                record.record_hash
            ),
            "freshness_disposition": (
                disposition.value
            ),
            "proposed_lifecycle_status": (
                proposed_lifecycle_status
            ),
            "trigger_codes": list(
                canonical_triggers
            ),
            "evidence_hash": evidence_hash,
        }

        return GovernanceInterventionVerificationFreshnessEvaluation(
            freshness_id=payload["freshness_id"],
            version=payload["version"],
            schema_version=payload["schema_version"],
            tenant_id=payload["tenant_id"],
            intervention_id=payload["intervention_id"],
            verification_record_hash=payload[
                "verification_record_hash"
            ],
            freshness_disposition=payload[
                "freshness_disposition"
            ],
            proposed_lifecycle_status=payload[
                "proposed_lifecycle_status"
            ],
            trigger_codes=canonical_triggers,
            evidence_hash=evidence_hash,
            freshness_evaluation_hash=sha256_hex(
                canonical_json(payload)
            ),
        )

    @staticmethod
    def _validate_record(
        *,
        record: GovernanceInterventionVerificationRecord,
        evidence: GovernanceInterventionVerificationFreshnessEvidence,
    ) -> None:
        if not record.verify():
            raise GovernanceInterventionVerificationFreshnessIntegrityError(
                "verification record failed deterministic verification"
            )

        if not evidence.tenant_id.strip():
            raise GovernanceInterventionVerificationFreshnessError(
                "tenant_id is required"
            )

        if evidence.tenant_id != evidence.tenant_id.strip():
            raise GovernanceInterventionVerificationFreshnessError(
                "tenant_id must already be canonical"
            )

        if not evidence.intervention_id.strip():
            raise GovernanceInterventionVerificationFreshnessError(
                "intervention_id is required"
            )

        if (
            evidence.tenant_id
            != record.tenant_id
        ):
            raise GovernanceInterventionVerificationFreshnessIntegrityError(
                "freshness evidence tenant does not match "
                "verification record tenant"
            )

        if (
            evidence.intervention_id
            != record.intervention_id
        ):
            raise GovernanceInterventionVerificationFreshnessIntegrityError(
                "freshness evidence intervention does not match "
                "verification record intervention"
            )

        if (
            evidence.verification_record_hash
            != record.record_hash
        ):
            raise GovernanceInterventionVerificationFreshnessIntegrityError(
                "freshness evidence is not bound to the "
                "verification record"
            )

        required_hash_fields = {
            "baseline_policy_hash": (
                evidence.baseline_policy_hash
            ),
            "current_policy_hash": (
                evidence.current_policy_hash
            ),
            "baseline_source_evidence_hash": (
                evidence.baseline_source_evidence_hash
            ),
            "current_source_evidence_hash": (
                evidence.current_source_evidence_hash
            ),
            "baseline_requirements_hash": (
                evidence.baseline_requirements_hash
            ),
            "current_requirements_hash": (
                evidence.current_requirements_hash
            ),
            "baseline_contract_hash": (
                evidence.baseline_contract_hash
            ),
            "current_contract_hash": (
                evidence.current_contract_hash
            ),
        }

        for field_name, value in required_hash_fields.items():
            if not value.strip():
                raise GovernanceInterventionVerificationFreshnessError(
                    f"{field_name} is required"
                )

    @staticmethod
    def _parse_timestamp(
        value: str,
        *,
        field_name: str,
    ) -> datetime:
        normalized = value.strip()

        if not normalized:
            raise GovernanceInterventionVerificationFreshnessError(
                f"{field_name} is required"
            )

        candidate = normalized

        if candidate.endswith("Z"):
            candidate = (
                candidate[:-1]
                + "+00:00"
            )

        try:
            parsed = datetime.fromisoformat(
                candidate
            )
        except ValueError as exc:
            raise GovernanceInterventionVerificationFreshnessError(
                f"{field_name} must be ISO-8601"
            ) from exc

        if parsed.tzinfo is None:
            raise GovernanceInterventionVerificationFreshnessError(
                f"{field_name} must include a timezone"
            )

        return parsed.astimezone(
            timezone.utc
        )