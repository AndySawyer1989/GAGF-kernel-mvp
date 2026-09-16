from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path

from backend.app.gagf.governance_customer_trial_client_receipt_observation import (
    CustomerTrialClientReceiptObservation,
)
from backend.app.gagf.scientific_authority_guard import (
    canonical_json,
    sha256_hex,
)


CUSTOMER_TRIAL_CLIENT_RECEIPT_OBSERVATION_RECEIPT_ID = (
    "governance-customer-trial-client-receipt-observation-receipt"
)

CUSTOMER_TRIAL_CLIENT_RECEIPT_OBSERVATION_RECEIPT_VERSION = "0.1.0"

CUSTOMER_TRIAL_CLIENT_RECEIPT_OBSERVATION_RECEIPT_SCHEMA_VERSION = "1.0.0"


class CustomerTrialClientReceiptObservationReceiptError(
    RuntimeError
):
    """Base client-receipt observation receipt error."""


class CustomerTrialClientReceiptObservationReceiptConflictError(
    CustomerTrialClientReceiptObservationReceiptError
):
    """Raised when persisted client-receipt lineage conflicts."""


@dataclass(
    frozen=True,
    slots=True,
)
class CustomerTrialClientReceiptObservationReceipt:
    tenant_id: str
    client_id: str
    engagement_id: str
    assessment_id: str
    hierarchy_key: str

    observation_status: str

    delivery_observation_receipt_hash: str
    delivery_observation_hash: str

    report_id: str

    acknowledgment_id: str
    acknowledged_by: str
    acknowledged_at: str
    acknowledgment_method: str
    acknowledgment_reference: str
    acknowledgment_status: str

    acknowledgment_artifact_id: str
    acknowledgment_artifact_hash: str
    acknowledgment_sequence_number: int
    acknowledgment_chain_hash: str

    observation_hash: str
    receipt_hash: str

    receipt_type: str = (
        CUSTOMER_TRIAL_CLIENT_RECEIPT_OBSERVATION_RECEIPT_ID
    )

    version: str = (
        CUSTOMER_TRIAL_CLIENT_RECEIPT_OBSERVATION_RECEIPT_VERSION
    )

    schema_version: str = (
        CUSTOMER_TRIAL_CLIENT_RECEIPT_OBSERVATION_RECEIPT_SCHEMA_VERSION
    )

    @property
    def boundaries(
        self,
    ) -> dict[str, bool]:
        return {
            "receipt_is_audit_evidence_only":
                True,
            "receipt_is_not_client_response":
                True,
            "receipt_is_not_findings_acceptance":
                True,
            "receipt_is_not_recommendation_acceptance":
                True,
            "receipt_is_not_client_satisfaction":
                True,
            "receipt_is_not_closeout_authority":
                True,
            "receipt_is_not_intervention_authority":
                True,
            "receipt_is_not_execution_authority":
                True,
            "receipt_is_not_roi_verification":
                True,
            "receipt_is_not_customer_outcome_verification":
                True,
            "pa006_remains_client_receipt_authority":
                True,
            "pa012_remains_lifecycle_persistence_authority":
                True,
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

            "controlled_trial_lineage": {
                "delivery_observation_receipt_hash": (
                    self.delivery_observation_receipt_hash
                ),
                "delivery_observation_hash": (
                    self.delivery_observation_hash
                ),
            },

            "report": {
                "report_id":
                    self.report_id,
            },

            "client_receipt": {
                "acknowledgment_id":
                    self.acknowledgment_id,
                "acknowledged_by":
                    self.acknowledged_by,
                "acknowledged_at":
                    self.acknowledged_at,
                "acknowledgment_method":
                    self.acknowledgment_method,
                "acknowledgment_reference":
                    self.acknowledgment_reference,
                "acknowledgment_status":
                    self.acknowledgment_status,
            },

            "persistence_lineage": {
                "acknowledgment_artifact_id":
                    self.acknowledgment_artifact_id,
                "acknowledgment_artifact_hash":
                    self.acknowledgment_artifact_hash,
                "acknowledgment_sequence_number":
                    self.acknowledgment_sequence_number,
                "acknowledgment_chain_hash":
                    self.acknowledgment_chain_hash,
                "repository_chain_valid":
                    True,
            },

            "observation_hash":
                self.observation_hash,
            "receipt_hash":
                self.receipt_hash,

            "boundaries":
                self.boundaries,
        }


class GovernanceCustomerTrialClientReceiptObservationReceiptStore:
    TABLE_NAME = (
        "governance_customer_trial_client_receipt_observation_receipts"
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

                    delivery_observation_receipt_hash TEXT NOT NULL,
                    delivery_observation_hash TEXT NOT NULL,

                    report_id TEXT NOT NULL,

                    acknowledgment_id TEXT NOT NULL,
                    acknowledged_by TEXT NOT NULL,
                    acknowledged_at TEXT NOT NULL,
                    acknowledgment_method TEXT NOT NULL,
                    acknowledgment_reference TEXT NOT NULL,
                    acknowledgment_status TEXT NOT NULL,

                    acknowledgment_artifact_id TEXT NOT NULL,
                    acknowledgment_artifact_hash TEXT NOT NULL,
                    acknowledgment_sequence_number INTEGER NOT NULL,
                    acknowledgment_chain_hash TEXT NOT NULL,

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
            CustomerTrialClientReceiptObservation,
    ) -> CustomerTrialClientReceiptObservationReceipt:
        observation_hash = sha256_hex(
            canonical_json(
                observation.to_dict()
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

            "delivery_observation_receipt_hash": (
                observation
                .delivery_observation_receipt_hash
            ),
            "delivery_observation_hash": (
                observation
                .delivery_observation_hash
            ),

            "report_id":
                observation.report_id,

            "acknowledgment_id":
                observation.acknowledgment_id,
            "acknowledged_by":
                observation.acknowledged_by,
            "acknowledged_at":
                observation.acknowledged_at,
            "acknowledgment_method":
                observation.acknowledgment_method,
            "acknowledgment_reference":
                observation.acknowledgment_reference,
            "acknowledgment_status":
                observation.acknowledgment_status,

            "acknowledgment_artifact_id":
                observation.acknowledgment_artifact_id,
            "acknowledgment_artifact_hash":
                observation.acknowledgment_artifact_hash,
            "acknowledgment_sequence_number":
                observation.acknowledgment_sequence_number,
            "acknowledgment_chain_hash":
                observation.acknowledgment_chain_hash,

            "observation_hash":
                observation_hash,

            "schema_version": (
                CUSTOMER_TRIAL_CLIENT_RECEIPT_OBSERVATION_RECEIPT_SCHEMA_VERSION
            ),
        }

        receipt_hash = sha256_hex(
            canonical_json(
                receipt_payload
            )
        )

        return (
            CustomerTrialClientReceiptObservationReceipt(
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

                delivery_observation_receipt_hash=(
                    observation
                    .delivery_observation_receipt_hash
                ),
                delivery_observation_hash=(
                    observation
                    .delivery_observation_hash
                ),

                report_id=
                    observation.report_id,

                acknowledgment_id=
                    observation.acknowledgment_id,
                acknowledged_by=
                    observation.acknowledged_by,
                acknowledged_at=
                    observation.acknowledged_at,
                acknowledgment_method=
                    observation.acknowledgment_method,
                acknowledgment_reference=
                    observation.acknowledgment_reference,
                acknowledgment_status=
                    observation.acknowledgment_status,

                acknowledgment_artifact_id=(
                    observation.acknowledgment_artifact_id
                ),
                acknowledgment_artifact_hash=(
                    observation.acknowledgment_artifact_hash
                ),
                acknowledgment_sequence_number=(
                    observation.acknowledgment_sequence_number
                ),
                acknowledgment_chain_hash=(
                    observation.acknowledgment_chain_hash
                ),

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
            CustomerTrialClientReceiptObservation,
    ) -> CustomerTrialClientReceiptObservationReceipt:
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
                CustomerTrialClientReceiptObservationReceiptConflictError(
                    "controlled-trial client receipt observation "
                    "already exists with different lineage"
                )
            )

        with sqlite3.connect(
            self.database_path
        ) as connection:
            connection.execute(
                f"""
                INSERT INTO {self.TABLE_NAME}
                (
                    tenant_id,
                    client_id,
                    engagement_id,
                    assessment_id,

                    hierarchy_key,
                    observation_status,

                    delivery_observation_receipt_hash,
                    delivery_observation_hash,

                    report_id,

                    acknowledgment_id,
                    acknowledged_by,
                    acknowledged_at,
                    acknowledgment_method,
                    acknowledgment_reference,
                    acknowledgment_status,

                    acknowledgment_artifact_id,
                    acknowledgment_artifact_hash,
                    acknowledgment_sequence_number,
                    acknowledgment_chain_hash,

                    observation_hash,
                    receipt_hash,

                    schema_version
                )
                VALUES
                (
                    ?, ?, ?, ?,
                    ?, ?,
                    ?, ?,
                    ?,
                    ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?,
                    ?, ?,
                    ?
                )
                """,
                (
                    receipt.tenant_id,
                    receipt.client_id,
                    receipt.engagement_id,
                    receipt.assessment_id,

                    receipt.hierarchy_key,
                    receipt.observation_status,

                    receipt.delivery_observation_receipt_hash,
                    receipt.delivery_observation_hash,

                    receipt.report_id,

                    receipt.acknowledgment_id,
                    receipt.acknowledged_by,
                    receipt.acknowledged_at,
                    receipt.acknowledgment_method,
                    receipt.acknowledgment_reference,
                    receipt.acknowledgment_status,

                    receipt.acknowledgment_artifact_id,
                    receipt.acknowledgment_artifact_hash,
                    receipt.acknowledgment_sequence_number,
                    receipt.acknowledgment_chain_hash,

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
    ) -> (
        CustomerTrialClientReceiptObservationReceipt
        | None
    ):
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

                    delivery_observation_receipt_hash,
                    delivery_observation_hash,

                    report_id,

                    acknowledgment_id,
                    acknowledged_by,
                    acknowledged_at,
                    acknowledgment_method,
                    acknowledgment_reference,
                    acknowledgment_status,

                    acknowledgment_artifact_id,
                    acknowledgment_artifact_hash,
                    acknowledgment_sequence_number,
                    acknowledgment_chain_hash,

                    observation_hash,
                    receipt_hash,

                    schema_version

                FROM {self.TABLE_NAME}

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
            CustomerTrialClientReceiptObservationReceipt(
                tenant_id=row[0],
                client_id=row[1],
                engagement_id=row[2],
                assessment_id=row[3],

                hierarchy_key=row[4],
                observation_status=row[5],

                delivery_observation_receipt_hash=row[6],
                delivery_observation_hash=row[7],

                report_id=row[8],

                acknowledgment_id=row[9],
                acknowledged_by=row[10],
                acknowledged_at=row[11],
                acknowledgment_method=row[12],
                acknowledgment_reference=row[13],
                acknowledgment_status=row[14],

                acknowledgment_artifact_id=row[15],
                acknowledgment_artifact_hash=row[16],
                acknowledgment_sequence_number=row[17],
                acknowledgment_chain_hash=row[18],

                observation_hash=row[19],
                receipt_hash=row[20],

                schema_version=row[21],
            )
        )