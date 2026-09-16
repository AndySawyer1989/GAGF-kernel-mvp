from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path

from backend.app.gagf.governance_customer_trial_client_response_observation import (
    CustomerTrialClientResponseObservation,
)
from backend.app.gagf.scientific_authority_guard import (
    canonical_json,
    sha256_hex,
)


CUSTOMER_TRIAL_CLIENT_RESPONSE_OBSERVATION_RECEIPT_ID = (
    "governance-customer-trial-client-response-observation-receipt"
)

CUSTOMER_TRIAL_CLIENT_RESPONSE_OBSERVATION_RECEIPT_VERSION = "0.1.0"

CUSTOMER_TRIAL_CLIENT_RESPONSE_OBSERVATION_RECEIPT_SCHEMA_VERSION = "1.0.0"


class CustomerTrialClientResponseObservationReceiptError(
    RuntimeError
):
    """Base controlled-trial client-response observation receipt error."""


class CustomerTrialClientResponseObservationReceiptConflictError(
    CustomerTrialClientResponseObservationReceiptError
):
    """Raised when persisted response-observation lineage conflicts."""


@dataclass(
    frozen=True,
    slots=True,
)
class CustomerTrialClientResponseObservationReceipt:
    tenant_id: str
    client_id: str
    engagement_id: str
    assessment_id: str
    hierarchy_key: str

    observation_status: str

    client_receipt_observation_receipt_hash: str
    client_receipt_observation_hash: str

    report_id: str

    response_id: str
    responded_by: str
    responded_at: str
    response_method: str
    response_reference: str

    findings_disposition: str
    recommendations_disposition: str
    response_note: str
    response_status: str

    observation_hash: str
    receipt_hash: str

    receipt_type: str = (
        CUSTOMER_TRIAL_CLIENT_RESPONSE_OBSERVATION_RECEIPT_ID
    )

    version: str = (
        CUSTOMER_TRIAL_CLIENT_RESPONSE_OBSERVATION_RECEIPT_VERSION
    )

    schema_version: str = (
        CUSTOMER_TRIAL_CLIENT_RESPONSE_OBSERVATION_RECEIPT_SCHEMA_VERSION
    )

    @property
    def boundaries(
        self,
    ) -> dict[str, bool]:
        return {
            "receipt_is_audit_evidence_only":
                True,
            "receipt_does_not_create_client_response":
                True,
            "receipt_does_not_validate_findings":
                True,
            "receipt_does_not_implement_recommendations":
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
            "pa007_remains_client_response_authority":
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
                "client_receipt_observation_receipt_hash": (
                    self.client_receipt_observation_receipt_hash
                ),
                "client_receipt_observation_hash": (
                    self.client_receipt_observation_hash
                ),
            },

            "report": {
                "report_id":
                    self.report_id,
            },

            "client_response": {
                "response_id":
                    self.response_id,
                "responded_by":
                    self.responded_by,
                "responded_at":
                    self.responded_at,
                "response_method":
                    self.response_method,
                "response_reference":
                    self.response_reference,
                "findings_disposition":
                    self.findings_disposition,
                "recommendations_disposition":
                    self.recommendations_disposition,
                "response_note":
                    self.response_note,
                "response_status":
                    self.response_status,
            },

            "observation_hash":
                self.observation_hash,
            "receipt_hash":
                self.receipt_hash,

            "boundaries":
                self.boundaries,
        }


class GovernanceCustomerTrialClientResponseObservationReceiptStore:
    TABLE_NAME = (
        "governance_customer_trial_client_response_observation_receipts"
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

                    client_receipt_observation_receipt_hash TEXT NOT NULL,
                    client_receipt_observation_hash TEXT NOT NULL,

                    report_id TEXT NOT NULL,

                    response_id TEXT NOT NULL,
                    responded_by TEXT NOT NULL,
                    responded_at TEXT NOT NULL,
                    response_method TEXT NOT NULL,
                    response_reference TEXT NOT NULL,

                    findings_disposition TEXT NOT NULL,
                    recommendations_disposition TEXT NOT NULL,
                    response_note TEXT NOT NULL,
                    response_status TEXT NOT NULL,

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
            CustomerTrialClientResponseObservation,
    ) -> CustomerTrialClientResponseObservationReceipt:
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

            "client_receipt_observation_receipt_hash": (
                observation
                .client_receipt_observation_receipt_hash
            ),
            "client_receipt_observation_hash": (
                observation
                .client_receipt_observation_hash
            ),

            "report_id":
                observation.report_id,

            "response_id":
                observation.response_id,
            "responded_by":
                observation.responded_by,
            "responded_at":
                observation.responded_at,
            "response_method":
                observation.response_method,
            "response_reference":
                observation.response_reference,

            "findings_disposition":
                observation.findings_disposition,
            "recommendations_disposition":
                observation.recommendations_disposition,
            "response_note":
                observation.response_note,
            "response_status":
                observation.response_status,

            "observation_hash":
                observation_hash,

            "schema_version": (
                CUSTOMER_TRIAL_CLIENT_RESPONSE_OBSERVATION_RECEIPT_SCHEMA_VERSION
            ),
        }

        receipt_hash = sha256_hex(
            canonical_json(
                receipt_payload
            )
        )

        return (
            CustomerTrialClientResponseObservationReceipt(
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

                client_receipt_observation_receipt_hash=(
                    observation
                    .client_receipt_observation_receipt_hash
                ),
                client_receipt_observation_hash=(
                    observation
                    .client_receipt_observation_hash
                ),

                report_id=
                    observation.report_id,

                response_id=
                    observation.response_id,
                responded_by=
                    observation.responded_by,
                responded_at=
                    observation.responded_at,
                response_method=
                    observation.response_method,
                response_reference=
                    observation.response_reference,

                findings_disposition=
                    observation.findings_disposition,
                recommendations_disposition=(
                    observation.recommendations_disposition
                ),
                response_note=
                    observation.response_note,
                response_status=
                    observation.response_status,

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
            CustomerTrialClientResponseObservation,
    ) -> CustomerTrialClientResponseObservationReceipt:
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
                CustomerTrialClientResponseObservationReceiptConflictError(
                    "controlled-trial client response observation "
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

                    client_receipt_observation_receipt_hash,
                    client_receipt_observation_hash,

                    report_id,

                    response_id,
                    responded_by,
                    responded_at,
                    response_method,
                    response_reference,

                    findings_disposition,
                    recommendations_disposition,
                    response_note,
                    response_status,

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
                    ?, ?, ?, ?, ?,
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

                    receipt.client_receipt_observation_receipt_hash,
                    receipt.client_receipt_observation_hash,

                    receipt.report_id,

                    receipt.response_id,
                    receipt.responded_by,
                    receipt.responded_at,
                    receipt.response_method,
                    receipt.response_reference,

                    receipt.findings_disposition,
                    receipt.recommendations_disposition,
                    receipt.response_note,
                    receipt.response_status,

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
        CustomerTrialClientResponseObservationReceipt
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

                    client_receipt_observation_receipt_hash,
                    client_receipt_observation_hash,

                    report_id,

                    response_id,
                    responded_by,
                    responded_at,
                    response_method,
                    response_reference,

                    findings_disposition,
                    recommendations_disposition,
                    response_note,
                    response_status,

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
            CustomerTrialClientResponseObservationReceipt(
                tenant_id=row[0],
                client_id=row[1],
                engagement_id=row[2],
                assessment_id=row[3],

                hierarchy_key=row[4],
                observation_status=row[5],

                client_receipt_observation_receipt_hash=row[6],
                client_receipt_observation_hash=row[7],

                report_id=row[8],

                response_id=row[9],
                responded_by=row[10],
                responded_at=row[11],
                response_method=row[12],
                response_reference=row[13],

                findings_disposition=row[14],
                recommendations_disposition=row[15],
                response_note=row[16],
                response_status=row[17],

                observation_hash=row[18],
                receipt_hash=row[19],

                schema_version=row[20],
            )
        )