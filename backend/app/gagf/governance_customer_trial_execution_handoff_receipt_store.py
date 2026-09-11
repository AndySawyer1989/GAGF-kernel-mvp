from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from backend.app.gagf.governance_customer_trial_execution_handoff_bridge import (
    CustomerTrialExecutionHandoffBridgeResult,
)


CUSTOMER_TRIAL_EXECUTION_HANDOFF_RECEIPT_STORE_ID = (
    "governance-customer-trial-execution-handoff-receipt-store"
)

CUSTOMER_TRIAL_EXECUTION_HANDOFF_RECEIPT_STORE_VERSION = "0.1.0"

CUSTOMER_TRIAL_EXECUTION_HANDOFF_RECEIPT_SCHEMA_VERSION = "1.0.0"

CUSTOMER_TRIAL_EXECUTION_HANDOFF_RECEIPT_TABLE = (
    "governance_customer_trial_execution_handoff_receipts"
)


class CustomerTrialExecutionHandoffReceiptStoreError(
    ValueError
):
    pass


class CustomerTrialExecutionHandoffReceiptConflictError(
    CustomerTrialExecutionHandoffReceiptStoreError
):
    pass


class CustomerTrialExecutionHandoffReceiptIntegrityError(
    CustomerTrialExecutionHandoffReceiptStoreError
):
    pass


def canonical_json(
    value: Any,
) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


def sha256_text(
    value: str,
) -> str:
    return hashlib.sha256(
        value.encode("utf-8")
    ).hexdigest()


@dataclass(
    frozen=True,
    slots=True,
)
class CustomerTrialExecutionHandoffReceipt:
    tenant_id: str
    client_id: str
    engagement_id: str
    assessment_id: str

    hierarchy_key: str

    preflight_receipt_hash: str
    preflight_decision_payload_hash: str
    preflight_package_hash: str

    contract_execution_event_hash: str
    paid_work_authorization_hash: str
    assessment_execution_request_hash: str
    handoff_hash: str

    lineage_hash: str
    receipt_hash: str

    schema_version: str = (
        CUSTOMER_TRIAL_EXECUTION_HANDOFF_RECEIPT_SCHEMA_VERSION
    )

    @property
    def boundaries(
        self,
    ) -> dict[str, bool]:
        return {
            "receipt_is_audit_evidence_only": True,
            "receipt_is_not_execution_authority": True,
            "receipt_is_not_paid_work_authority": True,
            "receipt_is_not_contract_authority": True,
            "receipt_is_not_assessment_execution": True,
            "receipt_is_not_intervention_authority": True,
        }

    def to_dict(
        self,
    ) -> dict[str, Any]:
        return {
            "store": (
                CUSTOMER_TRIAL_EXECUTION_HANDOFF_RECEIPT_STORE_ID
            ),
            "version": (
                CUSTOMER_TRIAL_EXECUTION_HANDOFF_RECEIPT_STORE_VERSION
            ),
            "schema_version":
                self.schema_version,
            "tenant_id":
                self.tenant_id,
            "client_id":
                self.client_id,
            "engagement_id":
                self.engagement_id,
            "assessment_id":
                self.assessment_id,
            "hierarchy_key":
                self.hierarchy_key,
            "preflight_lineage": {
                "receipt_hash":
                    self.preflight_receipt_hash,
                "decision_payload_hash":
                    self.preflight_decision_payload_hash,
                "package_hash":
                    self.preflight_package_hash,
            },
            "execution_handoff_lineage": {
                "contract_execution_event_hash":
                    self.contract_execution_event_hash,
                "paid_work_authorization_hash":
                    self.paid_work_authorization_hash,
                "assessment_execution_request_hash":
                    self.assessment_execution_request_hash,
                "handoff_hash":
                    self.handoff_hash,
            },
            "lineage_hash":
                self.lineage_hash,
            "receipt_hash":
                self.receipt_hash,
            "boundaries":
                self.boundaries,
        }


class GovernanceCustomerTrialExecutionHandoffReceiptStore:
    def __init__(
        self,
        database_path: str | Path,
    ) -> None:
        self.database_path = Path(
            database_path
        )

    def initialize(
        self,
    ) -> None:
        if self.database_path.parent:
            self.database_path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

        with sqlite3.connect(
            self.database_path
        ) as connection:
            connection.execute(
                f"""
                CREATE TABLE IF NOT EXISTS
                {CUSTOMER_TRIAL_EXECUTION_HANDOFF_RECEIPT_TABLE}
                (
                    hierarchy_key TEXT PRIMARY KEY,

                    tenant_id TEXT NOT NULL,
                    client_id TEXT NOT NULL,
                    engagement_id TEXT NOT NULL,
                    assessment_id TEXT NOT NULL,

                    preflight_receipt_hash TEXT NOT NULL,
                    preflight_decision_payload_hash TEXT NOT NULL,
                    preflight_package_hash TEXT NOT NULL,

                    contract_execution_event_hash TEXT NOT NULL,
                    paid_work_authorization_hash TEXT NOT NULL,
                    assessment_execution_request_hash TEXT NOT NULL,
                    handoff_hash TEXT NOT NULL,

                    lineage_hash TEXT NOT NULL,
                    receipt_hash TEXT NOT NULL,

                    schema_version TEXT NOT NULL
                )
                """
            )

    def build_receipt(
        self,
        *,
        bridge_result:
            CustomerTrialExecutionHandoffBridgeResult,
    ) -> CustomerTrialExecutionHandoffReceipt:
        handoff = bridge_result.handoff

        hierarchy_key = (
            bridge_result.hierarchy_key
        )

        parts = hierarchy_key.split(
            "/"
        )

        if len(parts) != 4:
            raise (
                CustomerTrialExecutionHandoffReceiptStoreError(
                    "customer trial execution handoff "
                    "hierarchy_key must contain exactly "
                    "tenant/client/engagement/assessment"
                )
            )

        (
            tenant_id,
            client_id,
            engagement_id,
            assessment_id,
        ) = parts

        if (
            handoff.hierarchy_key
            != hierarchy_key
        ):
            raise (
                CustomerTrialExecutionHandoffReceiptStoreError(
                    "execution handoff hierarchy does not "
                    "match customer trial bridge hierarchy"
                )
            )

        lineage_payload = {
            "tenant_id":
                tenant_id,
            "client_id":
                client_id,
            "engagement_id":
                engagement_id,
            "assessment_id":
                assessment_id,
            "hierarchy_key":
                hierarchy_key,
            "preflight_receipt_hash":
                bridge_result.preflight_receipt_hash,
            "preflight_decision_payload_hash":
                (
                    bridge_result
                    .preflight_decision_payload_hash
                ),
            "preflight_package_hash":
                bridge_result.preflight_package_hash,
            "contract_execution_event_hash":
                handoff.contract_execution_event_hash,
            "paid_work_authorization_hash":
                handoff.paid_work_authorization_hash,
            "assessment_execution_request_hash":
                handoff.assessment_execution_request_hash,
            "handoff_hash":
                handoff.handoff_hash,
        }

        lineage_hash = sha256_text(
            canonical_json(
                lineage_payload
            )
        )

        receipt_payload = {
            **lineage_payload,
            "lineage_hash":
                lineage_hash,
            "schema_version": (
                CUSTOMER_TRIAL_EXECUTION_HANDOFF_RECEIPT_SCHEMA_VERSION
            ),
        }

        receipt_hash = sha256_text(
            canonical_json(
                receipt_payload
            )
        )

        return (
            CustomerTrialExecutionHandoffReceipt(
                tenant_id=tenant_id,
                client_id=client_id,
                engagement_id=engagement_id,
                assessment_id=assessment_id,
                hierarchy_key=hierarchy_key,
                preflight_receipt_hash=(
                    bridge_result
                    .preflight_receipt_hash
                ),
                preflight_decision_payload_hash=(
                    bridge_result
                    .preflight_decision_payload_hash
                ),
                preflight_package_hash=(
                    bridge_result
                    .preflight_package_hash
                ),
                contract_execution_event_hash=(
                    handoff
                    .contract_execution_event_hash
                ),
                paid_work_authorization_hash=(
                    handoff
                    .paid_work_authorization_hash
                ),
                assessment_execution_request_hash=(
                    handoff
                    .assessment_execution_request_hash
                ),
                handoff_hash=(
                    handoff.handoff_hash
                ),
                lineage_hash=lineage_hash,
                receipt_hash=receipt_hash,
            )
        )

    def put(
        self,
        *,
        bridge_result:
            CustomerTrialExecutionHandoffBridgeResult,
    ) -> CustomerTrialExecutionHandoffReceipt:
        self.initialize()

        receipt = self.build_receipt(
            bridge_result=bridge_result
        )

        existing = self.get(
            tenant_id=receipt.tenant_id,
            client_id=receipt.client_id,
            engagement_id=receipt.engagement_id,
            assessment_id=receipt.assessment_id,
        )

        if existing is not None:
            if (
                existing.receipt_hash
                == receipt.receipt_hash
            ):
                return existing

            raise (
                CustomerTrialExecutionHandoffReceiptConflictError(
                    "existing customer trial execution "
                    "handoff receipt does not match "
                    "the supplied governed lineage"
                )
            )

        try:
            with sqlite3.connect(
                self.database_path
            ) as connection:
                connection.execute(
                    f"""
                    INSERT INTO
                    {CUSTOMER_TRIAL_EXECUTION_HANDOFF_RECEIPT_TABLE}
                    (
                        hierarchy_key,
                        tenant_id,
                        client_id,
                        engagement_id,
                        assessment_id,
                        preflight_receipt_hash,
                        preflight_decision_payload_hash,
                        preflight_package_hash,
                        contract_execution_event_hash,
                        paid_work_authorization_hash,
                        assessment_execution_request_hash,
                        handoff_hash,
                        lineage_hash,
                        receipt_hash,
                        schema_version
                    )
                    VALUES (
                        ?, ?, ?, ?, ?,
                        ?, ?, ?, ?,
                        ?, ?, ?, ?,
                        ?, ?
                    )
                    """,
                    (
                        receipt.hierarchy_key,
                        receipt.tenant_id,
                        receipt.client_id,
                        receipt.engagement_id,
                        receipt.assessment_id,
                        receipt.preflight_receipt_hash,
                        (
                            receipt
                            .preflight_decision_payload_hash
                        ),
                        receipt.preflight_package_hash,
                        (
                            receipt
                            .contract_execution_event_hash
                        ),
                        (
                            receipt
                            .paid_work_authorization_hash
                        ),
                        (
                            receipt
                            .assessment_execution_request_hash
                        ),
                        receipt.handoff_hash,
                        receipt.lineage_hash,
                        receipt.receipt_hash,
                        receipt.schema_version,
                    ),
                )

        except sqlite3.IntegrityError as exc:
            raise (
                CustomerTrialExecutionHandoffReceiptConflictError(
                    "customer trial execution handoff "
                    "receipt already exists"
                )
            ) from exc

        stored = self.get(
            tenant_id=receipt.tenant_id,
            client_id=receipt.client_id,
            engagement_id=receipt.engagement_id,
            assessment_id=receipt.assessment_id,
        )

        if stored is None:
            raise (
                CustomerTrialExecutionHandoffReceiptStoreError(
                    "customer trial execution handoff "
                    "receipt could not be restored"
                )
            )

        return stored

    def get(
        self,
        *,
        tenant_id: str,
        client_id: str,
        engagement_id: str,
        assessment_id: str,
    ) -> (
        CustomerTrialExecutionHandoffReceipt
        | None
    ):
        self.initialize()

        hierarchy_key = "/".join(
            (
                tenant_id,
                client_id,
                engagement_id,
                assessment_id,
            )
        )

        with sqlite3.connect(
            self.database_path
        ) as connection:
            row = connection.execute(
                f"""
                SELECT
                    hierarchy_key,
                    tenant_id,
                    client_id,
                    engagement_id,
                    assessment_id,
                    preflight_receipt_hash,
                    preflight_decision_payload_hash,
                    preflight_package_hash,
                    contract_execution_event_hash,
                    paid_work_authorization_hash,
                    assessment_execution_request_hash,
                    handoff_hash,
                    lineage_hash,
                    receipt_hash,
                    schema_version
                FROM
                    {CUSTOMER_TRIAL_EXECUTION_HANDOFF_RECEIPT_TABLE}
                WHERE hierarchy_key = ?
                """,
                (
                    hierarchy_key,
                ),
            ).fetchone()

        if row is None:
            return None

        receipt = (
            CustomerTrialExecutionHandoffReceipt(
                hierarchy_key=row[0],
                tenant_id=row[1],
                client_id=row[2],
                engagement_id=row[3],
                assessment_id=row[4],
                preflight_receipt_hash=row[5],
                preflight_decision_payload_hash=row[6],
                preflight_package_hash=row[7],
                contract_execution_event_hash=row[8],
                paid_work_authorization_hash=row[9],
                assessment_execution_request_hash=row[10],
                handoff_hash=row[11],
                lineage_hash=row[12],
                receipt_hash=row[13],
                schema_version=row[14],
            )
        )

        self._verify(
            receipt
        )

        return receipt

    def _verify(
        self,
        receipt:
            CustomerTrialExecutionHandoffReceipt,
    ) -> None:
        expected_hierarchy = "/".join(
            (
                receipt.tenant_id,
                receipt.client_id,
                receipt.engagement_id,
                receipt.assessment_id,
            )
        )

        if (
            receipt.hierarchy_key
            != expected_hierarchy
        ):
            raise (
                CustomerTrialExecutionHandoffReceiptIntegrityError(
                    "customer trial execution handoff "
                    "receipt hierarchy verification failed"
                )
            )

        lineage_payload = {
            "tenant_id":
                receipt.tenant_id,
            "client_id":
                receipt.client_id,
            "engagement_id":
                receipt.engagement_id,
            "assessment_id":
                receipt.assessment_id,
            "hierarchy_key":
                receipt.hierarchy_key,
            "preflight_receipt_hash":
                receipt.preflight_receipt_hash,
            "preflight_decision_payload_hash":
                (
                    receipt
                    .preflight_decision_payload_hash
                ),
            "preflight_package_hash":
                receipt.preflight_package_hash,
            "contract_execution_event_hash":
                receipt.contract_execution_event_hash,
            "paid_work_authorization_hash":
                receipt.paid_work_authorization_hash,
            "assessment_execution_request_hash":
                (
                    receipt
                    .assessment_execution_request_hash
                ),
            "handoff_hash":
                receipt.handoff_hash,
        }

        expected_lineage_hash = (
            sha256_text(
                canonical_json(
                    lineage_payload
                )
            )
        )

        if (
            expected_lineage_hash
            != receipt.lineage_hash
        ):
            raise (
                CustomerTrialExecutionHandoffReceiptIntegrityError(
                    "customer trial execution handoff "
                    "lineage hash verification failed"
                )
            )

        receipt_payload = {
            **lineage_payload,
            "lineage_hash":
                receipt.lineage_hash,
            "schema_version":
                receipt.schema_version,
        }

        expected_receipt_hash = (
            sha256_text(
                canonical_json(
                    receipt_payload
                )
            )
        )

        if (
            expected_receipt_hash
            != receipt.receipt_hash
        ):
            raise (
                CustomerTrialExecutionHandoffReceiptIntegrityError(
                    "customer trial execution handoff "
                    "receipt hash verification failed"
                )
            )