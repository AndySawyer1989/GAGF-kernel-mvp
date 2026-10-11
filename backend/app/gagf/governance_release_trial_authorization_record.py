from __future__ import annotations

import hashlib
import hmac
import json
from dataclasses import dataclass
from typing import Any

from backend.app.gagf.governance_release_acceptance_manifest import (
    GovernanceReleaseAcceptanceManifest,
)
from backend.app.gagf.governance_release_acceptance_manifest_proof import (
    GovernanceReleaseAcceptanceManifestProofResult,
)
from backend.app.gagf.governance_release_trial_authorization_decision import (
    GovernanceReleaseTrialAuthorizationDecision,
)
from backend.app.gagf.governance_release_trial_authorization_gate import (
    GovernanceReleaseTrialAuthorizationGateResult,
)
from backend.app.gagf.governance_release_trial_authorization_manifest import (
    GovernanceReleaseTrialAuthorizationManifest,
)


GOVERNANCE_RELEASE_TRIAL_AUTHORIZATION_RECORD_TYPE = (
    "governance-release-trial-authorization-record"
)

GOVERNANCE_RELEASE_TRIAL_AUTHORIZATION_RECORD_VERSION = (
    "0.1.0"
)

GOVERNANCE_RELEASE_TRIAL_AUTHORIZATION_SIGNATURE_ALGORITHM = (
    "hmac-sha256"
)

GOVERNANCE_RELEASE_TRIAL_AUTHORIZATION_SIGNATURE_VERSION = (
    "1.0.0"
)


@dataclass(
    frozen=True,
    slots=True,
)
class GovernanceReleaseTrialAuthorizationRecord:
    release_environment: str
    backup_id: str
    decision_id: str
    decided_by: str
    decided_at: str
    decision: str
    trial_authorized: bool

    acceptance_manifest_hash: str
    manifest_proof_hash: str
    authorization_decision_hash: str
    authorization_manifest_hash: str
    authorization_gate_hash: str

    lineage_hash: str

    key_id: str
    signature: str

    record_type: str = (
        GOVERNANCE_RELEASE_TRIAL_AUTHORIZATION_RECORD_TYPE
    )

    version: str = (
        GOVERNANCE_RELEASE_TRIAL_AUTHORIZATION_RECORD_VERSION
    )

    signature_algorithm: str = (
        GOVERNANCE_RELEASE_TRIAL_AUTHORIZATION_SIGNATURE_ALGORITHM
    )

    signature_version: str = (
        GOVERNANCE_RELEASE_TRIAL_AUTHORIZATION_SIGNATURE_VERSION
    )

    def to_dict(
        self,
    ) -> dict[str, object]:
        return {
            "record_type":
                self.record_type,
            "version":
                self.version,
            "release_environment":
                self.release_environment,
            "backup_id":
                self.backup_id,
            "decision_id":
                self.decision_id,
            "decided_by":
                self.decided_by,
            "decided_at":
                self.decided_at,
            "decision":
                self.decision,
            "trial_authorized":
                self.trial_authorized,
            "acceptance_manifest_hash":
                self.acceptance_manifest_hash,
            "manifest_proof_hash":
                self.manifest_proof_hash,
            "authorization_decision_hash":
                self.authorization_decision_hash,
            "authorization_manifest_hash":
                self.authorization_manifest_hash,
            "authorization_gate_hash":
                self.authorization_gate_hash,
            "lineage_hash":
                self.lineage_hash,
            "key_id":
                self.key_id,
            "signature":
                self.signature,
            "signature_algorithm":
                self.signature_algorithm,
            "signature_version":
                self.signature_version,
            "boundaries": {
                "record_is_evidence":
                    True,
                "record_binds_existing_trial_authorization":
                    True,
                "record_does_not_create_trial_authorization":
                    True,
                "signature_proves_integrity_not_human_identity":
                    True,
                "signing_key_identity_is_not_actor_identity":
                    True,
                "record_is_not_deployment_execution":
                    True,
                "record_is_not_paid_assessment_execution":
                    True,
                "record_is_not_pa001_paid_work_authorization":
                    True,
                "record_is_not_delivery_approval":
                    True,
                "record_is_not_production_activation":
                    True,
                "record_is_not_intervention_authority":
                    True,
                "record_does_not_invoke_pa014_or_pa015":
                    True,
            },
        }


def canonical_json(
    value: Any,
) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


def sha256_json(
    value: Any,
) -> str:
    return hashlib.sha256(
        canonical_json(
            value
        ).encode(
            "utf-8"
        )
    ).hexdigest()


def build_trial_authorization_lineage_payload(
    *,
    acceptance_manifest:
        GovernanceReleaseAcceptanceManifest,
    manifest_proof:
        GovernanceReleaseAcceptanceManifestProofResult,
    authorization_decision:
        GovernanceReleaseTrialAuthorizationDecision,
    authorization_manifest:
        GovernanceReleaseTrialAuthorizationManifest,
    authorization_gate:
        GovernanceReleaseTrialAuthorizationGateResult,
) -> dict[str, object]:
    _require_evidence_types(
        acceptance_manifest=acceptance_manifest,
        manifest_proof=manifest_proof,
        authorization_decision=authorization_decision,
        authorization_manifest=authorization_manifest,
        authorization_gate=authorization_gate,
    )

    return {
        "release_environment":
            authorization_decision.release_environment,
        "backup_id":
            authorization_decision.backup_id,
        "decision_id":
            authorization_decision.decision_id,
        "decided_by":
            authorization_decision.decided_by,
        "decided_at":
            authorization_decision.decided_at,
        "decision":
            authorization_decision.decision,
        "trial_authorized":
            authorization_decision.trial_authorized,
        "acceptance_manifest_hash":
            sha256_json(
                acceptance_manifest.to_dict()
            ),
        "manifest_proof_hash":
            sha256_json(
                manifest_proof.to_dict()
            ),
        "authorization_decision_hash":
            sha256_json(
                authorization_decision.to_dict()
            ),
        "authorization_manifest_hash":
            sha256_json(
                authorization_manifest.to_dict()
            ),
        "authorization_gate_hash":
            sha256_json(
                authorization_gate.to_dict()
            ),
    }


def canonical_trial_authorization_signature_payload(
    *,
    lineage_payload: dict[str, object],
    lineage_hash: str,
    key_id: str,
    signature_algorithm: str = (
        GOVERNANCE_RELEASE_TRIAL_AUTHORIZATION_SIGNATURE_ALGORITHM
    ),
    signature_version: str = (
        GOVERNANCE_RELEASE_TRIAL_AUTHORIZATION_SIGNATURE_VERSION
    ),
) -> dict[str, object]:
    normalized_key_id = _normalize_required_text(
        name="key_id",
        value=key_id,
    )

    if (
        signature_algorithm
        != GOVERNANCE_RELEASE_TRIAL_AUTHORIZATION_SIGNATURE_ALGORITHM
    ):
        raise ValueError(
            "unsupported trial authorization signature algorithm: "
            f"{signature_algorithm}"
        )

    if (
        signature_version
        != GOVERNANCE_RELEASE_TRIAL_AUTHORIZATION_SIGNATURE_VERSION
    ):
        raise ValueError(
            "unsupported trial authorization signature version: "
            f"{signature_version}"
        )

    return {
        "lineage":
            dict(
                lineage_payload
            ),
        "lineage_hash":
            lineage_hash,
        "key_id":
            normalized_key_id,
        "signature_algorithm":
            signature_algorithm,
        "signature_version":
            signature_version,
    }


def compute_trial_authorization_signature(
    *,
    lineage_payload: dict[str, object],
    lineage_hash: str,
    key_id: str,
    secret: bytes,
    signature_algorithm: str = (
        GOVERNANCE_RELEASE_TRIAL_AUTHORIZATION_SIGNATURE_ALGORITHM
    ),
    signature_version: str = (
        GOVERNANCE_RELEASE_TRIAL_AUTHORIZATION_SIGNATURE_VERSION
    ),
) -> str:
    if not isinstance(
        secret,
        bytes,
    ):
        raise TypeError(
            "secret must be bytes"
        )

    if not secret:
        raise ValueError(
            "trial authorization signing secret is required"
        )

    payload = (
        canonical_trial_authorization_signature_payload(
            lineage_payload=lineage_payload,
            lineage_hash=lineage_hash,
            key_id=key_id,
            signature_algorithm=signature_algorithm,
            signature_version=signature_version,
        )
    )

    return hmac.new(
        secret,
        canonical_json(
            payload
        ).encode(
            "utf-8"
        ),
        hashlib.sha256,
    ).hexdigest()


def build_signed_trial_authorization_record(
    *,
    acceptance_manifest:
        GovernanceReleaseAcceptanceManifest,
    manifest_proof:
        GovernanceReleaseAcceptanceManifestProofResult,
    authorization_decision:
        GovernanceReleaseTrialAuthorizationDecision,
    authorization_manifest:
        GovernanceReleaseTrialAuthorizationManifest,
    authorization_gate:
        GovernanceReleaseTrialAuthorizationGateResult,
    key_id: str,
    secret: bytes,
) -> GovernanceReleaseTrialAuthorizationRecord:
    lineage_payload = (
        build_trial_authorization_lineage_payload(
            acceptance_manifest=acceptance_manifest,
            manifest_proof=manifest_proof,
            authorization_decision=authorization_decision,
            authorization_manifest=authorization_manifest,
            authorization_gate=authorization_gate,
        )
    )

    _require_authorized_chain(
        authorization_decision=authorization_decision,
        authorization_manifest=authorization_manifest,
        authorization_gate=authorization_gate,
    )

    lineage_hash = sha256_json(
        lineage_payload
    )

    signature = (
        compute_trial_authorization_signature(
            lineage_payload=lineage_payload,
            lineage_hash=lineage_hash,
            key_id=key_id,
            secret=secret,
        )
    )

    return GovernanceReleaseTrialAuthorizationRecord(
        release_environment=(
            authorization_decision.release_environment
        ),
        backup_id=(
            authorization_decision.backup_id
        ),
        decision_id=(
            authorization_decision.decision_id
        ),
        decided_by=(
            authorization_decision.decided_by
        ),
        decided_at=(
            authorization_decision.decided_at
        ),
        decision=(
            authorization_decision.decision
        ),
        trial_authorized=(
            authorization_decision.trial_authorized
        ),
        acceptance_manifest_hash=(
            lineage_payload[
                "acceptance_manifest_hash"
            ]
        ),
        manifest_proof_hash=(
            lineage_payload[
                "manifest_proof_hash"
            ]
        ),
        authorization_decision_hash=(
            lineage_payload[
                "authorization_decision_hash"
            ]
        ),
        authorization_manifest_hash=(
            lineage_payload[
                "authorization_manifest_hash"
            ]
        ),
        authorization_gate_hash=(
            lineage_payload[
                "authorization_gate_hash"
            ]
        ),
        lineage_hash=(
            lineage_hash
        ),
        key_id=(
            key_id.strip()
        ),
        signature=(
            signature
        ),
    )


def verify_trial_authorization_record(
    *,
    record:
        GovernanceReleaseTrialAuthorizationRecord,
    acceptance_manifest:
        GovernanceReleaseAcceptanceManifest,
    manifest_proof:
        GovernanceReleaseAcceptanceManifestProofResult,
    authorization_decision:
        GovernanceReleaseTrialAuthorizationDecision,
    authorization_manifest:
        GovernanceReleaseTrialAuthorizationManifest,
    authorization_gate:
        GovernanceReleaseTrialAuthorizationGateResult,
    secret: bytes,
) -> bool:
    if not isinstance(
        record,
        GovernanceReleaseTrialAuthorizationRecord,
    ):
        raise TypeError(
            "record must be a "
            "GovernanceReleaseTrialAuthorizationRecord"
        )

    lineage_payload = (
        build_trial_authorization_lineage_payload(
            acceptance_manifest=acceptance_manifest,
            manifest_proof=manifest_proof,
            authorization_decision=authorization_decision,
            authorization_manifest=authorization_manifest,
            authorization_gate=authorization_gate,
        )
    )

    expected_lineage_hash = (
        sha256_json(
            lineage_payload
        )
    )

    if not hmac.compare_digest(
        expected_lineage_hash,
        record.lineage_hash,
    ):
        return False

    expected_identity = {
        "release_environment":
            authorization_decision.release_environment,
        "backup_id":
            authorization_decision.backup_id,
        "decision_id":
            authorization_decision.decision_id,
        "decided_by":
            authorization_decision.decided_by,
        "decided_at":
            authorization_decision.decided_at,
        "decision":
            authorization_decision.decision,
        "trial_authorized":
            authorization_decision.trial_authorized,
        "acceptance_manifest_hash":
            lineage_payload[
                "acceptance_manifest_hash"
            ],
        "manifest_proof_hash":
            lineage_payload[
                "manifest_proof_hash"
            ],
        "authorization_decision_hash":
            lineage_payload[
                "authorization_decision_hash"
            ],
        "authorization_manifest_hash":
            lineage_payload[
                "authorization_manifest_hash"
            ],
        "authorization_gate_hash":
            lineage_payload[
                "authorization_gate_hash"
            ],
    }

    actual_identity = {
        "release_environment":
            record.release_environment,
        "backup_id":
            record.backup_id,
        "decision_id":
            record.decision_id,
        "decided_by":
            record.decided_by,
        "decided_at":
            record.decided_at,
        "decision":
            record.decision,
        "trial_authorized":
            record.trial_authorized,
        "acceptance_manifest_hash":
            record.acceptance_manifest_hash,
        "manifest_proof_hash":
            record.manifest_proof_hash,
        "authorization_decision_hash":
            record.authorization_decision_hash,
        "authorization_manifest_hash":
            record.authorization_manifest_hash,
        "authorization_gate_hash":
            record.authorization_gate_hash,
    }

    if (
        actual_identity
        != expected_identity
    ):
        return False

    expected_signature = (
        compute_trial_authorization_signature(
            lineage_payload=lineage_payload,
            lineage_hash=record.lineage_hash,
            key_id=record.key_id,
            secret=secret,
            signature_algorithm=record.signature_algorithm,
            signature_version=record.signature_version,
        )
    )

    return hmac.compare_digest(
        expected_signature,
        record.signature,
    )


def _require_authorized_chain(
    *,
    authorization_decision:
        GovernanceReleaseTrialAuthorizationDecision,
    authorization_manifest:
        GovernanceReleaseTrialAuthorizationManifest,
    authorization_gate:
        GovernanceReleaseTrialAuthorizationGateResult,
) -> None:
    if (
        authorization_decision.trial_authorized
        is not True
    ):
        raise ValueError(
            "authorization decision must authorize trial"
        )

    if (
        authorization_manifest.trial_authorized
        is not True
    ):
        raise ValueError(
            "authorization manifest must authorize trial"
        )

    if (
        authorization_gate.passed
        is not True
    ):
        raise ValueError(
            "authorization gate must pass"
        )

    if (
        authorization_gate.trial_authorized
        is not True
    ):
        raise ValueError(
            "authorization gate must verify trial authorization"
        )


def _require_evidence_types(
    *,
    acceptance_manifest: object,
    manifest_proof: object,
    authorization_decision: object,
    authorization_manifest: object,
    authorization_gate: object,
) -> None:
    expected = (
        (
            "acceptance_manifest",
            acceptance_manifest,
            GovernanceReleaseAcceptanceManifest,
        ),
        (
            "manifest_proof",
            manifest_proof,
            GovernanceReleaseAcceptanceManifestProofResult,
        ),
        (
            "authorization_decision",
            authorization_decision,
            GovernanceReleaseTrialAuthorizationDecision,
        ),
        (
            "authorization_manifest",
            authorization_manifest,
            GovernanceReleaseTrialAuthorizationManifest,
        ),
        (
            "authorization_gate",
            authorization_gate,
            GovernanceReleaseTrialAuthorizationGateResult,
        ),
    )

    for (
        name,
        value,
        expected_type,
    ) in expected:
        if not isinstance(
            value,
            expected_type,
        ):
            raise TypeError(
                f"{name} must be a "
                f"{expected_type.__name__}"
            )


def _normalize_required_text(
    *,
    name: str,
    value: object,
) -> str:
    if not isinstance(
        value,
        str,
    ):
        raise TypeError(
            f"{name} must be a string"
        )

    normalized = (
        value.strip()
    )

    if not normalized:
        raise ValueError(
            f"{name} must not be empty"
        )

    return normalized