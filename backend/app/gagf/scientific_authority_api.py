from dataclasses import asdict, dataclass, is_dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from backend.app.gagf.scientific_authority_receipt_ledger import (
    ScientificAuthorityReceiptLedger,
)
from backend.app.gagf.scientific_calculation_contract import (
    CalculationAuthority,
    get_calculation_contract,
    list_calculation_contracts,
)
from backend.app.gagf.scientific_evidence_checkpoint_ledger import (
    ScientificEvidenceCheckpointLedger,
)
from backend.app.gagf.scientific_evidence_checkpoint_replay_verifier import (
    ScientificEvidenceCheckpointReplayVerifier,
)
from backend.app.gagf.scientific_pipeline_execution_journal import (
    ScientificPipelineExecutionJournal,
    ScientificPipelineRecoveryCoordinator,
)
from backend.app.gagf.scientific_authority_guard import (
    AuthorityEscalationEvidence,
)


SCIENTIFIC_AUTHORITY_API_ID = "scientific-authority-api"
SCIENTIFIC_AUTHORITY_API_VERSION = "0.1.0"


@dataclass(frozen=True, slots=True)
class ScientificAuthorityApiPaths:
    authority_database_path: Path
    audit_database_path: Path
    checkpoint_database_path: Path
    journal_database_path: Path


class AuthorityEscalationEvidenceRequest(BaseModel):
    deterministic_replay_verified: bool
    canonical_input_binding_verified: bool
    calculation_version_frozen: bool
    regression_suite_passed: bool
    validation_report_present: bool
    constitutional_approval_present: bool

    def to_domain(self) -> AuthorityEscalationEvidence:
        return AuthorityEscalationEvidence(
            deterministic_replay_verified=(
                self.deterministic_replay_verified
            ),
            canonical_input_binding_verified=(
                self.canonical_input_binding_verified
            ),
            calculation_version_frozen=(
                self.calculation_version_frozen
            ),
            regression_suite_passed=(
                self.regression_suite_passed
            ),
            validation_report_present=(
                self.validation_report_present
            ),
            constitutional_approval_present=(
                self.constitutional_approval_present
            ),
        )


class ScientificAuthorityEvaluationRequest(BaseModel):
    calculation_id: str
    requested_authority: CalculationAuthority
    evidence: AuthorityEscalationEvidenceRequest


def create_scientific_authority_router(
    *,
    paths: ScientificAuthorityApiPaths,
) -> APIRouter:
    router = APIRouter(
        prefix="/scientific-authority",
        tags=["scientific-authority"],
    )

    coordinator = ScientificPipelineRecoveryCoordinator(
        authority_database_path=paths.authority_database_path,
        audit_database_path=paths.audit_database_path,
        checkpoint_database_path=paths.checkpoint_database_path,
        journal_database_path=paths.journal_database_path,
    )

    authority_ledger = ScientificAuthorityReceiptLedger(
        paths.authority_database_path
    )
    checkpoint_ledger = ScientificEvidenceCheckpointLedger(
        paths.checkpoint_database_path
    )
    journal = ScientificPipelineExecutionJournal(
        paths.journal_database_path
    )

    @router.get("/contracts")
    def list_contracts() -> dict:
        contracts = list_calculation_contracts()

        return {
            "api_id": SCIENTIFIC_AUTHORITY_API_ID,
            "api_version": SCIENTIFIC_AUTHORITY_API_VERSION,
            "contracts": [
                _serialize_value(contract)
                for contract in contracts
            ],
        }

    @router.post(
        "/evaluate",
        status_code=status.HTTP_200_OK,
    )
    def evaluate_authority(
        request: ScientificAuthorityEvaluationRequest,
    ) -> dict:
        try:
            contract = get_calculation_contract(
                request.calculation_id
            )
        except KeyError as exc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=(
                    "Scientific calculation contract was not found."
                ),
            ) from exc

        try:
            result = coordinator.execute(
                contract=contract,
                requested_authority=(
                    request.requested_authority
                ),
                evidence=request.evidence.to_domain(),
            )
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(exc),
            ) from exc
        except Exception as exc:
            raise HTTPException(
                status_code=(
                    status.HTTP_500_INTERNAL_SERVER_ERROR
                ),
                detail=(
                    "Scientific authority execution failed: "
                    + str(exc)
                ),
            ) from exc

        return {
            "api_id": SCIENTIFIC_AUTHORITY_API_ID,
            "api_version": SCIENTIFIC_AUTHORITY_API_VERSION,
            **result.to_dict(),
        }

    @router.get("/receipts/{receipt_hash}")
    def get_authority_receipt(
        receipt_hash: str,
    ) -> dict:
        record = authority_ledger.get_by_hash(
            receipt_hash
        )

        if record is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Authority receipt was not found.",
            )

        return {
            "api_id": SCIENTIFIC_AUTHORITY_API_ID,
            "api_version": SCIENTIFIC_AUTHORITY_API_VERSION,
            **record.to_dict(),
        }

    @router.get("/checkpoints/{checkpoint_hash}")
    def get_checkpoint(
        checkpoint_hash: str,
    ) -> dict:
        record = checkpoint_ledger.get_by_hash(
            checkpoint_hash
        )

        if record is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Scientific evidence checkpoint was not found.",
            )

        return {
            "api_id": SCIENTIFIC_AUTHORITY_API_ID,
            "api_version": SCIENTIFIC_AUTHORITY_API_VERSION,
            **record.to_dict(),
        }

    @router.post("/checkpoints/{checkpoint_hash}/verify")
    def verify_checkpoint(
        checkpoint_hash: str,
    ) -> dict:
        record = checkpoint_ledger.get_by_hash(
            checkpoint_hash
        )

        if record is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Scientific evidence checkpoint was not found.",
            )

        result = (
            ScientificEvidenceCheckpointReplayVerifier()
            .verify(
                checkpoint=record.checkpoint,
                authority_database_path=(
                    paths.authority_database_path
                ),
                audit_database_path=(
                    paths.audit_database_path
                ),
            )
        )

        return {
            "api_id": SCIENTIFIC_AUTHORITY_API_ID,
            "api_version": SCIENTIFIC_AUTHORITY_API_VERSION,
            **result.to_dict(),
        }

    @router.get("/executions/{execution_id}")
    def get_execution(
        execution_id: str,
    ) -> dict:
        record = journal.get(execution_id)

        if record is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Scientific pipeline execution was not found.",
            )

        transitions = journal.list_transitions(
            execution_id
        )

        return {
            "api_id": SCIENTIFIC_AUTHORITY_API_ID,
            "api_version": SCIENTIFIC_AUTHORITY_API_VERSION,
            "execution": record.to_dict(),
            "transitions": [
                transition.to_dict()
                for transition in transitions
            ],
        }

    return router


def _serialize_value(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value

    if is_dataclass(value):
        return _serialize_value(asdict(value))

    if isinstance(value, dict):
        return {
            str(key): _serialize_value(item)
            for key, item in value.items()
        }

    if isinstance(value, (list, tuple)):
        return [
            _serialize_value(item)
            for item in value
        ]

    return value
