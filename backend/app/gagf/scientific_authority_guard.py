import hashlib
import json
from dataclasses import dataclass

from backend.app.gagf.scientific_calculation_contract import (
    CalculationAuthority,
    CalculationStatus,
    ScientificCalculationContract,
)


AUTHORITY_POLICY_ID = "scientific-authority-escalation"
AUTHORITY_POLICY_VERSION = "0.1.0"
AUTHORITY_RECEIPT_SCHEMA_VERSION = "1.0.0"


def canonical_json(value: dict) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


def sha256_hex(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class AuthorityEscalationEvidence:
    deterministic_replay_verified: bool
    canonical_input_binding_verified: bool
    calculation_version_frozen: bool
    regression_suite_passed: bool
    validation_report_present: bool
    constitutional_approval_present: bool

    def missing_requirements(self) -> tuple[str, ...]:
        requirements = {
            "deterministic_replay_verified": (
                self.deterministic_replay_verified
            ),
            "canonical_input_binding_verified": (
                self.canonical_input_binding_verified
            ),
            "calculation_version_frozen": (
                self.calculation_version_frozen
            ),
            "regression_suite_passed": (
                self.regression_suite_passed
            ),
            "validation_report_present": (
                self.validation_report_present
            ),
            "constitutional_approval_present": (
                self.constitutional_approval_present
            ),
        }

        return tuple(
            requirement
            for requirement, satisfied in requirements.items()
            if not satisfied
        )

    def to_dict(self) -> dict[str, bool]:
        return {
            "deterministic_replay_verified": (
                self.deterministic_replay_verified
            ),
            "canonical_input_binding_verified": (
                self.canonical_input_binding_verified
            ),
            "calculation_version_frozen": (
                self.calculation_version_frozen
            ),
            "regression_suite_passed": (
                self.regression_suite_passed
            ),
            "validation_report_present": (
                self.validation_report_present
            ),
            "constitutional_approval_present": (
                self.constitutional_approval_present
            ),
        }


@dataclass(frozen=True, slots=True)
class AuthorityEscalationDecision:
    allowed: bool
    policy_id: str
    policy_version: str
    calculation_id: str
    calculation_version: str
    current_authority: CalculationAuthority
    requested_authority: CalculationAuthority
    reason: str
    missing_requirements: tuple[str, ...]

    def to_dict(self) -> dict:
        return {
            "allowed": self.allowed,
            "policy_id": self.policy_id,
            "policy_version": self.policy_version,
            "calculation_id": self.calculation_id,
            "calculation_version": self.calculation_version,
            "current_authority": self.current_authority.value,
            "requested_authority": self.requested_authority.value,
            "reason": self.reason,
            "missing_requirements": list(
                self.missing_requirements
            ),
        }


@dataclass(frozen=True, slots=True)
class AuthorityDecisionReceipt:
    receipt_schema_version: str
    policy_id: str
    policy_version: str
    calculation_id: str
    calculation_version: str
    current_authority: str
    requested_authority: str
    evidence: dict[str, bool]
    decision: dict
    receipt_hash: str

    def payload(self) -> dict:
        return {
            "receipt_schema_version": self.receipt_schema_version,
            "policy_id": self.policy_id,
            "policy_version": self.policy_version,
            "calculation_id": self.calculation_id,
            "calculation_version": self.calculation_version,
            "current_authority": self.current_authority,
            "requested_authority": self.requested_authority,
            "evidence": dict(self.evidence),
            "decision": dict(self.decision),
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


class ScientificAuthorityEscalationGuard:
    def evaluate(
        self,
        *,
        contract: ScientificCalculationContract,
        requested_authority: CalculationAuthority,
        evidence: AuthorityEscalationEvidence,
    ) -> AuthorityEscalationDecision:
        if requested_authority == contract.authority:
            return self._decision(
                contract=contract,
                requested_authority=requested_authority,
                allowed=True,
                reason="Requested authority already matches the contract.",
            )

        if requested_authority == CalculationAuthority.NON_AUTHORITATIVE:
            return self._decision(
                contract=contract,
                requested_authority=requested_authority,
                allowed=True,
                reason="Authority reduction is permitted.",
            )

        if (
            contract.authority == CalculationAuthority.AUTHORITATIVE
            and requested_authority == CalculationAuthority.ADVISORY
        ):
            return self._decision(
                contract=contract,
                requested_authority=requested_authority,
                allowed=True,
                reason="Authority reduction is permitted.",
            )

        if requested_authority == CalculationAuthority.ADVISORY:
            return self._evaluate_advisory_escalation(
                contract=contract,
                evidence=evidence,
            )

        return self._evaluate_authoritative_escalation(
            contract=contract,
            evidence=evidence,
        )

    def evaluate_with_receipt(
        self,
        *,
        contract: ScientificCalculationContract,
        requested_authority: CalculationAuthority,
        evidence: AuthorityEscalationEvidence,
    ) -> tuple[
        AuthorityEscalationDecision,
        AuthorityDecisionReceipt,
    ]:
        decision = self.evaluate(
            contract=contract,
            requested_authority=requested_authority,
            evidence=evidence,
        )

        receipt = self.build_receipt(
            contract=contract,
            requested_authority=requested_authority,
            evidence=evidence,
            decision=decision,
        )

        return decision, receipt

    def build_receipt(
        self,
        *,
        contract: ScientificCalculationContract,
        requested_authority: CalculationAuthority,
        evidence: AuthorityEscalationEvidence,
        decision: AuthorityEscalationDecision,
    ) -> AuthorityDecisionReceipt:
        payload = {
            "receipt_schema_version": (
                AUTHORITY_RECEIPT_SCHEMA_VERSION
            ),
            "policy_id": AUTHORITY_POLICY_ID,
            "policy_version": AUTHORITY_POLICY_VERSION,
            "calculation_id": contract.calculation_id,
            "calculation_version": contract.calculation_version,
            "current_authority": contract.authority.value,
            "requested_authority": requested_authority.value,
            "evidence": evidence.to_dict(),
            "decision": decision.to_dict(),
        }

        receipt_hash = sha256_hex(canonical_json(payload))

        return AuthorityDecisionReceipt(
            receipt_schema_version=(
                AUTHORITY_RECEIPT_SCHEMA_VERSION
            ),
            policy_id=AUTHORITY_POLICY_ID,
            policy_version=AUTHORITY_POLICY_VERSION,
            calculation_id=contract.calculation_id,
            calculation_version=contract.calculation_version,
            current_authority=contract.authority.value,
            requested_authority=requested_authority.value,
            evidence=evidence.to_dict(),
            decision=decision.to_dict(),
            receipt_hash=receipt_hash,
        )

    def _evaluate_advisory_escalation(
        self,
        *,
        contract: ScientificCalculationContract,
        evidence: AuthorityEscalationEvidence,
    ) -> AuthorityEscalationDecision:
        if contract.calculation_status in {
            CalculationStatus.LEGACY_HEURISTIC,
            CalculationStatus.DEPRECATED,
        }:
            return self._decision(
                contract=contract,
                requested_authority=CalculationAuthority.ADVISORY,
                allowed=False,
                reason=(
                    "Legacy or deprecated calculations cannot be "
                    "escalated to advisory authority."
                ),
            )

        required = {
            "deterministic_replay_verified": (
                evidence.deterministic_replay_verified
            ),
            "calculation_version_frozen": (
                evidence.calculation_version_frozen
            ),
            "regression_suite_passed": (
                evidence.regression_suite_passed
            ),
        }

        missing = tuple(
            requirement
            for requirement, satisfied in required.items()
            if not satisfied
        )

        if missing:
            return self._decision(
                contract=contract,
                requested_authority=CalculationAuthority.ADVISORY,
                allowed=False,
                reason=(
                    "Advisory escalation requirements are incomplete."
                ),
                missing_requirements=missing,
            )

        return self._decision(
            contract=contract,
            requested_authority=CalculationAuthority.ADVISORY,
            allowed=True,
            reason="Advisory escalation requirements are satisfied.",
        )

    def _evaluate_authoritative_escalation(
        self,
        *,
        contract: ScientificCalculationContract,
        evidence: AuthorityEscalationEvidence,
    ) -> AuthorityEscalationDecision:
        if contract.calculation_status != CalculationStatus.VALIDATED:
            return self._decision(
                contract=contract,
                requested_authority=(
                    CalculationAuthority.AUTHORITATIVE
                ),
                allowed=False,
                reason=(
                    "Only validated calculations may become "
                    "authoritative."
                ),
            )

        missing = evidence.missing_requirements()

        if missing:
            return self._decision(
                contract=contract,
                requested_authority=(
                    CalculationAuthority.AUTHORITATIVE
                ),
                allowed=False,
                reason=(
                    "Authoritative escalation requirements are "
                    "incomplete."
                ),
                missing_requirements=missing,
            )

        return self._decision(
            contract=contract,
            requested_authority=CalculationAuthority.AUTHORITATIVE,
            allowed=True,
            reason=(
                "Authoritative escalation requirements are satisfied."
            ),
        )

    def _decision(
        self,
        *,
        contract: ScientificCalculationContract,
        requested_authority: CalculationAuthority,
        allowed: bool,
        reason: str,
        missing_requirements: tuple[str, ...] = (),
    ) -> AuthorityEscalationDecision:
        return AuthorityEscalationDecision(
            allowed=allowed,
            policy_id=AUTHORITY_POLICY_ID,
            policy_version=AUTHORITY_POLICY_VERSION,
            calculation_id=contract.calculation_id,
            calculation_version=contract.calculation_version,
            current_authority=contract.authority,
            requested_authority=requested_authority,
            reason=reason,
            missing_requirements=missing_requirements,
        )
