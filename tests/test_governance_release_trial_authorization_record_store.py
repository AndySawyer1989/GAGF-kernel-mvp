import json
import sqlite3
from dataclasses import replace
from pathlib import Path

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
    GovernanceReleaseTrialAuthorizationRecord,
    build_signed_trial_authorization_record,
    verify_trial_authorization_record,
)
from backend.app.gagf.governance_release_trial_authorization_record_store import (
    GOVERNANCE_RELEASE_TRIAL_AUTHORIZATION_RECORD_TABLE,
    GovernanceReleaseTrialAuthorizationRecordConflictError,
    GovernanceReleaseTrialAuthorizationRecordIntegrityError,
    GovernanceReleaseTrialAuthorizationRecordStore,
)


SIGNING_KEY_ID = "paid-trial-release-key-001"
SIGNING_SECRET = b"synthetic-paid-trial-release-secret"


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
    decided_at: str = "2026-10-10T18:00:00Z",
) -> GovernanceReleaseTrialAuthorizationDecision:
    return evaluate_governance_release_trial_authorization_decision(
        acceptance_manifest=acceptance_manifest,
        manifest_proof=manifest_proof,
        decision_id=decision_id,
        decided_by=decided_by,
        decided_at=decided_at,
        decision=TRIAL_AUTHORIZATION_DECISION_AUTHORIZE,
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


def build_record(
    *,
    decision_id: str = "trial-auth-001",
    decided_by: str = "release-operator",
    decided_at: str = "2026-10-10T18:00:00Z",
    release_environment: str = "paid_trial",
    backup_id: str = "backup-001",
) -> tuple[
    GovernanceReleaseTrialAuthorizationRecord,
    GovernanceReleaseAcceptanceManifest,
    GovernanceReleaseAcceptanceManifestProofResult,
    GovernanceReleaseTrialAuthorizationDecision,
    GovernanceReleaseTrialAuthorizationManifest,
    GovernanceReleaseTrialAuthorizationGateResult,
]:
    acceptance_manifest = (
        build_acceptance_manifest(
            release_environment=release_environment,
            backup_id=backup_id,
        )
    )

    manifest_proof = (
        build_manifest_proof(
            release_environment=release_environment,
            backup_id=backup_id,
        )
    )

    authorization_decision = (
        build_authorization_decision(
            acceptance_manifest=acceptance_manifest,
            manifest_proof=manifest_proof,
            decision_id=decision_id,
            decided_by=decided_by,
            decided_at=decided_at,
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


def build_store(
    tmp_path: Path,
) -> GovernanceReleaseTrialAuthorizationRecordStore:
    return GovernanceReleaseTrialAuthorizationRecordStore(
        tmp_path / "trial_authorization.sqlite3"
    )


def test_append_and_get_round_trip(
    tmp_path: Path,
) -> None:
    store = build_store(
        tmp_path
    )

    record, *_ = build_record()

    stored = store.append(
        record
    )

    reread = store.get(
        decision_id=record.decision_id
    )

    assert stored == record
    assert reread == record


def test_append_is_idempotent_for_identical_record(
    tmp_path: Path,
) -> None:
    store = build_store(
        tmp_path
    )

    record, *_ = build_record()

    first = store.append(
        record
    )

    second = store.append(
        record
    )

    assert first == record
    assert second == record

    records = store.list_records()

    assert len(records) == 1


def test_same_decision_id_with_different_record_conflicts(
    tmp_path: Path,
) -> None:
    store = build_store(
        tmp_path
    )

    original, *_ = build_record()

    conflicting = replace(
        original,
        decided_by="different-operator",
    )

    store.append(
        original
    )

    with pytest.raises(
        GovernanceReleaseTrialAuthorizationRecordConflictError
    ):
        store.append(
            conflicting
        )


def test_record_survives_store_restart(
    tmp_path: Path,
) -> None:
    database_path = (
        tmp_path
        / "trial_authorization.sqlite3"
    )

    first_store = (
        GovernanceReleaseTrialAuthorizationRecordStore(
            database_path
        )
    )

    record, *_ = build_record()

    first_store.append(
        record
    )

    second_store = (
        GovernanceReleaseTrialAuthorizationRecordStore(
            database_path
        )
    )

    reread = second_store.get(
        decision_id=record.decision_id
    )

    assert reread == record


def test_reread_record_still_verifies_cryptographically(
    tmp_path: Path,
) -> None:
    store = build_store(
        tmp_path
    )

    (
        record,
        acceptance_manifest,
        manifest_proof,
        authorization_decision,
        authorization_manifest,
        authorization_gate,
    ) = build_record()

    store.append(
        record
    )

    reread = store.get(
        decision_id=record.decision_id
    )

    assert verify_trial_authorization_record(
        record=reread,
        acceptance_manifest=acceptance_manifest,
        manifest_proof=manifest_proof,
        authorization_decision=authorization_decision,
        authorization_manifest=authorization_manifest,
        authorization_gate=authorization_gate,
        secret=SIGNING_SECRET,
    ) is True


def test_missing_record_raises_key_error(
    tmp_path: Path,
) -> None:
    store = build_store(
        tmp_path
    )

    with pytest.raises(
        KeyError
    ):
        store.get(
            decision_id="missing-decision"
        )


def test_get_optional_returns_none_when_missing(
    tmp_path: Path,
) -> None:
    store = build_store(
        tmp_path
    )

    assert (
        store.get_optional(
            decision_id="missing-decision"
        )
        is None
    )


def test_list_records_returns_newest_first(
    tmp_path: Path,
) -> None:
    store = build_store(
        tmp_path
    )

    first, *_ = build_record(
        decision_id="trial-auth-001",
        decided_at="2026-10-10T18:00:00Z",
    )

    second, *_ = build_record(
        decision_id="trial-auth-002",
        decided_at="2026-10-10T18:01:00Z",
    )

    store.append(
        first
    )

    store.append(
        second
    )

    records = store.list_records()

    assert [
        record.decision_id
        for record in records
    ] == [
        "trial-auth-002",
        "trial-auth-001",
    ]


def test_list_records_can_filter_environment(
    tmp_path: Path,
) -> None:
    store = build_store(
        tmp_path
    )

    paid_trial, *_ = build_record(
        decision_id="trial-auth-paid",
        release_environment="paid_trial",
    )

    prelive_record = replace(
        paid_trial,
        decision_id="trial-auth-prelive",
        release_environment="prelive",
    )

    store.append(
        paid_trial
    )

    store.append(
        prelive_record
    )

    records = store.list_records(
        release_environment="paid_trial"
    )

    assert [
        record.decision_id
        for record in records
    ] == [
        "trial-auth-paid",
    ]


def test_list_records_limit_is_applied(
    tmp_path: Path,
) -> None:
    store = build_store(
        tmp_path
    )

    for index in range(3):
        record, *_ = build_record(
            decision_id=(
                f"trial-auth-{index}"
            ),
            decided_at=(
                f"2026-10-10T18:0{index}:00Z"
            ),
        )

        store.append(
            record
        )

    records = store.list_records(
        limit=2
    )

    assert len(records) == 2


def test_invalid_record_type_is_rejected_before_insert(
    tmp_path: Path,
) -> None:
    store = build_store(
        tmp_path
    )

    record, *_ = build_record()

    invalid = replace(
        record,
        record_type="invalid-record-type",
    )

    with pytest.raises(
        GovernanceReleaseTrialAuthorizationRecordIntegrityError
    ):
        store.append(
            invalid
        )


def test_non_record_object_is_rejected(
    tmp_path: Path,
) -> None:
    store = build_store(
        tmp_path
    )

    with pytest.raises(
        TypeError
    ):
        store.append(
            object()
        )


def test_storage_hash_corruption_is_detected(
    tmp_path: Path,
) -> None:
    store = build_store(
        tmp_path
    )

    record, *_ = build_record()

    store.append(
        record
    )

    with sqlite3.connect(
        store.database_path
    ) as connection:
        connection.execute(
            f"""
            UPDATE
                {GOVERNANCE_RELEASE_TRIAL_AUTHORIZATION_RECORD_TABLE}
            SET
                storage_hash = ?
            WHERE
                decision_id = ?
            """,
            (
                "0" * 64,
                record.decision_id,
            ),
        )

        connection.commit()

    with pytest.raises(
        GovernanceReleaseTrialAuthorizationRecordIntegrityError,
        match="storage hash verification failed",
    ):
        store.get(
            decision_id=record.decision_id
        )


def test_record_json_corruption_is_detected(
    tmp_path: Path,
) -> None:
    store = build_store(
        tmp_path
    )

    record, *_ = build_record()

    store.append(
        record
    )

    with sqlite3.connect(
        store.database_path
    ) as connection:
        connection.execute(
            f"""
            UPDATE
                {GOVERNANCE_RELEASE_TRIAL_AUTHORIZATION_RECORD_TABLE}
            SET
                record_json = ?
            WHERE
                decision_id = ?
            """,
            (
                "{not-valid-json",
                record.decision_id,
            ),
        )

        connection.commit()

    with pytest.raises(
        GovernanceReleaseTrialAuthorizationRecordIntegrityError,
        match="record JSON is invalid",
    ):
        store.get(
            decision_id=record.decision_id
        )


def test_row_decision_id_tampering_is_detected(
    tmp_path: Path,
) -> None:
    store = build_store(
        tmp_path
    )

    record, *_ = build_record()

    store.append(
        record
    )

    with sqlite3.connect(
        store.database_path
    ) as connection:
        connection.execute(
            f"""
            UPDATE
                {GOVERNANCE_RELEASE_TRIAL_AUTHORIZATION_RECORD_TABLE}
            SET
                decided_by = ?
            WHERE
                decision_id = ?
            """,
            (
                "tampered-operator",
                record.decision_id,
            ),
        )

        connection.commit()

    with pytest.raises(
        GovernanceReleaseTrialAuthorizationRecordIntegrityError,
        match="row identity verification failed",
    ):
        store.get(
            decision_id=record.decision_id
        )


def test_record_json_identity_tampering_with_recomputed_storage_hash_is_detected(
    tmp_path: Path,
) -> None:
    store = build_store(
        tmp_path
    )

    record, *_ = build_record()

    store.append(
        record
    )

    with sqlite3.connect(
        store.database_path
    ) as connection:
        row = connection.execute(
            f"""
            SELECT
                record_json
            FROM
                {GOVERNANCE_RELEASE_TRIAL_AUTHORIZATION_RECORD_TABLE}
            WHERE
                decision_id = ?
            """,
            (
                record.decision_id,
            ),
        ).fetchone()

        payload = json.loads(
            row[0]
        )

        payload[
            "decided_by"
        ] = "tampered-operator"

        from backend.app.gagf.governance_release_trial_authorization_record import (
            sha256_json,
        )

        new_record_json = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )

        new_storage_hash = (
            sha256_json(
                payload
            )
        )

        connection.execute(
            f"""
            UPDATE
                {GOVERNANCE_RELEASE_TRIAL_AUTHORIZATION_RECORD_TABLE}
            SET
                record_json = ?,
                storage_hash = ?
            WHERE
                decision_id = ?
            """,
            (
                new_record_json,
                new_storage_hash,
                record.decision_id,
            ),
        )

        connection.commit()

    with pytest.raises(
        GovernanceReleaseTrialAuthorizationRecordIntegrityError,
        match="row identity verification failed",
    ):
        store.get(
            decision_id=record.decision_id
        )


def test_tampered_signature_survives_storage_hash_but_fails_hmac(
    tmp_path: Path,
) -> None:
    store = build_store(
        tmp_path
    )

    (
        record,
        acceptance_manifest,
        manifest_proof,
        authorization_decision,
        authorization_manifest,
        authorization_gate,
    ) = build_record()

    store.append(
        record
    )

    with sqlite3.connect(
        store.database_path
    ) as connection:
        row = connection.execute(
            f"""
            SELECT
                record_json
            FROM
                {GOVERNANCE_RELEASE_TRIAL_AUTHORIZATION_RECORD_TABLE}
            WHERE
                decision_id = ?
            """,
            (
                record.decision_id,
            ),
        ).fetchone()

        payload = json.loads(
            row[0]
        )

        payload[
            "signature"
        ] = "0" * 64

        from backend.app.gagf.governance_release_trial_authorization_record import (
            sha256_json,
        )

        record_json = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )

        storage_hash = (
            sha256_json(
                payload
            )
        )

        connection.execute(
            f"""
            UPDATE
                {GOVERNANCE_RELEASE_TRIAL_AUTHORIZATION_RECORD_TABLE}
            SET
                record_json = ?,
                storage_hash = ?
            WHERE
                decision_id = ?
            """,
            (
                record_json,
                storage_hash,
                record.decision_id,
            ),
        )

        connection.commit()

    reread = store.get(
        decision_id=record.decision_id
    )

    assert verify_trial_authorization_record(
        record=reread,
        acceptance_manifest=acceptance_manifest,
        manifest_proof=manifest_proof,
        authorization_decision=authorization_decision,
        authorization_manifest=authorization_manifest,
        authorization_gate=authorization_gate,
        secret=SIGNING_SECRET,
    ) is False


@pytest.mark.parametrize(
    "decision_id",
    (
        "",
        "   ",
    ),
)
def test_empty_decision_id_is_rejected(
    tmp_path: Path,
    decision_id: str,
) -> None:
    store = build_store(
        tmp_path
    )

    with pytest.raises(
        ValueError
    ):
        store.get(
            decision_id=decision_id
        )


def test_database_parent_directory_is_created(
    tmp_path: Path,
) -> None:
    database_path = (
        tmp_path
        / "nested"
        / "deeper"
        / "trial_authorization.sqlite3"
    )

    assert not (
        database_path.parent.exists()
    )

    GovernanceReleaseTrialAuthorizationRecordStore(
        database_path
    )

    assert (
        database_path.parent.exists()
    )

    assert (
        database_path.exists()
    )