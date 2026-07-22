from dataclasses import dataclass
from pathlib import Path

from backend.app.gagf.scientific_evidence_checkpoint import (
    SCIENTIFIC_EVIDENCE_CHECKPOINT_ID,
    SCIENTIFIC_EVIDENCE_CHECKPOINT_SCHEMA_VERSION,
    SCIENTIFIC_EVIDENCE_CHECKPOINT_VERSION,
    ScientificEvidenceCheckpoint,
    ScientificEvidenceCheckpointBuilder,
)


SCIENTIFIC_EVIDENCE_CHECKPOINT_VERIFIER_ID = (
    "scientific-evidence-checkpoint-replay-verifier"
)
SCIENTIFIC_EVIDENCE_CHECKPOINT_VERIFIER_VERSION = "0.1.0"


@dataclass(frozen=True, slots=True)
class ScientificEvidenceCheckpointReplayResult:
    valid: bool
    verifier_id: str
    verifier_version: str
    original_checkpoint_hash: str
    replayed_checkpoint_hash: str | None
    checks: dict[str, bool]
    errors: tuple[str, ...]

    def to_dict(self) -> dict:
        return {
            "valid": self.valid,
            "verifier_id": self.verifier_id,
            "verifier_version": self.verifier_version,
            "original_checkpoint_hash": (
                self.original_checkpoint_hash
            ),
            "replayed_checkpoint_hash": (
                self.replayed_checkpoint_hash
            ),
            "checks": dict(self.checks),
            "errors": list(self.errors),
        }


class ScientificEvidenceCheckpointReplayVerifier:
    def verify(
        self,
        *,
        checkpoint: ScientificEvidenceCheckpoint,
        authority_database_path: str | Path,
        audit_database_path: str | Path,
    ) -> ScientificEvidenceCheckpointReplayResult:
        checks = {
            "checkpoint_hash_valid": checkpoint.verify(),
            "checkpoint_schema_supported": (
                checkpoint.checkpoint_schema_version
                == SCIENTIFIC_EVIDENCE_CHECKPOINT_SCHEMA_VERSION
            ),
            "checkpoint_identity_supported": (
                checkpoint.checkpoint_id
                == SCIENTIFIC_EVIDENCE_CHECKPOINT_ID
            ),
            "checkpoint_version_supported": (
                checkpoint.checkpoint_version
                == SCIENTIFIC_EVIDENCE_CHECKPOINT_VERSION
            ),
            "authority_ledger_identity_matches": False,
            "audit_ledger_identity_matches": False,
            "authority_audit_matches_replay": False,
            "audit_ledger_audit_matches_replay": False,
            "checkpoint_validity_matches_replay": False,
            "checkpoint_hash_matches_replay": False,
        }
        errors: list[str] = []

        if not checks["checkpoint_hash_valid"]:
            errors.append(
                "Checkpoint failed SHA-256 verification."
            )

        if not checks["checkpoint_schema_supported"]:
            errors.append(
                "Checkpoint schema version is unsupported."
            )

        if not checks["checkpoint_identity_supported"]:
            errors.append(
                "Checkpoint identity is unsupported."
            )

        if not checks["checkpoint_version_supported"]:
            errors.append(
                "Checkpoint version is unsupported."
            )

        replayed_checkpoint = (
            ScientificEvidenceCheckpointBuilder()
            .build(
                authority_database_path=authority_database_path,
                audit_database_path=audit_database_path,
            )
        )

        checks["authority_ledger_identity_matches"] = (
            checkpoint.authority_ledger_identity
            == replayed_checkpoint.authority_ledger_identity
        )
        if not checks["authority_ledger_identity_matches"]:
            errors.append(
                "Authority-ledger identity does not match replay."
            )

        checks["audit_ledger_identity_matches"] = (
            checkpoint.audit_ledger_identity
            == replayed_checkpoint.audit_ledger_identity
        )
        if not checks["audit_ledger_identity_matches"]:
            errors.append(
                "Audit-ledger identity does not match replay."
            )

        checks["authority_audit_matches_replay"] = (
            checkpoint.authority_audit
            == replayed_checkpoint.authority_audit
        )
        if not checks["authority_audit_matches_replay"]:
            errors.append(
                "Authority-ledger audit does not match replay."
            )

        checks["audit_ledger_audit_matches_replay"] = (
            checkpoint.audit_ledger_audit
            == replayed_checkpoint.audit_ledger_audit
        )
        if not checks["audit_ledger_audit_matches_replay"]:
            errors.append(
                "Audit-ledger audit does not match replay."
            )

        checks["checkpoint_validity_matches_replay"] = (
            checkpoint.valid
            == replayed_checkpoint.valid
        )
        if not checks["checkpoint_validity_matches_replay"]:
            errors.append(
                "Checkpoint validity does not match replay."
            )

        checks["checkpoint_hash_matches_replay"] = (
            checkpoint.checkpoint_hash
            == replayed_checkpoint.checkpoint_hash
        )
        if not checks["checkpoint_hash_matches_replay"]:
            errors.append(
                "Checkpoint hash does not match replay."
            )

        return ScientificEvidenceCheckpointReplayResult(
            valid=all(checks.values()),
            verifier_id=(
                SCIENTIFIC_EVIDENCE_CHECKPOINT_VERIFIER_ID
            ),
            verifier_version=(
                SCIENTIFIC_EVIDENCE_CHECKPOINT_VERIFIER_VERSION
            ),
            original_checkpoint_hash=(
                checkpoint.checkpoint_hash
            ),
            replayed_checkpoint_hash=(
                replayed_checkpoint.checkpoint_hash
            ),
            checks=checks,
            errors=tuple(errors),
        )
