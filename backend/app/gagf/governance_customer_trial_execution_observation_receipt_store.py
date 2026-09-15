from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path

from backend.app.gagf.governance_customer_trial_execution_observation import (
    CustomerTrialExecutionObservation,
)
from backend.app.gagf.scientific_authority_guard import (
    canonical_json,
    sha256_hex,
)


CUSTOMER_TRIAL_EXECUTION_OBSERVATION_RECEIPT_ID = (
    "governance-customer-trial-execution-observation-receipt"
)

CUSTOMER_TRIAL_EXECUTION_OBSERVATION_RECEIPT_VERSION = "0.1.0"
CUSTOMER_TRIAL_EXECUTION_OBSERVATION_RECEIPT_SCHEMA_VERSION = "1.0.0"


class CustomerTrialExecutionObservationReceiptError(
    RuntimeError
):
    """Base error for execution-observation receipt storage."""


class CustomerTrialExecutionObservationReceiptConflictError(
    CustomerTrialExecutionObservationReceiptError
):
    """Raised when stored observation lineage conflicts."""


@dataclass(frozen=True, slots=True)
class CustomerTrialExecutionObservationReceipt:
    tenant_id: str
    client_id: str
    engagement_id: str
    assessment_id: str
    hierarchy_key: str

    observation_status: str

    handoff_receipt_hash: str
    handoff_lineage_hash: str

    handoff_hash: str
    assessment_execution_request_hash: str
    execution_result_hash: str
    application_hash: str
    persistence_hash: str

    report_id: str
    report_package_hash: str

    observation_hash: str
    receipt_hash: str

    receipt_type: str = (
        CUSTOMER_TRIAL_EXECUTION_OBSERVATION_RECEIPT_ID
    )

    version: str = (
        CUSTOMER_TRIAL_EXECUTION_OBSERVATION_RECEIPT_VERSION
    )

    schema_version: str = (
        CUSTOMER_TRIAL_EXECUTION_OBSERVATION_RECEIPT_SCHEMA_VERSION
    )

    @property
    def boundaries(
        self,
    ) -> dict[str, bool]:
        return {
            "receipt_is_audit_evidence_only": True,
            "receipt_is_not_execution_authority": True,
            "receipt_is_not_recovery_authority": True,
            "receipt_is_not_delivery_authority": True,
            "receipt_is_not_closeout_authority": True,
            "receipt_is_not_intervention_authority": True,
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
            "observation_status":
                self.observation_status,
            "handoff_receipt_hash":
                self.handoff_receipt_hash,
            "handoff_lineage_hash":
                self.handoff_lineage_hash,
            "execution_lineage": {
                "handoff_hash":
                    self.handoff_hash,
                "assessment_execution_request_hash":
                    self.assessment_execution_request_hash,
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
            "observation_hash":
                self.observation_hash,
            "receipt_hash":
                self.receipt_hash,
            "boundaries":
                self.boundaries,
        }


class GovernanceCustomerTrialExecutionObservationReceiptStore:
    TABLE_NAME = (
        "governance_customer_trial_execution_observation_receipts"
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
                    observation_status TEXT NOT NULL,

                    handoff_receipt_hash TEXT NOT NULL,
                    handoff_lineage_hash TEXT NOT NULL,

                    handoff_hash TEXT NOT NULL,
                    assessment_execution_request_hash TEXT NOT NULL,
                    execution_result_hash TEXT NOT NULL,
                    application_hash TEXT NOT NULL,
                    persistence_hash TEXT NOT NULL,

                    report_id TEXT NOT NULL,
                    report_package_hash TEXT NOT NULL,

                    observation_hash TEXT NOT NULL,
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
        observation:
            CustomerTrialExecutionObservation,
    ) -> CustomerTrialExecutionObservationReceipt:
        observation_payload = (
            observation.to_dict()
        )

        observation_hash = sha256_hex(
            canonical_json(
                observation_payload
            )
        )

        receipt_payload = {
            "tenant_id":
                observation.tenant_id,
            "client_id":
                observation.client_id,
            "engagement_id":
                observation.engagement_id,
            "assessment_id":
                observation.assessment_id,
            "hierarchy_key":
                observation.hierarchy_key,
            "observation_status":
                observation.observation_status,
            "handoff_receipt_hash":
                observation.handoff_receipt_hash,
            "handoff_lineage_hash":
                observation.handoff_lineage_hash,
            "handoff_hash":
                observation.handoff_hash,
            "assessment_execution_request_hash": (
                observation
                .assessment_execution_request_hash
            ),
            "execution_result_hash":
                observation.execution_result_hash,
            "application_hash":
                observation.application_hash,
            "persistence_hash":
                observation.persistence_hash,
            "report_id":
                observation.report_id,
            "report_package_hash":
                observation.report_package_hash,
            "observation_hash":
                observation_hash,
            "schema_version": (
                CUSTOMER_TRIAL_EXECUTION_OBSERVATION_RECEIPT_SCHEMA_VERSION
            ),
        }

        receipt_hash = sha256_hex(
            canonical_json(
                receipt_payload
            )
        )

        return (
            CustomerTrialExecutionObservationReceipt(
                tenant_id=
                    observation.tenant_id,
                client_id=
                    observation.client_id,
                engagement_id=
                    observation.engagement_id,
                assessment_id=
                    observation.assessment_id,
                hierarchy_key=
                    observation.hierarchy_key,
                observation_status=
                    observation.observation_status,
                handoff_receipt_hash=
                    observation.handoff_receipt_hash,
                handoff_lineage_hash=
                    observation.handoff_lineage_hash,
                handoff_hash=
                    observation.handoff_hash,
                assessment_execution_request_hash=(
                    observation
                    .assessment_execution_request_hash
                ),
                execution_result_hash=
                    observation.execution_result_hash,
                application_hash=
                    observation.application_hash,
                persistence_hash=
                    observation.persistence_hash,
                report_id=
                    observation.report_id,
                report_package_hash=
                    observation.report_package_hash,
                observation_hash=
                    observation_hash,
                receipt_hash=
                    receipt_hash,
            )
        )

    def put(
        self,
        *,
        observation:
            CustomerTrialExecutionObservation,
    ) -> CustomerTrialExecutionObservationReceipt:
        self.initialize()

        receipt = self.build_receipt(
            observation=observation
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
                CustomerTrialExecutionObservationReceiptConflictError(
                    "existing customer-trial execution "
                    "observation receipt does not match "
                    "the supplied governed observation"
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
                    observation_status,

                    handoff_receipt_hash,
                    handoff_lineage_hash,

                    handoff_hash,
                    assessment_execution_request_hash,
                    execution_result_hash,
                    application_hash,
                    persistence_hash,

                    report_id,
                    report_package_hash,

                    observation_hash,
                    receipt_hash,
                    schema_version
                )
                VALUES
                (
                    ?, ?, ?, ?,
                    ?, ?,
                    ?, ?,
                    ?, ?, ?, ?, ?,
                    ?, ?,
                    ?, ?, ?
                )
                """,
                (
                    receipt.tenant_id,
                    receipt.client_id,
                    receipt.engagement_id,
                    receipt.assessment_id,

                    receipt.hierarchy_key,
                    receipt.observation_status,

                    receipt.handoff_receipt_hash,
                    receipt.handoff_lineage_hash,

                    receipt.handoff_hash,
                    receipt.assessment_execution_request_hash,
                    receipt.execution_result_hash,
                    receipt.application_hash,
                    receipt.persistence_hash,

                    receipt.report_id,
                    receipt.report_package_hash,

                    receipt.observation_hash,
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
    ) -> CustomerTrialExecutionObservationReceipt | None:
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
                    observation_status,

                    handoff_receipt_hash,
                    handoff_lineage_hash,

                    handoff_hash,
                    assessment_execution_request_hash,
                    execution_result_hash,
                    application_hash,
                    persistence_hash,

                    report_id,
                    report_package_hash,

                    observation_hash,
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

        return (
            CustomerTrialExecutionObservationReceipt(
                tenant_id=row[0],
                client_id=row[1],
                engagement_id=row[2],
                assessment_id=row[3],

                hierarchy_key=row[4],
                observation_status=row[5],

                handoff_receipt_hash=row[6],
                handoff_lineage_hash=row[7],

                handoff_hash=row[8],
                assessment_execution_request_hash=row[9],
                execution_result_hash=row[10],
                application_hash=row[11],
                persistence_hash=row[12],

                report_id=row[13],
                report_package_hash=row[14],

                observation_hash=row[15],
                receipt_hash=row[16],
                schema_version=row[17],
            )
        )