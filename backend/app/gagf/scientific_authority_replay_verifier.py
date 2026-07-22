from dataclasses import dataclass

from backend.app.gagf.scientific_authority_guard import (
    AUTHORITY_POLICY_ID,
    AUTHORITY_POLICY_VERSION,
    AUTHORITY_RECEIPT_SCHEMA_VERSION,
    AuthorityDecisionReceipt,
    AuthorityEscalationEvidence,
    ScientificAuthorityEscalationGuard,
)
from backend.app.gagf.scientific_calculation_contract import (
    CalculationAuthority,
    ScientificCalculationContract,
    get_calculation_contract,
)


REPLAY_VERIFIER_ID = "scientific-authority-replay-verifier"
REPLAY_VERIFIER_VERSION = "0.1.0"


@dataclass(frozen=True, slots=True)
class AuthorityReceiptReplayResult:
    valid: bool
    verifier_id: str
    verifier_version: str
    calculation_id: str
    calculation_version: str
    receipt_hash: str
    replayed_receipt_hash: str | None
    checks: dict[str, bool]
    errors: tuple[str, ...]

    def to_dict(self) -> dict:
        return {
            "valid": self.valid,
            "verifier_id": self.verifier_id,
            "verifier_version": self.verifier_version,
            "calculation_id": self.calculation_id,
            "calculation_version": self.calculation_version,
            "receipt_hash": self.receipt_hash,
            "replayed_receipt_hash": self.replayed_receipt_hash,
            "checks": dict(self.checks),
            "errors": list(self.errors),
        }


class ScientificAuthorityReceiptReplayVerifier:
    def verify(
        self,
        receipt: AuthorityDecisionReceipt,
    ) -> AuthorityReceiptReplayResult:
        checks = {
            "receipt_hash_valid": False,
            "receipt_schema_supported": False,
            "policy_identity_supported": False,
            "calculation_contract_found": False,
            "calculation_version_matches": False,
            "current_authority_matches": False,
            "requested_authority_valid": False,
            "evidence_valid": False,
            "decision_matches_replay": False,
            "receipt_hash_matches_replay": False,
        }
        errors: list[str] = []

        checks["receipt_hash_valid"] = receipt.verify()
        if not checks["receipt_hash_valid"]:
            errors.append("Receipt hash verification failed.")

        checks["receipt_schema_supported"] = (
            receipt.receipt_schema_version
            == AUTHORITY_RECEIPT_SCHEMA_VERSION
        )
        if not checks["receipt_schema_supported"]:
            errors.append(
                "Unsupported authority receipt schema version."
            )

        checks["policy_identity_supported"] = (
            receipt.policy_id == AUTHORITY_POLICY_ID
            and receipt.policy_version == AUTHORITY_POLICY_VERSION
        )
        if not checks["policy_identity_supported"]:
            errors.append(
                "Unsupported scientific authority policy identity."
            )

        contract = self._get_contract(
            receipt=receipt,
            checks=checks,
            errors=errors,
        )

        requested_authority = self._get_requested_authority(
            receipt=receipt,
            checks=checks,
            errors=errors,
        )

        evidence = self._get_evidence(
            receipt=receipt,
            checks=checks,
            errors=errors,
        )

        replayed_receipt_hash: str | None = None

        if (
            contract is not None
            and requested_authority is not None
            and evidence is not None
        ):
            decision, replayed_receipt = (
                ScientificAuthorityEscalationGuard()
                .evaluate_with_receipt(
                    contract=contract,
                    requested_authority=requested_authority,
                    evidence=evidence,
                )
            )

            checks["decision_matches_replay"] = (
                receipt.decision == decision.to_dict()
            )
            if not checks["decision_matches_replay"]:
                errors.append(
                    "Recorded decision does not match deterministic replay."
                )

            replayed_receipt_hash = replayed_receipt.receipt_hash

            checks["receipt_hash_matches_replay"] = (
                receipt.receipt_hash
                == replayed_receipt.receipt_hash
            )
            if not checks["receipt_hash_matches_replay"]:
                errors.append(
                    "Receipt hash does not match replayed receipt hash."
                )

        valid = all(checks.values())

        return AuthorityReceiptReplayResult(
            valid=valid,
            verifier_id=REPLAY_VERIFIER_ID,
            verifier_version=REPLAY_VERIFIER_VERSION,
            calculation_id=receipt.calculation_id,
            calculation_version=receipt.calculation_version,
            receipt_hash=receipt.receipt_hash,
            replayed_receipt_hash=replayed_receipt_hash,
            checks=checks,
            errors=tuple(errors),
        )

    def _get_contract(
        self,
        *,
        receipt: AuthorityDecisionReceipt,
        checks: dict[str, bool],
        errors: list[str],
    ) -> ScientificCalculationContract | None:
        try:
            contract = get_calculation_contract(
                receipt.calculation_id
            )
        except KeyError:
            errors.append(
                "Scientific calculation contract was not found."
            )
            return None

        checks["calculation_contract_found"] = True

        checks["calculation_version_matches"] = (
            contract.calculation_version
            == receipt.calculation_version
        )
        if not checks["calculation_version_matches"]:
            errors.append(
                "Receipt calculation version does not match registry."
            )

        checks["current_authority_matches"] = (
            contract.authority.value
            == receipt.current_authority
        )
        if not checks["current_authority_matches"]:
            errors.append(
                "Receipt current authority does not match registry."
            )

        return contract

    def _get_requested_authority(
        self,
        *,
        receipt: AuthorityDecisionReceipt,
        checks: dict[str, bool],
        errors: list[str],
    ) -> CalculationAuthority | None:
        try:
            requested_authority = CalculationAuthority(
                receipt.requested_authority
            )
        except ValueError:
            errors.append(
                "Receipt requested authority is invalid."
            )
            return None

        checks["requested_authority_valid"] = True
        return requested_authority

    def _get_evidence(
        self,
        *,
        receipt: AuthorityDecisionReceipt,
        checks: dict[str, bool],
        errors: list[str],
    ) -> AuthorityEscalationEvidence | None:
        expected_fields = {
            "deterministic_replay_verified",
            "canonical_input_binding_verified",
            "calculation_version_frozen",
            "regression_suite_passed",
            "validation_report_present",
            "constitutional_approval_present",
        }

        if set(receipt.evidence) != expected_fields:
            errors.append(
                "Receipt evidence fields do not match the required schema."
            )
            return None

        if not all(
            isinstance(value, bool)
            for value in receipt.evidence.values()
        ):
            errors.append(
                "Receipt evidence values must all be booleans."
            )
            return None

        checks["evidence_valid"] = True

        return AuthorityEscalationEvidence(
            deterministic_replay_verified=receipt.evidence[
                "deterministic_replay_verified"
            ],
            canonical_input_binding_verified=receipt.evidence[
                "canonical_input_binding_verified"
            ],
            calculation_version_frozen=receipt.evidence[
                "calculation_version_frozen"
            ],
            regression_suite_passed=receipt.evidence[
                "regression_suite_passed"
            ],
            validation_report_present=receipt.evidence[
                "validation_report_present"
            ],
            constitutional_approval_present=receipt.evidence[
                "constitutional_approval_present"
            ],
        )
