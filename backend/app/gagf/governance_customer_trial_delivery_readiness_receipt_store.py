from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path

from backend.app.gagf.governance_customer_trial_delivery_readiness import (
    CustomerTrialDeliveryReadiness,
)
from backend.app.gagf.scientific_authority_guard import (
    canonical_json,
    sha256_hex,
)


CUSTOMER_TRIAL_DELIVERY_READINESS_RECEIPT_ID = (
    "governance-customer-trial-delivery-readiness-receipt"
)

CUSTOMER_TRIAL_DELIVERY_READINESS_RECEIPT_VERSION = "0.1.0"

CUSTOMER_TRIAL_DELIVERY_READINESS_RECEIPT_SCHEMA_VERSION = "1.0.0"


class CustomerTrialDeliveryReadinessReceiptError(
    RuntimeError
):
    """Base error for controlled-trial delivery-readiness storage."""


class CustomerTrialDeliveryReadinessReceiptConflictError(
    CustomerTrialDeliveryReadinessReceiptError
):
    """Raised when stored delivery-readiness lineage conflicts."""


@dataclass(
    frozen=True,
    slots=True,
)
class CustomerTrialDeliveryReadinessReceipt:
    tenant_id: str
    client_id: str
    engagement_id: str
    assessment_id: str
    hierarchy_key: str

    readiness_status: str

    observation_receipt_hash: str
    observation_hash: str

    handoff_receipt_hash: str
    handoff_lineage_hash: str
    handoff_hash: str
    assessment_execution_request_hash: str

    execution_result_hash: str
    application_hash: str
    persistence_hash: str

    report_id: str
    report_package_hash: str

    execution_status_hash: str
    operator_result_hash: str
    operator_snapshot_hash: str

    delivery_readiness_status: str
    recovery_disposition: str
    artifact_count: int
    repository_chain_valid: bool

    readiness_hash: str
    receipt_hash: str

    receipt_type: str = (
        CUSTOMER_TRIAL_DELIVERY_READINESS_RECEIPT_ID
    )

    version: str = (
        CUSTOMER_TRIAL_DELIVERY_READINESS_RECEIPT_VERSION
    )

    schema_version: str = (
        CUSTOMER_TRIAL_DELIVERY_READINESS_RECEIPT_SCHEMA_VERSION
    )

    @property
    def boundaries(
        self,
    ) -> dict[str, bool]:
        return {
            "receipt_is_audit_evidence_only": True,
            "receipt_is_not_execution_authority": True,
            "receipt_is_not_recovery_authority": True,
            "receipt_is_not_delivery_approval": True,
            "receipt_is_not_approved_for_human_delivery": True,
            "receipt_is_not_delivery_authority": True,
            "receipt_is_not_client_receipt": True,
            "receipt_is_not_client_response": True,
            "receipt_is_not_closeout_authority": True,
            "receipt_is_not_intervention_authority": True,
            "pa003_remains_delivery_readiness_authority": True,
        }

    def to_dict(
        self,
    ) -> dict[str, object]:
        return {
            "receipt_type":
                self.receipt_type,
            "version":
                self.version,
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
            "readiness_status":
                self.readiness_status,
            "observation_receipt_hash":
                self.observation_receipt_hash,
            "observation_hash":
                self.observation_hash,
            "controlled_trial_lineage": {
                "handoff_receipt_hash":
                    self.handoff_receipt_hash,
                "handoff_lineage_hash":
                    self.handoff_lineage_hash,
                "handoff_hash":
                    self.handoff_hash,
                "assessment_execution_request_hash":
                    self.assessment_execution_request_hash,
            },
            "execution_lineage": {
                "execution_result_hash":
                    self.execution_result_hash,
                "application_hash":
                    self.application_hash,
                "persistence_hash":
                    self.persistence_hash,
            },
            "report": {
                "report_id":
                    self.report_id,
                "report_package_hash":
                    self.report_package_hash,
            },
            "commercial_readiness": {
                "execution_status_hash":
                    self.execution_status_hash,
                "operator_result_hash":
                    self.operator_result_hash,
                "operator_snapshot_hash":
                    self.operator_snapshot_hash,
                "delivery_readiness_status":
                    self.delivery_readiness_status,
                "recovery_disposition":
                    self.recovery_disposition,
                "artifact_count":
                    self.artifact_count,
                "repository_chain_valid":
                    self.repository_chain_valid,
            },
            "readiness_hash":
                self.readiness_hash,
            "receipt_hash":
                self.receipt_hash,
            "boundaries":
                self.boundaries,
        }


class GovernanceCustomerTrialDeliveryReadinessReceiptStore:
    TABLE_NAME = (
        "governance_customer_trial_delivery_readiness_receipts"
    )

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
        if (
            self.database_path.parent
            and not self.database_path.parent.exists()
        ):
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
                {self.TABLE_NAME}
                (
                    tenant_id TEXT NOT NULL,
                    client_id TEXT NOT NULL,
                    engagement_id TEXT NOT NULL,
                    assessment_id TEXT NOT NULL,

                    hierarchy_key TEXT NOT NULL,
                    readiness_status TEXT NOT NULL,

                    observation_receipt_hash TEXT NOT NULL,
                    observation_hash TEXT NOT NULL,

                    handoff_receipt_hash TEXT NOT NULL,
                    handoff_lineage_hash TEXT NOT NULL,
                    handoff_hash TEXT NOT NULL,
                    assessment_execution_request_hash TEXT NOT NULL,

                    execution_result_hash TEXT NOT NULL,
                    application_hash TEXT NOT NULL,
                    persistence_hash TEXT NOT NULL,

                    report_id TEXT NOT NULL,
                    report_package_hash TEXT NOT NULL,

                    execution_status_hash TEXT NOT NULL,
                    operator_result_hash TEXT NOT NULL,
                    operator_snapshot_hash TEXT NOT NULL,

                    delivery_readiness_status TEXT NOT NULL,
                    recovery_disposition TEXT NOT NULL,
                    artifact_count INTEGER NOT NULL,
                    repository_chain_valid INTEGER NOT NULL,

                    readiness_hash TEXT NOT NULL,
                    receipt_hash TEXT NOT NULL,

                    schema_version TEXT NOT NULL,

                    PRIMARY KEY
                    (
                        tenant_id,
                        client_id,
                        engagement_id,
                        assessment_id
                    )
                )
                """
            )

    def build_receipt(
        self,
        *,
        readiness: CustomerTrialDeliveryReadiness,
    ) -> CustomerTrialDeliveryReadinessReceipt:
        readiness_payload = (
            readiness.to_dict()
        )

        readiness_hash = sha256_hex(
            canonical_json(
                readiness_payload
            )
        )

        receipt_payload = {
            "tenant_id":
                readiness.tenant_id,
            "client_id":
                readiness.client_id,
            "engagement_id":
                readiness.engagement_id,
            "assessment_id":
                readiness.assessment_id,
            "hierarchy_key":
                readiness.hierarchy_key,
            "readiness_status":
                readiness.readiness_status,
            "observation_receipt_hash":
                readiness.observation_receipt_hash,
            "observation_hash":
                readiness.observation_hash,
            "handoff_receipt_hash":
                readiness.handoff_receipt_hash,
            "handoff_lineage_hash":
                readiness.handoff_lineage_hash,
            "handoff_hash":
                readiness.handoff_hash,
            "assessment_execution_request_hash":
                readiness.assessment_execution_request_hash,
            "execution_result_hash":
                readiness.execution_result_hash,
            "application_hash":
                readiness.application_hash,
            "persistence_hash":
                readiness.persistence_hash,
            "report_id":
                readiness.report_id,
            "report_package_hash":
                readiness.report_package_hash,
            "execution_status_hash":
                readiness.execution_status_hash,
            "operator_result_hash":
                readiness.operator_result_hash,
            "operator_snapshot_hash":
                readiness.operator_snapshot_hash,
            "delivery_readiness_status":
                readiness.delivery_readiness_status,
            "recovery_disposition":
                readiness.recovery_disposition,
            "artifact_count":
                readiness.artifact_count,
            "repository_chain_valid":
                readiness.repository_chain_valid,
            "readiness_hash":
                readiness_hash,
            "schema_version": (
                CUSTOMER_TRIAL_DELIVERY_READINESS_RECEIPT_SCHEMA_VERSION
            ),
        }

        receipt_hash = sha256_hex(
            canonical_json(
                receipt_payload
            )
        )

        return CustomerTrialDeliveryReadinessReceipt(
            tenant_id=
                readiness.tenant_id,
            client_id=
                readiness.client_id,
            engagement_id=
                readiness.engagement_id,
            assessment_id=
                readiness.assessment_id,
            hierarchy_key=
                readiness.hierarchy_key,
            readiness_status=
                readiness.readiness_status,
            observation_receipt_hash=
                readiness.observation_receipt_hash,
            observation_hash=
                readiness.observation_hash,
            handoff_receipt_hash=
                readiness.handoff_receipt_hash,
            handoff_lineage_hash=
                readiness.handoff_lineage_hash,
            handoff_hash=
                readiness.handoff_hash,
            assessment_execution_request_hash=
                readiness.assessment_execution_request_hash,
            execution_result_hash=
                readiness.execution_result_hash,
            application_hash=
                readiness.application_hash,
            persistence_hash=
                readiness.persistence_hash,
            report_id=
                readiness.report_id,
            report_package_hash=
                readiness.report_package_hash,
            execution_status_hash=
                readiness.execution_status_hash,
            operator_result_hash=
                readiness.operator_result_hash,
            operator_snapshot_hash=
                readiness.operator_snapshot_hash,
            delivery_readiness_status=
                readiness.delivery_readiness_status,
            recovery_disposition=
                readiness.recovery_disposition,
            artifact_count=
                readiness.artifact_count,
            repository_chain_valid=
                readiness.repository_chain_valid,
            readiness_hash=
                readiness_hash,
            receipt_hash=
                receipt_hash,
        )

    def put(
        self,
        *,
        readiness: CustomerTrialDeliveryReadiness,
    ) -> CustomerTrialDeliveryReadinessReceipt:
        self.initialize()

        receipt = self.build_receipt(
            readiness=readiness
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
                CustomerTrialDeliveryReadinessReceiptConflictError(
                    "existing customer-trial delivery-readiness "
                    "receipt does not match the supplied governed "
                    "readiness"
                )
            )

        with sqlite3.connect(
            self.database_path
        ) as connection:
            connection.execute(
                f"""
                INSERT INTO
                {self.TABLE_NAME}
                (
                    tenant_id,
                    client_id,
                    engagement_id,
                    assessment_id,

                    hierarchy_key,
                    readiness_status,

                    observation_receipt_hash,
                    observation_hash,

                    handoff_receipt_hash,
                    handoff_lineage_hash,
                    handoff_hash,
                    assessment_execution_request_hash,

                    execution_result_hash,
                    application_hash,
                    persistence_hash,

                    report_id,
                    report_package_hash,

                    execution_status_hash,
                    operator_result_hash,
                    operator_snapshot_hash,

                    delivery_readiness_status,
                    recovery_disposition,
                    artifact_count,
                    repository_chain_valid,

                    readiness_hash,
                    receipt_hash,
                    schema_version
                )
                VALUES
                (
                    ?, ?, ?, ?,
                    ?, ?,
                    ?, ?,
                    ?, ?, ?, ?,
                    ?, ?, ?,
                    ?, ?,
                    ?, ?, ?,
                    ?, ?, ?, ?,
                    ?, ?, ?
                )
                """,
                (
                    receipt.tenant_id,
                    receipt.client_id,
                    receipt.engagement_id,
                    receipt.assessment_id,

                    receipt.hierarchy_key,
                    receipt.readiness_status,

                    receipt.observation_receipt_hash,
                    receipt.observation_hash,

                    receipt.handoff_receipt_hash,
                    receipt.handoff_lineage_hash,
                    receipt.handoff_hash,
                    receipt.assessment_execution_request_hash,

                    receipt.execution_result_hash,
                    receipt.application_hash,
                    receipt.persistence_hash,

                    receipt.report_id,
                    receipt.report_package_hash,

                    receipt.execution_status_hash,
                    receipt.operator_result_hash,
                    receipt.operator_snapshot_hash,

                    receipt.delivery_readiness_status,
                    receipt.recovery_disposition,
                    receipt.artifact_count,
                    int(
                        receipt.repository_chain_valid
                    ),

                    receipt.readiness_hash,
                    receipt.receipt_hash,
                    receipt.schema_version,
                ),
            )

        return receipt

    def get(
        self,
        *,
        tenant_id: str,
        client_id: str,
        engagement_id: str,
        assessment_id: str,
    ) -> CustomerTrialDeliveryReadinessReceipt | None:
        self.initialize()

        with sqlite3.connect(
            self.database_path
        ) as connection:
            row = connection.execute(
                f"""
                SELECT
                    tenant_id,
                    client_id,
                    engagement_id,
                    assessment_id,

                    hierarchy_key,
                    readiness_status,

                    observation_receipt_hash,
                    observation_hash,

                    handoff_receipt_hash,
                    handoff_lineage_hash,
                    handoff_hash,
                    assessment_execution_request_hash,

                    execution_result_hash,
                    application_hash,
                    persistence_hash,

                    report_id,
                    report_package_hash,

                    execution_status_hash,
                    operator_result_hash,
                    operator_snapshot_hash,

                    delivery_readiness_status,
                    recovery_disposition,
                    artifact_count,
                    repository_chain_valid,

                    readiness_hash,
                    receipt_hash,
                    schema_version
                FROM
                    {self.TABLE_NAME}
                WHERE
                    tenant_id = ?
                    AND client_id = ?
                    AND engagement_id = ?
                    AND assessment_id = ?
                """,
                (
                    tenant_id,
                    client_id,
                    engagement_id,
                    assessment_id,
                ),
            ).fetchone()

        if row is None:
            return None

        return CustomerTrialDeliveryReadinessReceipt(
            tenant_id=row[0],
            client_id=row[1],
            engagement_id=row[2],
            assessment_id=row[3],

            hierarchy_key=row[4],
            readiness_status=row[5],

            observation_receipt_hash=row[6],
            observation_hash=row[7],

            handoff_receipt_hash=row[8],
            handoff_lineage_hash=row[9],
            handoff_hash=row[10],
            assessment_execution_request_hash=row[11],

            execution_result_hash=row[12],
            application_hash=row[13],
            persistence_hash=row[14],

            report_id=row[15],
            report_package_hash=row[16],

            execution_status_hash=row[17],
            operator_result_hash=row[18],
            operator_snapshot_hash=row[19],

            delivery_readiness_status=row[20],
            recovery_disposition=row[21],
            artifact_count=row[22],
            repository_chain_valid=bool(
                row[23]
            ),

            readiness_hash=row[24],
            receipt_hash=row[25],
            schema_version=row[26],
        )