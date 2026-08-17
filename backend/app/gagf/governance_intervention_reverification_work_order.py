from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from backend.app.gagf.governance_intervention_reverification_request import (
    GovernanceInterventionReverificationRequest,
    GovernanceInterventionReverificationScope,
)
from backend.app.gagf.governance_intervention_reverification_request_ledger import (
    GovernanceInterventionReverificationRequestLedgerEntry,
)
from backend.app.gagf.scientific_authority_guard import (
    canonical_json,
    sha256_hex,
)


GOVERNANCE_INTERVENTION_REVERIFICATION_WORK_ORDER_ID = (
    "governance-intervention-reverification-work-order"
)

GOVERNANCE_INTERVENTION_REVERIFICATION_WORK_ORDER_VERSION = (
    "0.1.0"
)

GOVERNANCE_INTERVENTION_REVERIFICATION_WORK_ORDER_SCHEMA_VERSION = (
    "1.0.0"
)


class GovernanceInterventionReverificationWorkOrderError(
    ValueError
):
    """Base error for governed reverification work-order construction."""


class GovernanceInterventionReverificationWorkOrderIntegrityError(
    GovernanceInterventionReverificationWorkOrderError
):
    """Raised when request/ledger lineage cannot be proven."""


@dataclass(frozen=True, slots=True)
class GovernanceInterventionReverificationWorkOrder:
    """
    Immutable binding between one persisted reverification request and one
    explicit future reverification attempt.

    A work order is not:
    - reverification execution;
    - evidence collection;
    - measurement;
    - verification completion;
    - a new verification disposition;
    - intervention authorization;
    - causal attribution.
    """

    work_order_id: str
    version: str
    schema_version: str

    tenant_id: str
    intervention_id: str
    verification_record_hash: str

    request_hash: str
    request_ledger_chain_hash: str

    attempt_id: str
    reverification_scope: str
    trigger_codes: tuple[str, ...]

    work_order_hash: str

    def payload(self) -> dict[str, Any]:
        return {
            "work_order_id": self.work_order_id,
            "version": self.version,
            "schema_version": self.schema_version,
            "tenant_id": self.tenant_id,
            "intervention_id": self.intervention_id,
            "verification_record_hash": (
                self.verification_record_hash
            ),
            "request_hash": self.request_hash,
            "request_ledger_chain_hash": (
                self.request_ledger_chain_hash
            ),
            "attempt_id": self.attempt_id,
            "reverification_scope": (
                self.reverification_scope
            ),
            "trigger_codes": list(
                self.trigger_codes
            ),
        }

    def verify(self) -> bool:
        return (
            self.work_order_hash
            == sha256_hex(
                canonical_json(
                    self.payload()
                )
            )
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            **self.payload(),
            "work_order_hash": self.work_order_hash,
        }


class GovernanceInterventionReverificationWorkOrderBuilder:
    """
    Deterministically binds a valid persisted I-K request to one explicit
    reverification attempt identity.

    The builder does not execute the attempt or mutate request/lifecycle state.
    """

    @classmethod
    def build(
        cls,
        *,
        request: GovernanceInterventionReverificationRequest,
        ledger_entry: (
            GovernanceInterventionReverificationRequestLedgerEntry
        ),
        attempt_id: str,
    ) -> GovernanceInterventionReverificationWorkOrder:
        cls._validate_inputs(
            request=request,
            ledger_entry=ledger_entry,
            attempt_id=attempt_id,
        )

        payload: dict[str, Any] = {
            "work_order_id": (
                GOVERNANCE_INTERVENTION_REVERIFICATION_WORK_ORDER_ID
            ),
            "version": (
                GOVERNANCE_INTERVENTION_REVERIFICATION_WORK_ORDER_VERSION
            ),
            "schema_version": (
                GOVERNANCE_INTERVENTION_REVERIFICATION_WORK_ORDER_SCHEMA_VERSION
            ),
            "tenant_id": request.tenant_id,
            "intervention_id": request.intervention_id,
            "verification_record_hash": (
                request.verification_record_hash
            ),
            "request_hash": request.request_hash,
            "request_ledger_chain_hash": (
                ledger_entry.chain_hash
            ),
            "attempt_id": attempt_id,
            "reverification_scope": (
                request.reverification_scope
            ),
            "trigger_codes": list(
                request.trigger_codes
            ),
        }

        return GovernanceInterventionReverificationWorkOrder(
            work_order_id=payload["work_order_id"],
            version=payload["version"],
            schema_version=payload["schema_version"],
            tenant_id=payload["tenant_id"],
            intervention_id=payload["intervention_id"],
            verification_record_hash=payload[
                "verification_record_hash"
            ],
            request_hash=payload["request_hash"],
            request_ledger_chain_hash=payload[
                "request_ledger_chain_hash"
            ],
            attempt_id=payload["attempt_id"],
            reverification_scope=payload[
                "reverification_scope"
            ],
            trigger_codes=tuple(
                payload["trigger_codes"]
            ),
            work_order_hash=sha256_hex(
                canonical_json(payload)
            ),
        )

    @staticmethod
    def _validate_inputs(
        *,
        request: GovernanceInterventionReverificationRequest,
        ledger_entry: (
            GovernanceInterventionReverificationRequestLedgerEntry
        ),
        attempt_id: str,
    ) -> None:
        if not request.verify():
            raise (
                GovernanceInterventionReverificationWorkOrderIntegrityError(
                    "reverification request failed deterministic verification"
                )
            )

        if not ledger_entry.verify_chain_hash():
            raise (
                GovernanceInterventionReverificationWorkOrderIntegrityError(
                    "reverification request ledger entry failed "
                    "chain verification"
                )
            )

        if (
            ledger_entry.tenant_id
            != request.tenant_id
        ):
            raise (
                GovernanceInterventionReverificationWorkOrderIntegrityError(
                    "request ledger tenant does not match request"
                )
            )

        if (
            ledger_entry.request_hash
            != request.request_hash
        ):
            raise (
                GovernanceInterventionReverificationWorkOrderIntegrityError(
                    "request ledger entry is not bound to request"
                )
            )

        if (
            ledger_entry.verification_record_hash
            != request.verification_record_hash
        ):
            raise (
                GovernanceInterventionReverificationWorkOrderIntegrityError(
                    "request ledger verification record does not "
                    "match request"
                )
            )

        normalized_attempt_id = attempt_id.strip()

        if not normalized_attempt_id:
            raise GovernanceInterventionReverificationWorkOrderError(
                "attempt_id is required"
            )

        if normalized_attempt_id != attempt_id:
            raise GovernanceInterventionReverificationWorkOrderError(
                "attempt_id must already be canonical"
            )

        try:
            GovernanceInterventionReverificationScope(
                request.reverification_scope
            )
        except ValueError as exc:
            raise (
                GovernanceInterventionReverificationWorkOrderIntegrityError(
                    "request contains unsupported reverification scope"
                )
            ) from exc

        if not request.trigger_codes:
            raise (
                GovernanceInterventionReverificationWorkOrderIntegrityError(
                    "request must contain at least one trigger"
                )
            )