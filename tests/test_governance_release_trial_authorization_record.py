from dataclasses import FrozenInstanceError, replace

import pytest

from backend.app.gagf.governance_release_acceptance_manifest import (
    ACCEPTANCE_MANIFEST_STATUS_READY,
    GovernanceReleaseAcceptanceManifest,
)
from backend.app.gagf.governance_release_acceptance_manifest_proof import (
    GovernanceReleaseAcceptanceManifestProofResult,
)
from backend.app.gagf.governance_release_acceptance_suite import (
    RELEASE_ACCEPTANCE_DISPOSITION_ACCEPTED,
)
from backend.app.gagf.governance_release_trial_authorization_decision import (
    TRIAL_AUTHORIZATION_DECISION_AUTHORIZE,
    TRIAL_AUTHORIZATION_DECISION_DENY,
    GovernanceReleaseTrialAuthorizationDecision,
    evaluate_governance_release_trial_authorization_decision,
)
from backend.app.gagf.governance_release_trial_authorization_gate import (
    GovernanceReleaseTrialAuthorizationGateResult,
    evaluate_governance_release_trial_authorization_gate,
)
from backend.app.gagf.governance_release_trial_authorization_manifest import (
    GovernanceReleaseTrialAuthorizationManifest,
    build_governance_release_trial_authorization_manifest,
)
from backend.app.gagf.governance_release_trial_authorization_record import (
    GOVERNANCE_RELEASE_TRIAL_AUTHORIZATION_RECORD_TYPE,
    GOVERNANCE_RELEASE_TRIAL_AUTHORIZATION_RECORD_VERSION,
    GOVERNANCE_RELEASE_TRIAL_AUTHORIZATION_SIGNATURE_ALGORITHM,
    GOVERNANCE_RELEASE_TRIAL_AUTHORIZATION_SIGNATURE_VERSION,
    GovernanceReleaseTrialAuthorizationRecord,
    build_signed_trial_authorization_record,
    build_trial_authorization_lineage_payload,
    canonical_json,
    compute_trial_authorization_signature,
    sha256_json,
    verify_trial_authorization_record,
)


SIGNING_KEY_ID = "paid-trial-release-key-001"
SIGNING_SECRET = b"synthetic-paid-trial-release-secret"
WRONG_SIGNING_SECRET = b"wrong-paid-trial-release-secret"


def build_acceptance_manifest(
    *,
    release_environment: str = "paid_trial",
    backup_id: str = "backup-001",
) -> GovernanceReleaseAcceptanceManifest:
    return GovernanceReleaseAcceptanceManifest(
        release_environment=release_environment,
        backup_id=backup_id,
        status=ACCEPTANCE_MANIFEST_STATUS_READY,
        acceptance_passed=True,
        acceptance_disposition=(
            RELEASE_ACCEPTANCE_DISPOSITION_ACCEPTED
        ),
        checks={
            "release_acceptance":
                True,
        },
        failure_reasons=(),
    )


def build_manifest_proof(
    *,
    release_environment: str = "paid_trial",
    backup_id: str = "backup-001",
) -> GovernanceReleaseAcceptanceManifestProofResult:
    return GovernanceReleaseAcceptanceManifestProofResult(
        release_environment=release_environment,
        backup_id=backup_id,
        passed=True,
        checks={
            "manifest_integrity":
                True,
        },
        failure_reasons=(),
    )


def build_authorization_decision(
    *,
    acceptance_manifest:
        GovernanceReleaseAcceptanceManifest,
    manifest_proof:
        GovernanceReleaseAcceptanceManifestProofResult,
    decision_id: str = "trial-auth-001",
    decided_by: str = "release-operator",
    decided_at: str = "2026-10-07T16:00:00Z",
    decision: str = TRIAL_AUTHORIZATION_DECISION_AUTHORIZE,
) -> GovernanceReleaseTrialAuthorizationDecision:
    return evaluate_governance_release_trial_authorization_decision(
        acceptance_manifest=acceptance_manifest,
        manifest_proof=manifest_proof,
        decision_id=decision_id,
        decided_by=decided_by,
        decided_at=decided_at,
        decision=decision,
    )


def build_authorization_manifest(
    *,
    acceptance_manifest:
        GovernanceReleaseAcceptanceManifest,
    manifest_proof:
        GovernanceReleaseAcceptanceManifestProofResult,
    authorization_decision:
        GovernanceReleaseTrialAuthorizationDecision,
) -> GovernanceReleaseTrialAuthorizationManifest:
    return build_governance_release_trial_authorization_manifest(
        acceptance_manifest=acceptance_manifest,
        manifest_proof=manifest_proof,
        authorization_decision=authorization_decision,
    )


def build_authorization_gate(
    *,
    acceptance_manifest:
        GovernanceReleaseAcceptanceManifest,
    manifest_proof:
        GovernanceReleaseAcceptanceManifestProofResult,
    authorization_decision:
        GovernanceReleaseTrialAuthorizationDecision,
    authorization_manifest:
        GovernanceReleaseTrialAuthorizationManifest,
) -> GovernanceReleaseTrialAuthorizationGateResult:
    return evaluate_governance_release_trial_authorization_gate(
        acceptance_manifest=acceptance_manifest,
        manifest_proof=manifest_proof,
        authorization_decision=authorization_decision,
        authorization_manifest=authorization_manifest,
    )


def build_authorized_chain(
) -> tuple[
    GovernanceReleaseAcceptanceManifest,
    GovernanceReleaseAcceptanceManifestProofResult,
    GovernanceReleaseTrialAuthorizationDecision,
    GovernanceReleaseTrialAuthorizationManifest,
    GovernanceReleaseTrialAuthorizationGateResult,
]:
    acceptance_manifest = (
        build_acceptance_manifest()
    )

    manifest_proof = (
        build_manifest_proof()
    )

    authorization_decision = (
        build_authorization_decision(
            acceptance_manifest=acceptance_manifest,
            manifest_proof=manifest_proof,
        )
    )

    authorization_manifest = (
        build_authorization_manifest(
            acceptance_manifest=acceptance_manifest,
            manifest_proof=manifest_proof,
            authorization_decision=authorization_decision,
        )
    )

    authorization_gate = (
        build_authorization_gate(
            acceptance_manifest=acceptance_manifest,
            manifest_proof=manifest_proof,
            authorization_decision=authorization_decision,
            authorization_manifest=authorization_manifest,
        )
    )

    return (
        acceptance_manifest,
        manifest_proof,
        authorization_decision,
        authorization_manifest,
        authorization_gate,
    )


def build_record(
) -> tuple[
    GovernanceReleaseTrialAuthorizationRecord,
    GovernanceReleaseAcceptanceManifest,
    GovernanceReleaseAcceptanceManifestProofResult,
    GovernanceReleaseTrialAuthorizationDecision,
    GovernanceReleaseTrialAuthorizationManifest,
    GovernanceReleaseTrialAuthorizationGateResult,
]:
    (
        acceptance_manifest,
        manifest_proof,
        authorization_decision,
        authorization_manifest,
        authorization_gate,
    ) = build_authorized_chain()

    record = (
        build_signed_trial_authorization_record(
            acceptance_manifest=acceptance_manifest,
            manifest_proof=manifest_proof,
            authorization_decision=authorization_decision,
            authorization_manifest=authorization_manifest,
            authorization_gate=authorization_gate,
            key_id=SIGNING_KEY_ID,
            secret=SIGNING_SECRET,
        )
    )

    return (
        record,
        acceptance_manifest,
        manifest_proof,
        authorization_decision,
        authorization_manifest,
        authorization_gate,
    )


def verify_record(
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
    secret: bytes = SIGNING_SECRET,
) -> bool:
    return verify_trial_authorization_record(
        record=record,
        acceptance_manifest=acceptance_manifest,
        manifest_proof=manifest_proof,
        authorization_decision=authorization_decision,
        authorization_manifest=authorization_manifest,
        authorization_gate=authorization_gate,
        secret=secret,
    )


def test_authorized_chain_builds_signed_record(
) -> None:
    (
        record,
        _,
        _,
        authorization_decision,
        _,
        authorization_gate,
    ) = build_record()

    assert isinstance(
        record,
        GovernanceReleaseTrialAuthorizationRecord,
    )

    assert record.release_environment == "paid_trial"
    assert record.backup_id == "backup-001"
    assert record.decision_id == "trial-auth-001"
    assert record.decided_by == "release-operator"
    assert record.decided_at == "2026-10-07T16:00:00Z"

    assert (
        record.decision
        == TRIAL_AUTHORIZATION_DECISION_AUTHORIZE
    )

    assert record.trial_authorized is True

    assert (
        authorization_decision.trial_authorized
        is True
    )

    assert authorization_gate.passed is True
    assert authorization_gate.trial_authorized is True

    assert record.key_id == SIGNING_KEY_ID

    assert (
        record.signature_algorithm
        == GOVERNANCE_RELEASE_TRIAL_AUTHORIZATION_SIGNATURE_ALGORITHM
    )

    assert (
        record.signature_version
        == GOVERNANCE_RELEASE_TRIAL_AUTHORIZATION_SIGNATURE_VERSION
    )

    assert len(record.lineage_hash) == 64
    assert len(record.signature) == 64


def test_signed_record_verifies_against_original_chain(
) -> None:
    (
        record,
        acceptance_manifest,
        manifest_proof,
        authorization_decision,
        authorization_manifest,
        authorization_gate,
    ) = build_record()

    assert verify_record(
        record=record,
        acceptance_manifest=acceptance_manifest,
        manifest_proof=manifest_proof,
        authorization_decision=authorization_decision,
        authorization_manifest=authorization_manifest,
        authorization_gate=authorization_gate,
    ) is True


def test_record_generation_is_deterministic_for_same_inputs(
) -> None:
    (
        acceptance_manifest,
        manifest_proof,
        authorization_decision,
        authorization_manifest,
        authorization_gate,
    ) = build_authorized_chain()

    first = build_signed_trial_authorization_record(
        acceptance_manifest=acceptance_manifest,
        manifest_proof=manifest_proof,
        authorization_decision=authorization_decision,
        authorization_manifest=authorization_manifest,
        authorization_gate=authorization_gate,
        key_id=SIGNING_KEY_ID,
        secret=SIGNING_SECRET,
    )

    second = build_signed_trial_authorization_record(
        acceptance_manifest=acceptance_manifest,
        manifest_proof=manifest_proof,
        authorization_decision=authorization_decision,
        authorization_manifest=authorization_manifest,
        authorization_gate=authorization_gate,
        key_id=SIGNING_KEY_ID,
        secret=SIGNING_SECRET,
    )

    assert first == second
    assert first.lineage_hash == second.lineage_hash
    assert first.signature == second.signature


def test_canonical_json_is_order_independent(
) -> None:
    first = {
        "b": 2,
        "a": 1,
    }

    second = {
        "a": 1,
        "b": 2,
    }

    assert (
        canonical_json(first)
        == canonical_json(second)
    )

    assert (
        sha256_json(first)
        == sha256_json(second)
    )


def test_lineage_hash_binds_all_release_authorization_evidence(
) -> None:
    (
        record,
        acceptance_manifest,
        manifest_proof,
        authorization_decision,
        authorization_manifest,
        authorization_gate,
    ) = build_record()

    payload = (
        build_trial_authorization_lineage_payload(
            acceptance_manifest=acceptance_manifest,
            manifest_proof=manifest_proof,
            authorization_decision=authorization_decision,
            authorization_manifest=authorization_manifest,
            authorization_gate=authorization_gate,
        )
    )

    assert (
        record.acceptance_manifest_hash
        == sha256_json(
            acceptance_manifest.to_dict()
        )
    )

    assert (
        record.manifest_proof_hash
        == sha256_json(
            manifest_proof.to_dict()
        )
    )

    assert (
        record.authorization_decision_hash
        == sha256_json(
            authorization_decision.to_dict()
        )
    )

    assert (
        record.authorization_manifest_hash
        == sha256_json(
            authorization_manifest.to_dict()
        )
    )

    assert (
        record.authorization_gate_hash
        == sha256_json(
            authorization_gate.to_dict()
        )
    )

    assert (
        record.lineage_hash
        == sha256_json(payload)
    )


def test_recorded_decision_id_tampering_is_detected(
) -> None:
    (
        record,
        acceptance_manifest,
        manifest_proof,
        authorization_decision,
        authorization_manifest,
        authorization_gate,
    ) = build_record()

    tampered_record = replace(
        record,
        decision_id="tampered-decision",
    )

    assert verify_record(
        record=tampered_record,
        acceptance_manifest=acceptance_manifest,
        manifest_proof=manifest_proof,
        authorization_decision=authorization_decision,
        authorization_manifest=authorization_manifest,
        authorization_gate=authorization_gate,
    ) is False


def test_recorded_actor_tampering_is_detected(
) -> None:
    (
        record,
        acceptance_manifest,
        manifest_proof,
        authorization_decision,
        authorization_manifest,
        authorization_gate,
    ) = build_record()

    tampered_record = replace(
        record,
        decided_by="different-operator",
    )

    assert verify_record(
        record=tampered_record,
        acceptance_manifest=acceptance_manifest,
        manifest_proof=manifest_proof,
        authorization_decision=authorization_decision,
        authorization_manifest=authorization_manifest,
        authorization_gate=authorization_gate,
    ) is False


def test_recorded_timestamp_tampering_is_detected(
) -> None:
    (
        record,
        acceptance_manifest,
        manifest_proof,
        authorization_decision,
        authorization_manifest,
        authorization_gate,
    ) = build_record()

    tampered_record = replace(
        record,
        decided_at="2026-10-08T16:00:00Z",
    )

    assert verify_record(
        record=tampered_record,
        acceptance_manifest=acceptance_manifest,
        manifest_proof=manifest_proof,
        authorization_decision=authorization_decision,
        authorization_manifest=authorization_manifest,
        authorization_gate=authorization_gate,
    ) is False


def test_recorded_release_environment_tampering_is_detected(
) -> None:
    (
        record,
        acceptance_manifest,
        manifest_proof,
        authorization_decision,
        authorization_manifest,
        authorization_gate,
    ) = build_record()

    tampered_record = replace(
        record,
        release_environment="prelive",
    )

    assert verify_record(
        record=tampered_record,
        acceptance_manifest=acceptance_manifest,
        manifest_proof=manifest_proof,
        authorization_decision=authorization_decision,
        authorization_manifest=authorization_manifest,
        authorization_gate=authorization_gate,
    ) is False


def test_recorded_backup_identity_tampering_is_detected(
) -> None:
    (
        record,
        acceptance_manifest,
        manifest_proof,
        authorization_decision,
        authorization_manifest,
        authorization_gate,
    ) = build_record()

    tampered_record = replace(
        record,
        backup_id="backup-999",
    )

    assert verify_record(
        record=tampered_record,
        acceptance_manifest=acceptance_manifest,
        manifest_proof=manifest_proof,
        authorization_decision=authorization_decision,
        authorization_manifest=authorization_manifest,
        authorization_gate=authorization_gate,
    ) is False


def test_recorded_lineage_hash_tampering_is_detected(
) -> None:
    (
        record,
        acceptance_manifest,
        manifest_proof,
        authorization_decision,
        authorization_manifest,
        authorization_gate,
    ) = build_record()

    tampered_record = replace(
        record,
        lineage_hash="0" * 64,
    )

    assert verify_record(
        record=tampered_record,
        acceptance_manifest=acceptance_manifest,
        manifest_proof=manifest_proof,
        authorization_decision=authorization_decision,
        authorization_manifest=authorization_manifest,
        authorization_gate=authorization_gate,
    ) is False


def test_recorded_signature_tampering_is_detected(
) -> None:
    (
        record,
        acceptance_manifest,
        manifest_proof,
        authorization_decision,
        authorization_manifest,
        authorization_gate,
    ) = build_record()

    tampered_record = replace(
        record,
        signature="0" * 64,
    )

    assert verify_record(
        record=tampered_record,
        acceptance_manifest=acceptance_manifest,
        manifest_proof=manifest_proof,
        authorization_decision=authorization_decision,
        authorization_manifest=authorization_manifest,
        authorization_gate=authorization_gate,
    ) is False


def test_recorded_key_id_tampering_is_detected(
) -> None:
    (
        record,
        acceptance_manifest,
        manifest_proof,
        authorization_decision,
        authorization_manifest,
        authorization_gate,
    ) = build_record()

    tampered_record = replace(
        record,
        key_id="other-key",
    )

    assert verify_record(
        record=tampered_record,
        acceptance_manifest=acceptance_manifest,
        manifest_proof=manifest_proof,
        authorization_decision=authorization_decision,
        authorization_manifest=authorization_manifest,
        authorization_gate=authorization_gate,
    ) is False


def test_wrong_secret_fails_verification(
) -> None:
    (
        record,
        acceptance_manifest,
        manifest_proof,
        authorization_decision,
        authorization_manifest,
        authorization_gate,
    ) = build_record()

    assert verify_record(
        record=record,
        acceptance_manifest=acceptance_manifest,
        manifest_proof=manifest_proof,
        authorization_decision=authorization_decision,
        authorization_manifest=authorization_manifest,
        authorization_gate=authorization_gate,
        secret=WRONG_SIGNING_SECRET,
    ) is False


def test_changed_authorization_decision_breaks_original_record(
) -> None:
    (
        record,
        acceptance_manifest,
        manifest_proof,
        authorization_decision,
        _,
        _,
    ) = build_record()

    changed_decision = replace(
        authorization_decision,
        decision_id="new-decision-id",
    )

    changed_manifest = (
        build_governance_release_trial_authorization_manifest(
            acceptance_manifest=acceptance_manifest,
            manifest_proof=manifest_proof,
            authorization_decision=changed_decision,
        )
    )

    changed_gate = (
        evaluate_governance_release_trial_authorization_gate(
            acceptance_manifest=acceptance_manifest,
            manifest_proof=manifest_proof,
            authorization_decision=changed_decision,
            authorization_manifest=changed_manifest,
        )
    )

    assert verify_record(
        record=record,
        acceptance_manifest=acceptance_manifest,
        manifest_proof=manifest_proof,
        authorization_decision=changed_decision,
        authorization_manifest=changed_manifest,
        authorization_gate=changed_gate,
    ) is False


def test_changed_acceptance_manifest_breaks_original_record(
) -> None:
    (
        record,
        _,
        manifest_proof,
        authorization_decision,
        authorization_manifest,
        authorization_gate,
    ) = build_record()

    changed_acceptance_manifest = replace(
        build_acceptance_manifest(),
        checks={
            "release_acceptance":
                True,
            "synthetic_additional_check":
                True,
        },
    )

    assert verify_record(
        record=record,
        acceptance_manifest=changed_acceptance_manifest,
        manifest_proof=manifest_proof,
        authorization_decision=authorization_decision,
        authorization_manifest=authorization_manifest,
        authorization_gate=authorization_gate,
    ) is False


def test_denied_decision_cannot_create_signed_authorization_record(
) -> None:
    acceptance_manifest = (
        build_acceptance_manifest()
    )

    manifest_proof = (
        build_manifest_proof()
    )

    authorization_decision = (
        build_authorization_decision(
            acceptance_manifest=acceptance_manifest,
            manifest_proof=manifest_proof,
            decision=TRIAL_AUTHORIZATION_DECISION_DENY,
        )
    )

    authorization_manifest = (
        build_authorization_manifest(
            acceptance_manifest=acceptance_manifest,
            manifest_proof=manifest_proof,
            authorization_decision=authorization_decision,
        )
    )

    authorization_gate = (
        build_authorization_gate(
            acceptance_manifest=acceptance_manifest,
            manifest_proof=manifest_proof,
            authorization_decision=authorization_decision,
            authorization_manifest=authorization_manifest,
        )
    )

    assert authorization_gate.passed is True
    assert authorization_gate.trial_authorized is False

    with pytest.raises(
        ValueError,
        match="authorization decision must authorize trial",
    ):
        build_signed_trial_authorization_record(
            acceptance_manifest=acceptance_manifest,
            manifest_proof=manifest_proof,
            authorization_decision=authorization_decision,
            authorization_manifest=authorization_manifest,
            authorization_gate=authorization_gate,
            key_id=SIGNING_KEY_ID,
            secret=SIGNING_SECRET,
        )


def test_failed_gate_cannot_create_signed_authorization_record(
) -> None:
    (
        acceptance_manifest,
        manifest_proof,
        authorization_decision,
        authorization_manifest,
        authorization_gate,
    ) = build_authorized_chain()

    failed_gate = replace(
        authorization_gate,
        passed=False,
        trial_authorized=False,
        failure_reasons=(
            "synthetic_gate_failure",
        ),
    )

    with pytest.raises(
        ValueError,
        match="authorization gate must pass",
    ):
        build_signed_trial_authorization_record(
            acceptance_manifest=acceptance_manifest,
            manifest_proof=manifest_proof,
            authorization_decision=authorization_decision,
            authorization_manifest=authorization_manifest,
            authorization_gate=failed_gate,
            key_id=SIGNING_KEY_ID,
            secret=SIGNING_SECRET,
        )


@pytest.mark.parametrize(
    "argument_name",
    (
        "acceptance_manifest",
        "manifest_proof",
        "authorization_decision",
        "authorization_manifest",
        "authorization_gate",
    ),
)
def test_wrong_evidence_types_are_rejected(
    argument_name: str,
) -> None:
    (
        acceptance_manifest,
        manifest_proof,
        authorization_decision,
        authorization_manifest,
        authorization_gate,
    ) = build_authorized_chain()

    kwargs = {
        "acceptance_manifest":
            acceptance_manifest,
        "manifest_proof":
            manifest_proof,
        "authorization_decision":
            authorization_decision,
        "authorization_manifest":
            authorization_manifest,
        "authorization_gate":
            authorization_gate,
        "key_id":
            SIGNING_KEY_ID,
        "secret":
            SIGNING_SECRET,
    }

    kwargs[
        argument_name
    ] = object()

    with pytest.raises(
        TypeError
    ):
        build_signed_trial_authorization_record(
            **kwargs
        )


@pytest.mark.parametrize(
    "key_id",
    (
        "",
        "   ",
    ),
)
def test_empty_signing_key_id_is_rejected(
    key_id: str,
) -> None:
    (
        acceptance_manifest,
        manifest_proof,
        authorization_decision,
        authorization_manifest,
        authorization_gate,
    ) = build_authorized_chain()

    with pytest.raises(
        ValueError,
        match="key_id must not be empty",
    ):
        build_signed_trial_authorization_record(
            acceptance_manifest=acceptance_manifest,
            manifest_proof=manifest_proof,
            authorization_decision=authorization_decision,
            authorization_manifest=authorization_manifest,
            authorization_gate=authorization_gate,
            key_id=key_id,
            secret=SIGNING_SECRET,
        )


def test_non_string_signing_key_id_is_rejected(
) -> None:
    with pytest.raises(
        TypeError,
        match="key_id must be a string",
    ):
        compute_trial_authorization_signature(
            lineage_payload={
                "synthetic":
                    True,
            },
            lineage_hash="0" * 64,
            key_id=object(),
            secret=SIGNING_SECRET,
        )


def test_empty_signing_secret_is_rejected(
) -> None:
    (
        acceptance_manifest,
        manifest_proof,
        authorization_decision,
        authorization_manifest,
        authorization_gate,
    ) = build_authorized_chain()

    with pytest.raises(
        ValueError,
        match="trial authorization signing secret is required",
    ):
        build_signed_trial_authorization_record(
            acceptance_manifest=acceptance_manifest,
            manifest_proof=manifest_proof,
            authorization_decision=authorization_decision,
            authorization_manifest=authorization_manifest,
            authorization_gate=authorization_gate,
            key_id=SIGNING_KEY_ID,
            secret=b"",
        )


def test_non_bytes_signing_secret_is_rejected(
) -> None:
    with pytest.raises(
        TypeError,
        match="secret must be bytes",
    ):
        compute_trial_authorization_signature(
            lineage_payload={
                "synthetic":
                    True,
            },
            lineage_hash="0" * 64,
            key_id=SIGNING_KEY_ID,
            secret="not-bytes",
        )


def test_unsupported_signature_algorithm_is_rejected(
) -> None:
    with pytest.raises(
        ValueError,
        match="unsupported trial authorization signature algorithm",
    ):
        compute_trial_authorization_signature(
            lineage_payload={
                "synthetic":
                    True,
            },
            lineage_hash="0" * 64,
            key_id=SIGNING_KEY_ID,
            secret=SIGNING_SECRET,
            signature_algorithm="sha1",
        )


def test_unsupported_signature_version_is_rejected(
) -> None:
    with pytest.raises(
        ValueError,
        match="unsupported trial authorization signature version",
    ):
        compute_trial_authorization_signature(
            lineage_payload={
                "synthetic":
                    True,
            },
            lineage_hash="0" * 64,
            key_id=SIGNING_KEY_ID,
            secret=SIGNING_SECRET,
            signature_version="999.0.0",
        )


def test_record_is_immutable(
) -> None:
    (
        record,
        _,
        _,
        _,
        _,
        _,
    ) = build_record()

    with pytest.raises(
        FrozenInstanceError
    ):
        record.decision_id = "changed"


def test_public_projection_preserves_authority_boundaries(
) -> None:
    (
        record,
        _,
        _,
        _,
        _,
        _,
    ) = build_record()

    payload = record.to_dict()

    assert (
        payload["record_type"]
        == GOVERNANCE_RELEASE_TRIAL_AUTHORIZATION_RECORD_TYPE
    )

    assert (
        payload["version"]
        == GOVERNANCE_RELEASE_TRIAL_AUTHORIZATION_RECORD_VERSION
    )

    assert payload["trial_authorized"] is True

    boundaries = payload[
        "boundaries"
    ]

    expected_boundaries = {
        "record_is_evidence",
        "record_binds_existing_trial_authorization",
        "record_does_not_create_trial_authorization",
        "signature_proves_integrity_not_human_identity",
        "signing_key_identity_is_not_actor_identity",
        "record_is_not_deployment_execution",
        "record_is_not_paid_assessment_execution",
        "record_is_not_pa001_paid_work_authorization",
        "record_is_not_delivery_approval",
        "record_is_not_production_activation",
        "record_is_not_intervention_authority",
        "record_does_not_invoke_pa014_or_pa015",
    }

    assert set(
        boundaries
    ) == expected_boundaries

    assert all(
        value is True
        for value in boundaries.values()
    )