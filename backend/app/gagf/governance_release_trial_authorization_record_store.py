from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from threading import RLock

from backend.app.gagf.governance_release_trial_authorization_record import (
    GOVERNANCE_RELEASE_TRIAL_AUTHORIZATION_RECORD_TYPE,
    GOVERNANCE_RELEASE_TRIAL_AUTHORIZATION_RECORD_VERSION,
    GOVERNANCE_RELEASE_TRIAL_AUTHORIZATION_SIGNATURE_ALGORITHM,
    GOVERNANCE_RELEASE_TRIAL_AUTHORIZATION_SIGNATURE_VERSION,
    GovernanceReleaseTrialAuthorizationRecord,
    sha256_json,
)


GOVERNANCE_RELEASE_TRIAL_AUTHORIZATION_RECORD_TABLE = (
    "governance_release_trial_authorization_records"
)

GOVERNANCE_RELEASE_TRIAL_AUTHORIZATION_RECORD_STORE_VERSION = (
    "0.1.0"
)


class GovernanceReleaseTrialAuthorizationRecordStoreError(
    ValueError
):
    pass


class GovernanceReleaseTrialAuthorizationRecordConflictError(
    GovernanceReleaseTrialAuthorizationRecordStoreError
):
    pass


class GovernanceReleaseTrialAuthorizationRecordIntegrityError(
    GovernanceReleaseTrialAuthorizationRecordStoreError
):
    pass


class GovernanceReleaseTrialAuthorizationRecordStore:
    def __init__(
        self,
        database_path: str | Path,
    ) -> None:
        self.database_path = Path(
            database_path
        )

        self.database_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        self._lock = RLock()

        self._initialize()

    def _connect(
        self,
    ) -> sqlite3.Connection:
        connection = sqlite3.connect(
            self.database_path
        )

        connection.row_factory = (
            sqlite3.Row
        )

        return connection

    def _initialize(
        self,
    ) -> None:
        with (
            self._lock,
            self._connect() as connection,
        ):
            connection.execute(
                f"""
                CREATE TABLE IF NOT EXISTS
                {GOVERNANCE_RELEASE_TRIAL_AUTHORIZATION_RECORD_TABLE}
                (
                    decision_id TEXT PRIMARY KEY,
                    release_environment TEXT NOT NULL,
                    backup_id TEXT NOT NULL,
                    decided_by TEXT NOT NULL,
                    decided_at TEXT NOT NULL,
                    record_json TEXT NOT NULL,
                    storage_hash TEXT NOT NULL,
                    record_type TEXT NOT NULL,
                    record_version TEXT NOT NULL,
                    signature_algorithm TEXT NOT NULL,
                    signature_version TEXT NOT NULL,
                    store_version TEXT NOT NULL
                )
                """
            )

            connection.execute(
                f"""
                CREATE INDEX IF NOT EXISTS
                idx_release_trial_authorization_environment_backup
                ON
                {GOVERNANCE_RELEASE_TRIAL_AUTHORIZATION_RECORD_TABLE}
                (
                    release_environment,
                    backup_id
                )
                """
            )

            connection.commit()

    def append(
        self,
        record:
            GovernanceReleaseTrialAuthorizationRecord,
    ) -> GovernanceReleaseTrialAuthorizationRecord:
        _require_record_type(
            record
        )

        _validate_record_metadata(
            record
        )

        record_payload = (
            record.to_dict()
        )

        record_json = json.dumps(
            record_payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )

        storage_hash = (
            sha256_json(
                record_payload
            )
        )

        existing = self.get_optional(
            decision_id=record.decision_id
        )

        if existing is not None:
            existing_hash = (
                sha256_json(
                    existing.to_dict()
                )
            )

            if (
                existing_hash
                == storage_hash
            ):
                return existing

            raise (
                GovernanceReleaseTrialAuthorizationRecordConflictError(
                    "trial authorization decision_id "
                    "already exists with different record"
                )
            )

        try:
            with (
                self._lock,
                self._connect() as connection,
            ):
                connection.execute(
                    f"""
                    INSERT INTO
                    {GOVERNANCE_RELEASE_TRIAL_AUTHORIZATION_RECORD_TABLE}
                    (
                        decision_id,
                        release_environment,
                        backup_id,
                        decided_by,
                        decided_at,
                        record_json,
                        storage_hash,
                        record_type,
                        record_version,
                        signature_algorithm,
                        signature_version,
                        store_version
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        record.decision_id,
                        record.release_environment,
                        record.backup_id,
                        record.decided_by,
                        record.decided_at,
                        record_json,
                        storage_hash,
                        record.record_type,
                        record.version,
                        record.signature_algorithm,
                        record.signature_version,
                        (
                            GOVERNANCE_RELEASE_TRIAL_AUTHORIZATION_RECORD_STORE_VERSION
                        ),
                    ),
                )

                connection.commit()

        except sqlite3.IntegrityError as exc:
            existing = self.get_optional(
                decision_id=record.decision_id
            )

            if existing is not None:
                existing_hash = (
                    sha256_json(
                        existing.to_dict()
                    )
                )

                if (
                    existing_hash
                    == storage_hash
                ):
                    return existing

            raise (
                GovernanceReleaseTrialAuthorizationRecordConflictError(
                    "trial authorization record insert conflict"
                )
            ) from exc

        stored = self.get(
            decision_id=record.decision_id
        )

        if (
            stored.to_dict()
            != record.to_dict()
        ):
            raise (
                GovernanceReleaseTrialAuthorizationRecordIntegrityError(
                    "stored trial authorization record "
                    "does not match appended record"
                )
            )

        return stored

    def get(
        self,
        *,
        decision_id: str,
    ) -> GovernanceReleaseTrialAuthorizationRecord:
        normalized_decision_id = (
            _normalize_required_text(
                name="decision_id",
                value=decision_id,
            )
        )

        with (
            self._lock,
            self._connect() as connection,
        ):
            row = connection.execute(
                f"""
                SELECT
                    decision_id,
                    release_environment,
                    backup_id,
                    decided_by,
                    decided_at,
                    record_json,
                    storage_hash,
                    record_type,
                    record_version,
                    signature_algorithm,
                    signature_version,
                    store_version
                FROM
                    {GOVERNANCE_RELEASE_TRIAL_AUTHORIZATION_RECORD_TABLE}
                WHERE
                    decision_id = ?
                """,
                (
                    normalized_decision_id,
                ),
            ).fetchone()

        if row is None:
            raise KeyError(
                normalized_decision_id
            )

        return self._row_to_record(
            row
        )

    def get_optional(
        self,
        *,
        decision_id: str,
    ) -> (
        GovernanceReleaseTrialAuthorizationRecord
        | None
    ):
        normalized_decision_id = (
            _normalize_required_text(
                name="decision_id",
                value=decision_id,
            )
        )

        with (
            self._lock,
            self._connect() as connection,
        ):
            row = connection.execute(
                f"""
                SELECT
                    decision_id,
                    release_environment,
                    backup_id,
                    decided_by,
                    decided_at,
                    record_json,
                    storage_hash,
                    record_type,
                    record_version,
                    signature_algorithm,
                    signature_version,
                    store_version
                FROM
                    {GOVERNANCE_RELEASE_TRIAL_AUTHORIZATION_RECORD_TABLE}
                WHERE
                    decision_id = ?
                """,
                (
                    normalized_decision_id,
                ),
            ).fetchone()

        if row is None:
            return None

        return self._row_to_record(
            row
        )

    def list_records(
        self,
        *,
        release_environment: str | None = None,
        limit: int = 100,
    ) -> list[
        GovernanceReleaseTrialAuthorizationRecord
    ]:
        safe_limit = max(
            1,
            min(
                int(limit),
                500,
            ),
        )

        with (
            self._lock,
            self._connect() as connection,
        ):
            if release_environment is None:
                rows = connection.execute(
                    f"""
                    SELECT
                        decision_id,
                        release_environment,
                        backup_id,
                        decided_by,
                        decided_at,
                        record_json,
                        storage_hash,
                        record_type,
                        record_version,
                        signature_algorithm,
                        signature_version,
                        store_version
                    FROM
                        {GOVERNANCE_RELEASE_TRIAL_AUTHORIZATION_RECORD_TABLE}
                    ORDER BY
                        rowid DESC
                    LIMIT ?
                    """,
                    (
                        safe_limit,
                    ),
                ).fetchall()

            else:
                normalized_environment = (
                    _normalize_required_text(
                        name="release_environment",
                        value=release_environment,
                    )
                )

                rows = connection.execute(
                    f"""
                    SELECT
                        decision_id,
                        release_environment,
                        backup_id,
                        decided_by,
                        decided_at,
                        record_json,
                        storage_hash,
                        record_type,
                        record_version,
                        signature_algorithm,
                        signature_version,
                        store_version
                    FROM
                        {GOVERNANCE_RELEASE_TRIAL_AUTHORIZATION_RECORD_TABLE}
                    WHERE
                        release_environment = ?
                    ORDER BY
                        rowid DESC
                    LIMIT ?
                    """,
                    (
                        normalized_environment,
                        safe_limit,
                    ),
                ).fetchall()

        return [
            self._row_to_record(
                row
            )
            for row in rows
        ]

    @staticmethod
    def _row_to_record(
        row: sqlite3.Row,
    ) -> GovernanceReleaseTrialAuthorizationRecord:
        if (
            row["store_version"]
            != GOVERNANCE_RELEASE_TRIAL_AUTHORIZATION_RECORD_STORE_VERSION
        ):
            raise (
                GovernanceReleaseTrialAuthorizationRecordIntegrityError(
                    "unsupported trial authorization "
                    "record store version"
                )
            )

        try:
            payload = json.loads(
                row["record_json"]
            )

        except (
            TypeError,
            json.JSONDecodeError,
        ) as exc:
            raise (
                GovernanceReleaseTrialAuthorizationRecordIntegrityError(
                    "trial authorization record JSON "
                    "is invalid"
                )
            ) from exc

        if not isinstance(
            payload,
            dict,
        ):
            raise (
                GovernanceReleaseTrialAuthorizationRecordIntegrityError(
                    "trial authorization record JSON "
                    "must be an object"
                )
            )

        expected_storage_hash = (
            sha256_json(
                payload
            )
        )

        if (
            expected_storage_hash
            != row["storage_hash"]
        ):
            raise (
                GovernanceReleaseTrialAuthorizationRecordIntegrityError(
                    "trial authorization record "
                    "storage hash verification failed"
                )
            )

        _require_payload_metadata(
            payload
        )

        expected_row_identity = {
            "decision_id":
                payload.get(
                    "decision_id"
                ),
            "release_environment":
                payload.get(
                    "release_environment"
                ),
            "backup_id":
                payload.get(
                    "backup_id"
                ),
            "decided_by":
                payload.get(
                    "decided_by"
                ),
            "decided_at":
                payload.get(
                    "decided_at"
                ),
            "record_type":
                payload.get(
                    "record_type"
                ),
            "record_version":
                payload.get(
                    "version"
                ),
            "signature_algorithm":
                payload.get(
                    "signature_algorithm"
                ),
            "signature_version":
                payload.get(
                    "signature_version"
                ),
        }

        actual_row_identity = {
            "decision_id":
                row["decision_id"],
            "release_environment":
                row[
                    "release_environment"
                ],
            "backup_id":
                row[
                    "backup_id"
                ],
            "decided_by":
                row[
                    "decided_by"
                ],
            "decided_at":
                row[
                    "decided_at"
                ],
            "record_type":
                row[
                    "record_type"
                ],
            "record_version":
                row[
                    "record_version"
                ],
            "signature_algorithm":
                row[
                    "signature_algorithm"
                ],
            "signature_version":
                row[
                    "signature_version"
                ],
        }

        if (
            actual_row_identity
            != expected_row_identity
        ):
            raise (
                GovernanceReleaseTrialAuthorizationRecordIntegrityError(
                    "trial authorization record "
                    "row identity verification failed"
                )
            )

        try:
            return (
                GovernanceReleaseTrialAuthorizationRecord(
                    release_environment=(
                        payload[
                            "release_environment"
                        ]
                    ),
                    backup_id=(
                        payload[
                            "backup_id"
                        ]
                    ),
                    decision_id=(
                        payload[
                            "decision_id"
                        ]
                    ),
                    decided_by=(
                        payload[
                            "decided_by"
                        ]
                    ),
                    decided_at=(
                        payload[
                            "decided_at"
                        ]
                    ),
                    decision=(
                        payload[
                            "decision"
                        ]
                    ),
                    trial_authorized=(
                        payload[
                            "trial_authorized"
                        ]
                    ),
                    acceptance_manifest_hash=(
                        payload[
                            "acceptance_manifest_hash"
                        ]
                    ),
                    manifest_proof_hash=(
                        payload[
                            "manifest_proof_hash"
                        ]
                    ),
                    authorization_decision_hash=(
                        payload[
                            "authorization_decision_hash"
                        ]
                    ),
                    authorization_manifest_hash=(
                        payload[
                            "authorization_manifest_hash"
                        ]
                    ),
                    authorization_gate_hash=(
                        payload[
                            "authorization_gate_hash"
                        ]
                    ),
                    lineage_hash=(
                        payload[
                            "lineage_hash"
                        ]
                    ),
                    key_id=(
                        payload[
                            "key_id"
                        ]
                    ),
                    signature=(
                        payload[
                            "signature"
                        ]
                    ),
                    record_type=(
                        payload[
                            "record_type"
                        ]
                    ),
                    version=(
                        payload[
                            "version"
                        ]
                    ),
                    signature_algorithm=(
                        payload[
                            "signature_algorithm"
                        ]
                    ),
                    signature_version=(
                        payload[
                            "signature_version"
                        ]
                    ),
                )
            )

        except (
            KeyError,
            TypeError,
        ) as exc:
            raise (
                GovernanceReleaseTrialAuthorizationRecordIntegrityError(
                    "trial authorization record "
                    "payload is incomplete"
                )
            ) from exc


def _require_record_type(
    record: object,
) -> None:
    if not isinstance(
        record,
        GovernanceReleaseTrialAuthorizationRecord,
    ):
        raise TypeError(
            "record must be a "
            "GovernanceReleaseTrialAuthorizationRecord"
        )


def _validate_record_metadata(
    record:
        GovernanceReleaseTrialAuthorizationRecord,
) -> None:
    if (
        record.record_type
        != GOVERNANCE_RELEASE_TRIAL_AUTHORIZATION_RECORD_TYPE
    ):
        raise (
            GovernanceReleaseTrialAuthorizationRecordIntegrityError(
                "unsupported trial authorization record type"
            )
        )

    if (
        record.version
        != GOVERNANCE_RELEASE_TRIAL_AUTHORIZATION_RECORD_VERSION
    ):
        raise (
            GovernanceReleaseTrialAuthorizationRecordIntegrityError(
                "unsupported trial authorization record version"
            )
        )

    if (
        record.signature_algorithm
        != GOVERNANCE_RELEASE_TRIAL_AUTHORIZATION_SIGNATURE_ALGORITHM
    ):
        raise (
            GovernanceReleaseTrialAuthorizationRecordIntegrityError(
                "unsupported trial authorization signature algorithm"
            )
        )

    if (
        record.signature_version
        != GOVERNANCE_RELEASE_TRIAL_AUTHORIZATION_SIGNATURE_VERSION
    ):
        raise (
            GovernanceReleaseTrialAuthorizationRecordIntegrityError(
                "unsupported trial authorization signature version"
            )
        )

    _normalize_required_text(
        name="decision_id",
        value=record.decision_id,
    )

    _normalize_required_text(
        name="release_environment",
        value=record.release_environment,
    )

    _normalize_required_text(
        name="backup_id",
        value=record.backup_id,
    )

    _normalize_required_text(
        name="decided_by",
        value=record.decided_by,
    )

    _normalize_required_text(
        name="decided_at",
        value=record.decided_at,
    )


def _require_payload_metadata(
    payload: dict[str, object],
) -> None:
    if (
        payload.get(
            "record_type"
        )
        != GOVERNANCE_RELEASE_TRIAL_AUTHORIZATION_RECORD_TYPE
    ):
        raise (
            GovernanceReleaseTrialAuthorizationRecordIntegrityError(
                "stored trial authorization "
                "record type is invalid"
            )
        )

    if (
        payload.get(
            "version"
        )
        != GOVERNANCE_RELEASE_TRIAL_AUTHORIZATION_RECORD_VERSION
    ):
        raise (
            GovernanceReleaseTrialAuthorizationRecordIntegrityError(
                "stored trial authorization "
                "record version is invalid"
            )
        )

    if (
        payload.get(
            "signature_algorithm"
        )
        != GOVERNANCE_RELEASE_TRIAL_AUTHORIZATION_SIGNATURE_ALGORITHM
    ):
        raise (
            GovernanceReleaseTrialAuthorizationRecordIntegrityError(
                "stored trial authorization "
                "signature algorithm is invalid"
            )
        )

    if (
        payload.get(
            "signature_version"
        )
        != GOVERNANCE_RELEASE_TRIAL_AUTHORIZATION_SIGNATURE_VERSION
    ):
        raise (
            GovernanceReleaseTrialAuthorizationRecordIntegrityError(
                "stored trial authorization "
                "signature version is invalid"
            )
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