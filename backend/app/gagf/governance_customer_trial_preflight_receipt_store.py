from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from backend.app.gagf.governance_customer_trial_preflight_decision import (
    CustomerTrialPreflightDecision,
)


CUSTOMER_TRIAL_PREFLIGHT_RECEIPT_STORE_ID = (
    "governance-customer-trial-preflight-receipt-store"
)

CUSTOMER_TRIAL_PREFLIGHT_RECEIPT_STORE_VERSION = "0.1.0"

CUSTOMER_TRIAL_PREFLIGHT_RECEIPT_SCHEMA_VERSION = "1.0.0"

TABLE_NAME = (
    "governance_customer_trial_preflight_receipts"
)


class CustomerTrialPreflightReceiptStoreError(
    RuntimeError
):
    """Raised when a preflight receipt cannot be stored safely."""


def _canonical_json(
    value: Any,
) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


def _sha256_text(
    value: str,
) -> str:
    return hashlib.sha256(
        value.encode("utf-8")
    ).hexdigest()


def _require_text(
    value: Any,
    field_name: str,
) -> str:
    if (
        not isinstance(value, str)
        or not value.strip()
    ):
        raise CustomerTrialPreflightReceiptStoreError(
            f"{field_name} must be non-empty"
        )

    return value.strip()


@dataclass(
    frozen=True,
    slots=True,
)
class CustomerTrialPreflightReceipt:
    tenant_id: str
    client_id: str
    engagement_id: str
    assessment_id: str

    decision_payload: dict[str, Any]
    decision_payload_hash: str
    receipt_hash: str

    schema_version: str = (
        CUSTOMER_TRIAL_PREFLIGHT_RECEIPT_SCHEMA_VERSION
    )

    @property
    def hierarchy_key(
        self,
    ) -> str:
        return "/".join(
            (
                self.tenant_id,
                self.client_id,
                self.engagement_id,
                self.assessment_id,
            )
        )

    def to_dict(
        self,
    ) -> dict[str, Any]:
        return {
            "store_type": (
                CUSTOMER_TRIAL_PREFLIGHT_RECEIPT_STORE_ID
            ),
            "version": (
                CUSTOMER_TRIAL_PREFLIGHT_RECEIPT_STORE_VERSION
            ),
            "schema_version": self.schema_version,
            "hierarchy_key": self.hierarchy_key,
            "decision_payload_hash": (
                self.decision_payload_hash
            ),
            "receipt_hash": self.receipt_hash,
            "decision_payload": self.decision_payload,
            "boundaries": {
                "receipt_is_not_execution_authority": True,
                "receipt_is_not_delivery_authority": True,
                "receipt_is_not_closeout_authority": True,
                "receipt_is_not_intervention_authority": True,
                "preflight_decision_remains_readiness_only": True,
            },
        }


class GovernanceCustomerTrialPreflightReceiptStore:
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

        self._initialize()

    def _connect(
        self,
    ) -> sqlite3.Connection:
        connection = sqlite3.connect(
            self.database_path
        )

        connection.row_factory = sqlite3.Row

        return connection

    def _initialize(
        self,
    ) -> None:
        with self._connect() as connection:
            connection.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
                    hierarchy_key TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL,
                    client_id TEXT NOT NULL,
                    engagement_id TEXT NOT NULL,
                    assessment_id TEXT NOT NULL,
                    decision_payload_json TEXT NOT NULL,
                    decision_payload_hash TEXT NOT NULL,
                    receipt_hash TEXT NOT NULL,
                    schema_version TEXT NOT NULL
                )
                """
            )

            connection.commit()

    def put(
        self,
        *,
        decision:
            CustomerTrialPreflightDecision,
    ) -> CustomerTrialPreflightReceipt:
        identity = decision.package_identity

        tenant_id = _require_text(
            identity.tenant_id,
            "tenant_id",
        )

        client_id = _require_text(
            identity.client_id,
            "client_id",
        )

        engagement_id = _require_text(
            identity.engagement_id,
            "engagement_id",
        )

        assessment_id = _require_text(
            identity.assessment_id,
            "assessment_id",
        )

        hierarchy_key = "/".join(
            (
                tenant_id,
                client_id,
                engagement_id,
                assessment_id,
            )
        )

        decision_payload_json = (
            _canonical_json(
                decision.to_dict()
            )
        )

        decision_payload_hash = (
            _sha256_text(
                decision_payload_json
            )
        )

        receipt_material = {
            "hierarchy_key": hierarchy_key,
            "decision_payload_hash": (
                decision_payload_hash
            ),
            "schema_version": (
                CUSTOMER_TRIAL_PREFLIGHT_RECEIPT_SCHEMA_VERSION
            ),
        }

        receipt_hash = _sha256_text(
            _canonical_json(
                receipt_material
            )
        )

        receipt = (
            CustomerTrialPreflightReceipt(
                tenant_id=tenant_id,
                client_id=client_id,
                engagement_id=engagement_id,
                assessment_id=assessment_id,
                decision_payload=json.loads(
                    decision_payload_json
                ),
                decision_payload_hash=(
                    decision_payload_hash
                ),
                receipt_hash=receipt_hash,
            )
        )

        existing = self.get(
            tenant_id=tenant_id,
            client_id=client_id,
            engagement_id=engagement_id,
            assessment_id=assessment_id,
        )

        if existing is not None:
            if (
                existing.receipt_hash
                != receipt.receipt_hash
            ):
                raise (
                    CustomerTrialPreflightReceiptStoreError(
                        "preflight receipt already exists "
                        "with different governed decision material"
                    )
                )

            return existing

        with self._connect() as connection:
            connection.execute(
                f"""
                INSERT INTO {TABLE_NAME} (
                    hierarchy_key,
                    tenant_id,
                    client_id,
                    engagement_id,
                    assessment_id,
                    decision_payload_json,
                    decision_payload_hash,
                    receipt_hash,
                    schema_version
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    hierarchy_key,
                    tenant_id,
                    client_id,
                    engagement_id,
                    assessment_id,
                    decision_payload_json,
                    decision_payload_hash,
                    receipt_hash,
                    CUSTOMER_TRIAL_PREFLIGHT_RECEIPT_SCHEMA_VERSION,
                ),
            )

            connection.commit()

        return receipt

    def get(
        self,
        *,
        tenant_id: str,
        client_id: str,
        engagement_id: str,
        assessment_id: str,
    ) -> CustomerTrialPreflightReceipt | None:
        tenant_id = _require_text(
            tenant_id,
            "tenant_id",
        )

        client_id = _require_text(
            client_id,
            "client_id",
        )

        engagement_id = _require_text(
            engagement_id,
            "engagement_id",
        )

        assessment_id = _require_text(
            assessment_id,
            "assessment_id",
        )

        hierarchy_key = "/".join(
            (
                tenant_id,
                client_id,
                engagement_id,
                assessment_id,
            )
        )

        with self._connect() as connection:
            row = connection.execute(
                f"""
                SELECT
                    hierarchy_key,
                    tenant_id,
                    client_id,
                    engagement_id,
                    assessment_id,
                    decision_payload_json,
                    decision_payload_hash,
                    receipt_hash,
                    schema_version
                FROM {TABLE_NAME}
                WHERE hierarchy_key = ?
                """,
                (
                    hierarchy_key,
                ),
            ).fetchone()

        if row is None:
            return None

        payload_json = row[
            "decision_payload_json"
        ]

        payload_hash = _sha256_text(
            payload_json
        )

        if (
            payload_hash
            != row["decision_payload_hash"]
        ):
            raise (
                CustomerTrialPreflightReceiptStoreError(
                    "preflight decision payload hash "
                    "verification failed"
                )
            )

        receipt_material = {
            "hierarchy_key": row[
                "hierarchy_key"
            ],
            "decision_payload_hash": (
                row["decision_payload_hash"]
            ),
            "schema_version": row[
                "schema_version"
            ],
        }

        expected_receipt_hash = (
            _sha256_text(
                _canonical_json(
                    receipt_material
                )
            )
        )

        if (
            expected_receipt_hash
            != row["receipt_hash"]
        ):
            raise (
                CustomerTrialPreflightReceiptStoreError(
                    "preflight receipt hash "
                    "verification failed"
                )
            )

        return CustomerTrialPreflightReceipt(
            tenant_id=row["tenant_id"],
            client_id=row["client_id"],
            engagement_id=row[
                "engagement_id"
            ],
            assessment_id=row[
                "assessment_id"
            ],
            decision_payload=json.loads(
                payload_json
            ),
            decision_payload_hash=row[
                "decision_payload_hash"
            ],
            receipt_hash=row[
                "receipt_hash"
            ],
            schema_version=row[
                "schema_version"
            ],
        )