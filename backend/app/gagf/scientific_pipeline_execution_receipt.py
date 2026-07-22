from dataclasses import dataclass

from backend.app.gagf.scientific_authority_evidence_pipeline import (
    SCIENTIFIC_AUTHORITY_EVIDENCE_PIPELINE_ID,
    SCIENTIFIC_AUTHORITY_EVIDENCE_PIPELINE_VERSION,
    ScientificAuthorityEvidencePipelineResult,
)
from backend.app.gagf.scientific_authority_guard import (
    AuthorityEscalationEvidence,
    canonical_json,
    sha256_hex,
)
from backend.app.gagf.scientific_calculation_contract import (
    CalculationAuthority,
    ScientificCalculationContract,
)


SCIENTIFIC_PIPELINE_EXECUTION_RECEIPT_ID = (
    "constitutional-scientific-pipeline-execution-receipt"
)
SCIENTIFIC_PIPELINE_EXECUTION_RECEIPT_VERSION = "0.1.0"
SCIENTIFIC_PIPELINE_EXECUTION_RECEIPT_SCHEMA_VERSION = "1.0.0"


@dataclass(frozen=True, slots=True)
class ScientificPipelineExecutionReceipt:
    receipt_schema_version: str
    receipt_id: str
    receipt_version: str
    pipeline_id: str
    pipeline_version: str
    calculation_id: str
    calculation_version: str
    requested_authority: str
    evidence: dict[str, bool]
    decision_allowed: bool
    authority_receipt_sequence: int
    authority_receipt_hash: str
    authority_ledger_audit_valid: bool
    audit_receipt_sequence: int
    audit_receipt_hash: str
    checkpoint_sequence: int
    checkpoint_hash: str
    checkpoint_valid: bool
    receipt_hash: str

    def payload(self) -> dict:
        return {
            "receipt_schema_version": (
                self.receipt_schema_version
            ),
            "receipt_id": self.receipt_id,
            "receipt_version": self.receipt_version,
            "pipeline_id": self.pipeline_id,
            "pipeline_version": self.pipeline_version,
            "calculation_id": self.calculation_id,
            "calculation_version": self.calculation_version,
            "requested_authority": self.requested_authority,
            "evidence": dict(self.evidence),
            "decision_allowed": self.decision_allowed,
            "authority_receipt_sequence": (
                self.authority_receipt_sequence
            ),
            "authority_receipt_hash": (
                self.authority_receipt_hash
            ),
            "authority_ledger_audit_valid": (
                self.authority_ledger_audit_valid
            ),
            "audit_receipt_sequence": (
                self.audit_receipt_sequence
            ),
            "audit_receipt_hash": self.audit_receipt_hash,
            "checkpoint_sequence": self.checkpoint_sequence,
            "checkpoint_hash": self.checkpoint_hash,
            "checkpoint_valid": self.checkpoint_valid,
        }

    def to_dict(self) -> dict:
        return {
            **self.payload(),
            "receipt_hash": self.receipt_hash,
        }

    def verify(self) -> bool:
        expected_hash = sha256_hex(
            canonical_json(self.payload())
        )

        return expected_hash == self.receipt_hash


class ScientificPipelineExecutionReceiptBuilder:
    def build(
        self,
        *,
        contract: ScientificCalculationContract,
        requested_authority: CalculationAuthority,
        evidence: AuthorityEscalationEvidence,
        pipeline_result: ScientificAuthorityEvidencePipelineResult,
    ) -> ScientificPipelineExecutionReceipt:
        self._validate_pipeline_result(
            contract=contract,
            requested_authority=requested_authority,
            pipeline_result=pipeline_result,
        )

        serialized_evidence = self._serialize_evidence(
            evidence
        )

        payload = {
            "receipt_schema_version": (
                SCIENTIFIC_PIPELINE_EXECUTION_RECEIPT_SCHEMA_VERSION
            ),
            "receipt_id": (
                SCIENTIFIC_PIPELINE_EXECUTION_RECEIPT_ID
            ),
            "receipt_version": (
                SCIENTIFIC_PIPELINE_EXECUTION_RECEIPT_VERSION
            ),
            "pipeline_id": pipeline_result.pipeline_id,
            "pipeline_version": pipeline_result.pipeline_version,
            "calculation_id": pipeline_result.calculation_id,
            "calculation_version": (
                pipeline_result.calculation_version
            ),
            "requested_authority": (
                pipeline_result.requested_authority
            ),
            "evidence": serialized_evidence,
            "decision_allowed": (
                pipeline_result.decision_allowed
            ),
            "authority_receipt_sequence": (
                pipeline_result.authority_receipt_sequence
            ),
            "authority_receipt_hash": (
                pipeline_result.authority_receipt_hash
            ),
            "authority_ledger_audit_valid": (
                pipeline_result.authority_ledger_audit_valid
            ),
            "audit_receipt_sequence": (
                pipeline_result.audit_receipt_sequence
            ),
            "audit_receipt_hash": (
                pipeline_result.audit_receipt_hash
            ),
            "checkpoint_sequence": (
                pipeline_result.checkpoint_sequence
            ),
            "checkpoint_hash": (
                pipeline_result.checkpoint_hash
            ),
            "checkpoint_valid": (
                pipeline_result.checkpoint_valid
            ),
        }

        receipt_hash = sha256_hex(
            canonical_json(payload)
        )

        return ScientificPipelineExecutionReceipt(
            receipt_schema_version=(
                SCIENTIFIC_PIPELINE_EXECUTION_RECEIPT_SCHEMA_VERSION
            ),
            receipt_id=(
                SCIENTIFIC_PIPELINE_EXECUTION_RECEIPT_ID
            ),
            receipt_version=(
                SCIENTIFIC_PIPELINE_EXECUTION_RECEIPT_VERSION
            ),
            pipeline_id=pipeline_result.pipeline_id,
            pipeline_version=pipeline_result.pipeline_version,
            calculation_id=pipeline_result.calculation_id,
            calculation_version=(
                pipeline_result.calculation_version
            ),
            requested_authority=(
                pipeline_result.requested_authority
            ),
            evidence=serialized_evidence,
            decision_allowed=pipeline_result.decision_allowed,
            authority_receipt_sequence=(
                pipeline_result.authority_receipt_sequence
            ),
            authority_receipt_hash=(
                pipeline_result.authority_receipt_hash
            ),
            authority_ledger_audit_valid=(
                pipeline_result.authority_ledger_audit_valid
            ),
            audit_receipt_sequence=(
                pipeline_result.audit_receipt_sequence
            ),
            audit_receipt_hash=(
                pipeline_result.audit_receipt_hash
            ),
            checkpoint_sequence=(
                pipeline_result.checkpoint_sequence
            ),
            checkpoint_hash=pipeline_result.checkpoint_hash,
            checkpoint_valid=pipeline_result.checkpoint_valid,
            receipt_hash=receipt_hash,
        )

    def _serialize_evidence(
        self,
        evidence: AuthorityEscalationEvidence,
    ) -> dict[str, bool]:
        return {
            "deterministic_replay_verified": (
                evidence.deterministic_replay_verified
            ),
            "canonical_input_binding_verified": (
                evidence.canonical_input_binding_verified
            ),
            "calculation_version_frozen": (
                evidence.calculation_version_frozen
            ),
            "regression_suite_passed": (
                evidence.regression_suite_passed
            ),
            "validation_report_present": (
                evidence.validation_report_present
            ),
            "constitutional_approval_present": (
                evidence.constitutional_approval_present
            ),
        }

    def _validate_pipeline_result(
        self,
        *,
        contract: ScientificCalculationContract,
        requested_authority: CalculationAuthority,
        pipeline_result: ScientificAuthorityEvidencePipelineResult,
    ) -> None:
        errors: list[str] = []

        if (
            pipeline_result.pipeline_id
            != SCIENTIFIC_AUTHORITY_EVIDENCE_PIPELINE_ID
        ):
            errors.append(
                "Pipeline result has an unsupported pipeline identity."
            )

        if (
            pipeline_result.pipeline_version
            != SCIENTIFIC_AUTHORITY_EVIDENCE_PIPELINE_VERSION
        ):
            errors.append(
                "Pipeline result has an unsupported pipeline version."
            )

        if (
            pipeline_result.calculation_id
            != contract.calculation_id
        ):
            errors.append(
                "Pipeline calculation identity does not match "
                "the supplied contract."
            )

        if (
            pipeline_result.calculation_version
            != contract.calculation_version
        ):
            errors.append(
                "Pipeline calculation version does not match "
                "the supplied contract."
            )

        if (
            pipeline_result.requested_authority
            != requested_authority.value
        ):
            errors.append(
                "Pipeline requested authority does not match "
                "the supplied request."
            )

        if errors:
            raise ValueError(
                "Cannot build scientific pipeline execution "
                "receipt: "
                + "; ".join(errors)
            )
