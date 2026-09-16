from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path

from backend.app.gagf.governance_customer_trial_administrative_closeout_observation import (
    CustomerTrialAdministrativeCloseoutObservation,
)
from backend.app.gagf.scientific_authority_guard import (
    canonical_json,
    sha256_hex,
)


CUSTOMER_TRIAL_ADMINISTRATIVE_CLOSEOUT_OBSERVATION_RECEIPT_ID = (
    "governance-customer-trial-administrative-closeout-observation-receipt"
)

CUSTOMER_TRIAL_ADMINISTRATIVE_CLOSEOUT_OBSERVATION_RECEIPT_VERSION = "0.1.0"

CUSTOMER_TRIAL_ADMINISTRATIVE_CLOSEOUT_OBSERVATION_RECEIPT_SCHEMA_VERSION = (
    "1.0.0"
)


class CustomerTrialAdministrativeCloseoutObservationReceiptError(
    RuntimeError
):
    """Base controlled-trial administrative-closeout receipt error."""


class CustomerTrialAdministrativeCloseoutObservationReceiptConflictError(
    CustomerTrialAdministrativeCloseoutObservationReceiptError
):
    """Raised when persisted closeout-observation lineage conflicts."""


@dataclass(
    frozen=True,
    slots=True,
)
class CustomerTrialAdministrativeCloseoutObservationReceipt:
    tenant_id: str
    client_id: str
    engagement_id: str
    assessment_id: str
    hierarchy_key: str

    observation_status: str
    controlled_trial_status: str
    controlled_trial_complete: bool

    client_response_observation_receipt_hash: str
    client_response_observation_hash: str

    report_id: str

    closeout_status: str
    closed_by: str
    closeout_reason: str

    closeout_artifact_id: str
    closeout_artifact_hash: str
    repository_chain_valid: bool

    observation_hash: str
    receipt_hash: str

    receipt_type: str = (
        CUSTOMER_TRIAL_ADMINISTRATIVE_CLOSEOUT_OBSERVATION_RECEIPT_ID
    )

    version: str = (
        CUSTOMER_TRIAL_ADMINISTRATIVE_CLOSEOUT_OBSERVATION_RECEIPT_VERSION
    )

    schema_version: str = (
        CUSTOMER_TRIAL_ADMINISTRATIVE_CLOSEOUT_OBSERVATION_RECEIPT_SCHEMA_VERSION
    )

    @property
    def boundaries(
        self,
    ) -> dict[str, bool]:
        return {
            "receipt_is_audit_evidence_only":
                True,
            "receipt_does_not_create_closeout":
                True,
            "trial_complete_is_administrative_only":
                True,
            "trial_complete_is_not_findings_validation":
                True,
            "trial_complete_is_not_recommendation_implementation":
                True,
            "trial_complete_is_not_intervention_request":
                True,
            "trial_complete_is_not_intervention_authority":
                True,
            "trial_complete_is_not_execution_authority":
                True,
            "trial_complete_is_not_causal_success":
                True,
            "trial_complete_is_not_roi_verification":
                True,
            "trial_complete_is_not_remediation_success":
                True,
            "trial_complete_is_not_customer_outcome_verification":
                True,
            "pa010_remains_administrative_closeout_authority":
                True,
            "pa012_remains_lifecycle_persistence_authority":
                True,
            "pa013_remains_operator_coordination_authority":
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

            "trial_completion": {
                "status":
                    self.controlled_trial_status,
                "controlled_trial_complete":
                    self.controlled_trial_complete,
            },

            "controlled_trial_lineage": {
                "client_response_observation_receipt_hash": (
                    self.client_response_observation_receipt_hash
                ),
                "client_response_observation_hash": (
                    self.client_response_observation_hash
                ),
            },

            "report": {
                "report_id":
                    self.report_id,
            },

            "administrative_closeout": {
                "closeout_status":
                    self.closeout_status,
                "closed_by":
                    self.closed_by,
                "closeout_reason":
                    self.closeout_reason,
                "closeout_artifact_id":
                    self.closeout_artifact_id,
                "closeout_artifact_hash":
                    self.closeout_artifact_hash,
                "repository_chain_valid":
                    self.repository_chain_valid,
            },

            "observation_hash":
                self.observation_hash,
            "receipt_hash":
                self.receipt_hash,

            "boundaries":
                self.boundaries,
        }


class GovernanceCustomerTrialAdministrativeCloseoutObservationReceiptStore:
    TABLE_NAME = (
        "governance_customer_trial_administrative_closeout_observation_receipts"
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
                    controlled_trial_status TEXT NOT NULL,
                    controlled_trial_complete INTEGER NOT NULL,

                    client_response_observation_receipt_hash TEXT NOT NULL,
                    client_response_observation_hash TEXT NOT NULL,

                    report_id TEXT NOT NULL,

                    closeout_status TEXT NOT NULL,
                    closed_by TEXT NOT NULL,
                    closeout_reason TEXT NOT NULL,

                    closeout_artifact_id TEXT NOT NULL,
                    closeout_artifact_hash TEXT NOT NULL,
                    repository_chain_valid INTEGER NOT NULL,

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
            CustomerTrialAdministrativeCloseoutObservation,
    ) -> CustomerTrialAdministrativeCloseoutObservationReceipt:
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

            "controlled_trial_status":
                observation.controlled_trial_status,

            "controlled_trial_complete":
                observation.controlled_trial_complete,

            "client_response_observation_receipt_hash": (
                observation.client_response_observation_receipt_hash
            ),

            "client_response_observation_hash": (
                observation.client_response_observation_hash
            ),

            "report_id":
                observation.report_id,

            "closeout_status":
                observation.closeout_status,
            "closed_by":
                observation.closed_by,
            "closeout_reason":
                observation.closeout_reason,

            "closeout_artifact_id":
                observation.closeout_artifact_id,
            "closeout_artifact_hash":
                observation.closeout_artifact_hash,

            "repository_chain_valid":
                observation.repository_chain_valid,

            "observation_hash":
                observation_hash,

            "schema_version": (
                CUSTOMER_TRIAL_ADMINISTRATIVE_CLOSEOUT_OBSERVATION_RECEIPT_SCHEMA_VERSION
            ),
        }

        receipt_hash = sha256_hex(
            canonical_json(
                receipt_payload
            )
        )

        return (
            CustomerTrialAdministrativeCloseoutObservationReceipt(
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

                controlled_trial_status=
                    observation.controlled_trial_status,

                controlled_trial_complete=
                    observation.controlled_trial_complete,

                client_response_observation_receipt_hash=(
                    observation.client_response_observation_receipt_hash
                ),

                client_response_observation_hash=(
                    observation.client_response_observation_hash
                ),

                report_id=
                    observation.report_id,

                closeout_status=
                    observation.closeout_status,
                closed_by=
                    observation.closed_by,
                closeout_reason=
                    observation.closeout_reason,

                closeout_artifact_id=
                    observation.closeout_artifact_id,
                closeout_artifact_hash=
                    observation.closeout_artifact_hash,

                repository_chain_valid=
                    observation.repository_chain_valid,

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
            CustomerTrialAdministrativeCloseoutObservation,
    ) -> CustomerTrialAdministrativeCloseoutObservationReceipt:
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
                CustomerTrialAdministrativeCloseoutObservationReceiptConflictError(
                    "controlled-trial administrative closeout "
                    "observation already exists with different lineage"
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
                    controlled_trial_status,
                    controlled_trial_complete,

                    client_response_observation_receipt_hash,
                    client_response_observation_hash,

                    report_id,

                    closeout_status,
                    closed_by,
                    closeout_reason,

                    closeout_artifact_id,
                    closeout_artifact_hash,
                    repository_chain_valid,

                    observation_hash,
                    receipt_hash,

                    schema_version
                )
                VALUES
                (
                    ?, ?, ?, ?,
                    ?,
                    ?, ?, ?,
                    ?, ?,
                    ?,
                    ?, ?, ?,
                    ?, ?, ?,
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
                    receipt.controlled_trial_status,
                    int(
                        receipt.controlled_trial_complete
                    ),

                    receipt.client_response_observation_receipt_hash,
                    receipt.client_response_observation_hash,

                    receipt.report_id,

                    receipt.closeout_status,
                    receipt.closed_by,
                    receipt.closeout_reason,

                    receipt.closeout_artifact_id,
                    receipt.closeout_artifact_hash,
                    int(
                        receipt.repository_chain_valid
                    ),

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
        CustomerTrialAdministrativeCloseoutObservationReceipt
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
                    controlled_trial_status,
                    controlled_trial_complete,

                    client_response_observation_receipt_hash,
                    client_response_observation_hash,

                    report_id,

                    closeout_status,
                    closed_by,
                    closeout_reason,

                    closeout_artifact_id,
                    closeout_artifact_hash,
                    repository_chain_valid,

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
            CustomerTrialAdministrativeCloseoutObservationReceipt(
                tenant_id=row[0],
                client_id=row[1],
                engagement_id=row[2],
                assessment_id=row[3],

                hierarchy_key=row[4],

                observation_status=row[5],
                controlled_trial_status=row[6],
                controlled_trial_complete=bool(
                    row[7]
                ),

                client_response_observation_receipt_hash=row[8],
                client_response_observation_hash=row[9],

                report_id=row[10],

                closeout_status=row[11],
                closed_by=row[12],
                closeout_reason=row[13],

                closeout_artifact_id=row[14],
                closeout_artifact_hash=row[15],
                repository_chain_valid=bool(
                    row[16]
                ),

                observation_hash=row[17],
                receipt_hash=row[18],

                schema_version=row[19],
            )
        )