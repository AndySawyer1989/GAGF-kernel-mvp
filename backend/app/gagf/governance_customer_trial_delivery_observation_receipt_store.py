from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path

from backend.app.gagf.governance_customer_trial_delivery_observation import (
    CustomerTrialDeliveryObservation,
)
from backend.app.gagf.scientific_authority_guard import (
    canonical_json,
    sha256_hex,
)


CUSTOMER_TRIAL_DELIVERY_OBSERVATION_RECEIPT_ID = (
    "governance-customer-trial-delivery-observation-receipt"
)

CUSTOMER_TRIAL_DELIVERY_OBSERVATION_RECEIPT_VERSION = "0.1.0"

CUSTOMER_TRIAL_DELIVERY_OBSERVATION_RECEIPT_SCHEMA_VERSION = "1.0.0"


class CustomerTrialDeliveryObservationReceiptError(
    RuntimeError
):
    """Base delivery-observation receipt storage error."""


class CustomerTrialDeliveryObservationReceiptConflictError(
    CustomerTrialDeliveryObservationReceiptError
):
    """Raised when stored delivery-observation lineage conflicts."""


@dataclass(
    frozen=True,
    slots=True,
)
class CustomerTrialDeliveryObservationReceipt:
    tenant_id: str
    client_id: str
    engagement_id: str
    assessment_id: str
    hierarchy_key: str

    observation_status: str

    delivery_readiness_receipt_hash: str
    delivery_readiness_hash: str

    delivery_event_id: str
    delivery_event_hash: str

    report_id: str

    delivered_by: str
    delivered_at: str
    delivery_method: str
    delivery_reference: str

    human_delivery_confirmation_hash: str
    approved_delivery_snapshot_hash: str

    observation_hash: str
    receipt_hash: str

    receipt_type: str = (
        CUSTOMER_TRIAL_DELIVERY_OBSERVATION_RECEIPT_ID
    )

    version: str = (
        CUSTOMER_TRIAL_DELIVERY_OBSERVATION_RECEIPT_VERSION
    )

    schema_version: str = (
        CUSTOMER_TRIAL_DELIVERY_OBSERVATION_RECEIPT_SCHEMA_VERSION
    )

    @property
    def boundaries(
        self,
    ) -> dict[str, bool]:
        return {
            "receipt_is_audit_evidence_only":
                True,
            "receipt_is_not_delivery_approval":
                True,
            "receipt_is_not_approved_for_human_delivery":
                True,
            "receipt_is_not_delivery_authority":
                True,
            "receipt_is_not_client_receipt":
                True,
            "receipt_is_not_client_acknowledgment":
                True,
            "receipt_is_not_client_response":
                True,
            "receipt_is_not_client_acceptance":
                True,
            "receipt_is_not_closeout_authority":
                True,
            "receipt_is_not_intervention_authority":
                True,
            "pa005_remains_delivery_event_authority":
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
                "delivery_readiness_receipt_hash": (
                    self.delivery_readiness_receipt_hash
                ),
                "delivery_readiness_hash": (
                    self.delivery_readiness_hash
                ),
            },

            "delivery_lineage": {
                "delivery_event_id":
                    self.delivery_event_id,
                "delivery_event_hash":
                    self.delivery_event_hash,
                "human_delivery_confirmation_hash": (
                    self.human_delivery_confirmation_hash
                ),
                "approved_delivery_snapshot_hash": (
                    self.approved_delivery_snapshot_hash
                ),
            },

            "report": {
                "report_id":
                    self.report_id,
            },

            "delivery": {
                "delivered_by":
                    self.delivered_by,
                "delivered_at":
                    self.delivered_at,
                "delivery_method":
                    self.delivery_method,
                "delivery_reference":
                    self.delivery_reference,
            },

            "observation_hash":
                self.observation_hash,
            "receipt_hash":
                self.receipt_hash,

            "boundaries":
                self.boundaries,
        }


class GovernanceCustomerTrialDeliveryObservationReceiptStore:
    TABLE_NAME = (
        "governance_customer_trial_delivery_observation_receipts"
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

                    delivery_readiness_receipt_hash TEXT NOT NULL,
                    delivery_readiness_hash TEXT NOT NULL,

                    delivery_event_id TEXT NOT NULL,
                    delivery_event_hash TEXT NOT NULL,

                    report_id TEXT NOT NULL,

                    delivered_by TEXT NOT NULL,
                    delivered_at TEXT NOT NULL,
                    delivery_method TEXT NOT NULL,
                    delivery_reference TEXT NOT NULL,

                    human_delivery_confirmation_hash TEXT NOT NULL,
                    approved_delivery_snapshot_hash TEXT NOT NULL,

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
            CustomerTrialDeliveryObservation,
    ) -> CustomerTrialDeliveryObservationReceipt:
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

            "delivery_readiness_receipt_hash": (
                observation
                .delivery_readiness_receipt_hash
            ),
            "delivery_readiness_hash": (
                observation
                .delivery_readiness_hash
            ),

            "delivery_event_id":
                observation.delivery_event_id,
            "delivery_event_hash":
                observation.delivery_event_hash,

            "report_id":
                observation.report_id,

            "delivered_by":
                observation.delivered_by,
            "delivered_at":
                observation.delivered_at,
            "delivery_method":
                observation.delivery_method,
            "delivery_reference":
                observation.delivery_reference,

            "human_delivery_confirmation_hash": (
                observation
                .human_delivery_confirmation_hash
            ),
            "approved_delivery_snapshot_hash": (
                observation
                .approved_delivery_snapshot_hash
            ),

            "observation_hash":
                observation_hash,

            "schema_version": (
                CUSTOMER_TRIAL_DELIVERY_OBSERVATION_RECEIPT_SCHEMA_VERSION
            ),
        }

        receipt_hash = sha256_hex(
            canonical_json(
                receipt_payload
            )
        )

        return CustomerTrialDeliveryObservationReceipt(
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

            delivery_readiness_receipt_hash=(
                observation
                .delivery_readiness_receipt_hash
            ),
            delivery_readiness_hash=(
                observation
                .delivery_readiness_hash
            ),

            delivery_event_id=
                observation.delivery_event_id,
            delivery_event_hash=
                observation.delivery_event_hash,

            report_id=
                observation.report_id,

            delivered_by=
                observation.delivered_by,
            delivered_at=
                observation.delivered_at,
            delivery_method=
                observation.delivery_method,
            delivery_reference=
                observation.delivery_reference,

            human_delivery_confirmation_hash=(
                observation
                .human_delivery_confirmation_hash
            ),
            approved_delivery_snapshot_hash=(
                observation
                .approved_delivery_snapshot_hash
            ),

            observation_hash=
                observation_hash,
            receipt_hash=
                receipt_hash,
        )

    def put(
        self,
        *,
        observation:
            CustomerTrialDeliveryObservation,
    ) -> CustomerTrialDeliveryObservationReceipt:
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
                CustomerTrialDeliveryObservationReceiptConflictError(
                    "controlled-trial delivery observation "
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

                    delivery_readiness_receipt_hash,
                    delivery_readiness_hash,

                    delivery_event_id,
                    delivery_event_hash,

                    report_id,

                    delivered_by,
                    delivered_at,
                    delivery_method,
                    delivery_reference,

                    human_delivery_confirmation_hash,
                    approved_delivery_snapshot_hash,

                    observation_hash,
                    receipt_hash,

                    schema_version
                )
                VALUES
                (
                    ?, ?, ?, ?,
                    ?, ?,
                    ?, ?,
                    ?, ?,
                    ?,
                    ?, ?, ?, ?,
                    ?, ?,
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

                    receipt.delivery_readiness_receipt_hash,
                    receipt.delivery_readiness_hash,

                    receipt.delivery_event_id,
                    receipt.delivery_event_hash,

                    receipt.report_id,

                    receipt.delivered_by,
                    receipt.delivered_at,
                    receipt.delivery_method,
                    receipt.delivery_reference,

                    receipt.human_delivery_confirmation_hash,
                    receipt.approved_delivery_snapshot_hash,

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
    ) -> CustomerTrialDeliveryObservationReceipt | None:
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

                    delivery_readiness_receipt_hash,
                    delivery_readiness_hash,

                    delivery_event_id,
                    delivery_event_hash,

                    report_id,

                    delivered_by,
                    delivered_at,
                    delivery_method,
                    delivery_reference,

                    human_delivery_confirmation_hash,
                    approved_delivery_snapshot_hash,

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

        return CustomerTrialDeliveryObservationReceipt(
            tenant_id=row[0],
            client_id=row[1],
            engagement_id=row[2],
            assessment_id=row[3],

            hierarchy_key=row[4],
            observation_status=row[5],

            delivery_readiness_receipt_hash=row[6],
            delivery_readiness_hash=row[7],

            delivery_event_id=row[8],
            delivery_event_hash=row[9],

            report_id=row[10],

            delivered_by=row[11],
            delivered_at=row[12],
            delivery_method=row[13],
            delivery_reference=row[14],

            human_delivery_confirmation_hash=row[15],
            approved_delivery_snapshot_hash=row[16],

            observation_hash=row[17],
            receipt_hash=row[18],

            schema_version=row[19],
        )