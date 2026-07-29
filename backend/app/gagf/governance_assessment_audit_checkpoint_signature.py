from __future__ import annotations

import hashlib
import hmac
import json
from dataclasses import asdict, dataclass
from typing import Any

from backend.app.gagf.governance_assessment_audit_checkpoint import (
    AssessmentAuditCheckpoint,
)


ASSESSMENT_CHECKPOINT_SIGNATURE_VERSION = "1.0.0"
ASSESSMENT_CHECKPOINT_SIGNATURE_ALGORITHM = "hmac-sha256"


@dataclass(frozen=True)
class SignedAssessmentAuditCheckpoint:
    checkpoint: AssessmentAuditCheckpoint
    key_id: str
    signature: str
    signature_algorithm: str = (
        ASSESSMENT_CHECKPOINT_SIGNATURE_ALGORITHM
    )
    signature_version: str = (
        ASSESSMENT_CHECKPOINT_SIGNATURE_VERSION
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "checkpoint": self.checkpoint.to_dict(),
            "key_id": self.key_id,
            "signature": self.signature,
            "signature_algorithm": self.signature_algorithm,
            "signature_version": self.signature_version,
        }


def canonical_checkpoint_signature_payload(
    *,
    checkpoint: AssessmentAuditCheckpoint,
    key_id: str,
    signature_algorithm: str = (
        ASSESSMENT_CHECKPOINT_SIGNATURE_ALGORITHM
    ),
    signature_version: str = (
        ASSESSMENT_CHECKPOINT_SIGNATURE_VERSION
    ),
) -> dict[str, Any]:
    if signature_algorithm != (
        ASSESSMENT_CHECKPOINT_SIGNATURE_ALGORITHM
    ):
        raise ValueError(
            "unsupported checkpoint signature algorithm: "
            f"{signature_algorithm}"
        )

    return {
        "checkpoint": asdict(checkpoint),
        "key_id": key_id,
        "signature_algorithm": signature_algorithm,
        "signature_version": signature_version,
    }


def compute_checkpoint_signature(
    *,
    checkpoint: AssessmentAuditCheckpoint,
    key_id: str,
    secret: bytes,
    signature_algorithm: str = (
        ASSESSMENT_CHECKPOINT_SIGNATURE_ALGORITHM
    ),
    signature_version: str = (
        ASSESSMENT_CHECKPOINT_SIGNATURE_VERSION
    ),
) -> str:
    if not key_id.strip():
        raise ValueError("checkpoint signing key_id is required")

    if not secret:
        raise ValueError("checkpoint signing secret is required")

    payload = canonical_checkpoint_signature_payload(
        checkpoint=checkpoint,
        key_id=key_id,
        signature_algorithm=signature_algorithm,
        signature_version=signature_version,
    )

    canonical_json = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")

    return hmac.new(
        secret,
        canonical_json,
        hashlib.sha256,
    ).hexdigest()


def sign_assessment_audit_checkpoint(
    *,
    checkpoint: AssessmentAuditCheckpoint,
    key_id: str,
    secret: bytes,
) -> SignedAssessmentAuditCheckpoint:
    signature = compute_checkpoint_signature(
        checkpoint=checkpoint,
        key_id=key_id,
        secret=secret,
    )

    return SignedAssessmentAuditCheckpoint(
        checkpoint=checkpoint,
        key_id=key_id,
        signature=signature,
    )


def verify_assessment_audit_checkpoint_signature(
    *,
    signed_checkpoint: SignedAssessmentAuditCheckpoint,
    secret: bytes,
) -> bool:
    expected_signature = compute_checkpoint_signature(
        checkpoint=signed_checkpoint.checkpoint,
        key_id=signed_checkpoint.key_id,
        secret=secret,
        signature_algorithm=(
            signed_checkpoint.signature_algorithm
        ),
        signature_version=(
            signed_checkpoint.signature_version
        ),
    )

    return hmac.compare_digest(
        expected_signature,
        signed_checkpoint.signature,
    )
