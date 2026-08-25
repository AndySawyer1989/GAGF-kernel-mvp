from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from backend.app.gagf.governance_paid_assessment_execution_handoff import (
    PaidAssessmentWorkAuthorization,
)
from backend.app.gagf.prelive_assessment_execution_bridge import (
    PreliveAssessmentExecutionMetadata,
)
from backend.app.gagf.prelive_blind_assessment import (
    PRELIVE_PROGRAM,
    PreliveScenarioError,
    validate_pre_live_scenario,
)
from backend.app.gagf.prelive_operator_execution_rehearsal import (
    PreliveOperatorExecutionConfirmation,
    PreliveOperatorExecutionRehearsal,
    PreliveOperatorExecutionRehearsalResult,
)
from backend.app.gagf.prelive_oracle_scoring import (
    PreliveOracleScoringResult,
    PreliveOracleScoringService,
)
from backend.app.gagf.prelive_rehearsal_result_verification import (
    PreliveRehearsalResultVerifier,
    PreliveRehearsalVerificationResult,
)


PRELIVE_BLIND_RUNNER_VERSION = "1.0.0"
PRELIVE_BLIND_RUNNER_STATUS = "blind_rehearsal_complete"
PRELIVE_BLIND_RUNNER_AUTHORITY = "GAGF_FIP_ONLY"


@dataclass(frozen=True, slots=True)
class PreliveBlindAssessmentRunResult:
    scenario_id: str
    scenario_sha256: str
    output_directory: str
    database_path: str

    execution: PreliveOperatorExecutionRehearsalResult
    verification: PreliveRehearsalVerificationResult
    scoring: PreliveOracleScoringResult

    run_status: str = PRELIVE_BLIND_RUNNER_STATUS
    authority: str = PRELIVE_BLIND_RUNNER_AUTHORITY
    runner_version: str = PRELIVE_BLIND_RUNNER_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_status": self.run_status,
            "authority": self.authority,
            "runner_version": self.runner_version,
            "scenario_id": self.scenario_id,
            "scenario_sha256": self.scenario_sha256,
            "output_directory": self.output_directory,
            "database_path": self.database_path,
            "execution": self.execution.to_dict(),
            "verification": self.verification.to_dict(),
            "scoring": self.scoring.to_dict(),
        }


class PreliveBlindAssessmentRunner:
    """
    Operator-controlled end-to-end PRELIVE blind assessment runner.

    Order is constitutionally important:

    1. Validate blind scenario.
    2. Prepare real assessment request and governed handoff.
    3. Require explicit operator execution confirmation.
    4. Execute through the existing paid-assessment coordinator.
    5. Verify persisted output independently.
    6. Only after verification passes, unseal and score oracle.
    7. Persist operator-facing run artifacts.

    External AI remains evidence/oracle generator only.
    """

    def __init__(
        self,
        *,
        rehearsal: PreliveOperatorExecutionRehearsal | None = None,
        verifier: PreliveRehearsalResultVerifier | None = None,
        scorer: PreliveOracleScoringService | None = None,
    ) -> None:
        self._rehearsal = (
            rehearsal
            or PreliveOperatorExecutionRehearsal()
        )

        self._verifier = (
            verifier
            or PreliveRehearsalResultVerifier()
        )

        self._scorer = (
            scorer
            or PreliveOracleScoringService()
        )

    def run(
        self,
        *,
        scenario: Mapping[str, Any],
        oracle: Mapping[str, Any],
        output_directory: str | Path,
        operator_id: str,
        execution_confirmed: bool,
        confirmed_at: str | None = None,
    ) -> PreliveBlindAssessmentRunResult:
        validation = validate_pre_live_scenario(
            scenario
        )

        if not validation.valid:
            messages = "; ".join(
                issue.message
                for issue in validation.issues
            )

            raise PreliveScenarioError(
                "PRELIVE blind scenario validation "
                f"failed: {messages}"
            )

        if validation.scenario_sha256 is None:
            raise PreliveScenarioError(
                "PRELIVE blind scenario did not "
                "produce a canonical SHA-256."
            )

        if execution_confirmed is not True:
            raise PreliveScenarioError(
                "PRELIVE blind assessment execution "
                "requires explicit human confirmation."
            )

        if (
            not isinstance(operator_id, str)
            or not operator_id.strip()
        ):
            raise PreliveScenarioError(
                "PRELIVE operator_id must not be empty."
            )

        scenario_dict = dict(scenario)
        oracle_dict = dict(oracle)

        scenario_id = str(
            scenario_dict["scenario_id"]
        ).strip()

        output_path = Path(
            output_directory
        )

        self._prepare_output_directory(
            output_path
        )

        database_path = (
            output_path
            / "prelive.sqlite3"
        )

        timestamp = (
            confirmed_at
            or datetime.now(
                timezone.utc
            ).isoformat()
        )

        tenant_id = self._scenario_tenant(
            scenario_dict
        )

        metadata = self._build_metadata(
            scenario=scenario_dict,
            tenant_id=tenant_id,
            scenario_id=scenario_id,
            operator_id=operator_id.strip(),
        )

        contract_event = self._build_contract_event(
            scenario_id=scenario_id,
            timestamp=timestamp,
        )

        authorization = (
            self._build_authorization(
                tenant_id=tenant_id,
                metadata=metadata,
                scenario_id=scenario_id,
                timestamp=timestamp,
                operator_id=operator_id.strip(),
            )
        )

        prepared = self._rehearsal.prepare(
            scenario=scenario_dict,
            metadata=metadata,
            contract_execution_event=(
                contract_event
            ),
            paid_work_authorization=(
                authorization
            ),
        )

        confirmation = (
            PreliveOperatorExecutionConfirmation(
                operator_id=operator_id.strip(),
                confirmed_at=timestamp,
                handoff_hash=(
                    prepared.handoff.handoff_hash
                ),
                assessment_execution_request_hash=(
                    prepared.handoff
                    .assessment_execution_request_hash
                ),
                execution_confirmed=True,
            )
        )

        execution = (
            self._rehearsal.execute_prepared(
                database_path=database_path,
                prepared=prepared,
                operator_confirmation=(
                    confirmation
                ),
            )
        )

        verification = self._verifier.verify(
            database_path=database_path,
            rehearsal_result=execution,
        )

        scoring = self._scorer.score(
            database_path=database_path,
            rehearsal_result=execution,
            verification=verification,
            oracle=oracle_dict,
        )

        result = PreliveBlindAssessmentRunResult(
            scenario_id=scenario_id,
            scenario_sha256=(
                validation.scenario_sha256
            ),
            output_directory=str(
                output_path
            ),
            database_path=str(
                database_path
            ),
            execution=execution,
            verification=verification,
            scoring=scoring,
        )

        self._write_outputs(
            output_path=output_path,
            scenario=scenario_dict,
            oracle=oracle_dict,
            result=result,
        )

        return result

    def _prepare_output_directory(
        self,
        output_path: Path,
    ) -> None:
        if output_path.exists():
            existing = tuple(
                output_path.iterdir()
            )

            if existing:
                raise PreliveScenarioError(
                    "PRELIVE output directory must "
                    "be empty for a new blind run."
                )
        else:
            output_path.mkdir(
                parents=True,
                exist_ok=False,
            )

    def _scenario_tenant(
        self,
        scenario: Mapping[str, Any],
    ) -> str:
        events = scenario.get(
            "events"
        )

        if not isinstance(
            events,
            list,
        ):
            raise PreliveScenarioError(
                "PRELIVE scenario events are required "
                "for runner tenant binding."
            )

        tenants = {
            str(
                event["tenant_id"]
            ).strip()
            for event in events
            if isinstance(
                event,
                Mapping,
            )
            and isinstance(
                event.get("tenant_id"),
                str,
            )
            and event["tenant_id"].strip()
        }

        if len(tenants) != 1:
            raise PreliveScenarioError(
                "PRELIVE runner requires exactly one "
                "tenant across blind evidence."
            )

        return next(
            iter(tenants)
        )

    def _build_metadata(
        self,
        *,
        scenario: Mapping[str, Any],
        tenant_id: str,
        scenario_id: str,
        operator_id: str,
    ) -> PreliveAssessmentExecutionMetadata:
        organization = scenario.get(
            "organization"
        )

        organization_name = (
            str(
                organization.get(
                    "name"
                )
            ).strip()
            if isinstance(
                organization,
                Mapping,
            )
            else ""
        )

        if not organization_name:
            organization_name = (
                "PRELIVE Synthetic Organization"
            )

        safe_scenario_id = (
            scenario_id
            .strip()
            .lower()
            .replace(" ", "-")
        )

        return PreliveAssessmentExecutionMetadata(
            tenant_id=tenant_id,
            client_id="prelive-client",
            engagement_id=(
                f"prelive-{safe_scenario_id}"
            ),
            assessment_id=(
                f"assessment-{safe_scenario_id}"
            ),
            assessment_name=(
                "PRELIVE Blind Governance Assessment"
            ),
            workflow_names=(
                "Blind Synthetic Workflow",
            ),
            organizational_units=(
                "Synthetic Operations",
            ),
            objectives=(
                "Evaluate blind governance "
                "friction detection.",
            ),
            expected_outcomes=(
                "Produce deterministic FIP "
                "assessment output.",
            ),
            client_display_name=(
                organization_name
            ),
            prepared_by=operator_id,
            exclusions=(
                "Production actions",
            ),
            maximum_priorities=3,
        )

    def _build_contract_event(
        self,
        *,
        scenario_id: str,
        timestamp: str,
    ) -> dict[str, Any]:
        contract_event_id = (
            f"contract-event-{scenario_id}"
        )

        return {
            "status": "ok",
            "event_type": (
                "assessment_factory_lite_"
                "contract_execution_event"
            ),
            "package_name": (
                "assessment_factory_lite"
            ),
            "release": (
                "assessment-factory-lite-"
                "scope-call-conversion"
            ),
            "version": "2.3.0",
            "event_stage": (
                "contract_execution"
            ),
            "event_status": (
                "contract_executed"
            ),
            "contract_execution_event_id": (
                contract_event_id
            ),
            "recorded_at": timestamp,
            "execution_evidence": {
                "executed_contract_reference": (
                    f"prelive-contract-{scenario_id}"
                ),
                "executed_at": timestamp,
                (
                    "executed_contract_"
                    "reference_recorded"
                ): True,
                "executed_at_recorded": True,
                "contract_execution_confirmed": True,
                "contract_executed": True,
            },
            "event_checklist": {
                "contract_execution_review_ready": True,
                "contract_execution_confirmed": True,
                (
                    "executed_contract_"
                    "reference_recorded"
                ): True,
                "executed_at_recorded": True,
                "execution_method_recorded": True,
                "all_required_signatures_recorded": True,
                (
                    "human_operator_"
                    "confirmed_execution"
                ): True,
                "signature_record_is_not_invoice": True,
                "signature_record_is_not_payment": True,
                "invoice_not_created": True,
                "payment_not_requested": True,
                "paid_assessment_not_authorized": True,
                (
                    "production_onboarding_"
                    "not_started"
                ): True,
            },
            "event_blockers": [],
            "commercial_boundary": {
                "contract_execution_recorded": True,
                "contract_executed": True,
                "invoice_created": False,
                "payment_requested": False,
                "paid_assessment_authorized": False,
                (
                    "production_onboarding_"
                    "authorized"
                ): False,
                "requires_separate_invoice": True,
                (
                    "requires_separate_"
                    "payment_confirmation"
                ): True,
                (
                    "requires_final_paid_"
                    "work_authorization"
                ): True,
                (
                    "requires_separate_"
                    "production_onboarding"
                ): True,
            },
            "governance_boundary": {
                "deterministic_status_required": True,
                "gagf_kernel_authoritative": True,
                "ai_override_allowed": False,
                "human_boundary_required": True,
                "release_marker_preserved": True,
                (
                    "contract_execution_event_"
                    "is_not_invoice"
                ): True,
                (
                    "contract_execution_event_"
                    "is_not_payment"
                ): True,
                (
                    "contract_execution_event_"
                    "is_not_paid_work_authorization"
                ): True,
            },
        }

    def _build_authorization(
        self,
        *,
        tenant_id: str,
        metadata:
            PreliveAssessmentExecutionMetadata,
        scenario_id: str,
        timestamp: str,
        operator_id: str,
    ) -> PaidAssessmentWorkAuthorization:
        return PaidAssessmentWorkAuthorization(
            authorization_id=(
                f"paid-work-auth-{scenario_id}"
            ),
            tenant_id=tenant_id,
            client_id=metadata.client_id,
            engagement_id=(
                metadata.engagement_id
            ),
            assessment_id=(
                metadata.assessment_id
            ),
            contract_execution_event_id=(
                f"contract-event-{scenario_id}"
            ),
            authorized_by=operator_id,
            authorized_at=timestamp,
            paid_assessment_authorized=True,
        )

    def _write_outputs(
        self,
        *,
        output_path: Path,
        scenario: Mapping[str, Any],
        oracle: Mapping[str, Any],
        result:
            PreliveBlindAssessmentRunResult,
    ) -> None:
        self._write_json(
            output_path
            / "scenario_input.json",
            scenario,
        )

        self._write_json(
            output_path
            / "oracle_unsealed.json",
            oracle,
        )

        self._write_json(
            output_path
            / "execution_result.json",
            result.execution.to_dict(),
        )

        self._write_json(
            output_path
            / "verification.json",
            result.verification.to_dict(),
        )

        self._write_json(
            output_path
            / "scoring.json",
            result.scoring.to_dict(),
        )

        self._write_json(
            output_path
            / "run_summary.json",
            self._summary_payload(
                result
            ),
        )

    def _summary_payload(
        self,
        result:
            PreliveBlindAssessmentRunResult,
    ) -> dict[str, Any]:
        score = result.scoring

        return {
            "test_program":
                PRELIVE_PROGRAM,
            "run_status":
                result.run_status,
            "authority":
                result.authority,
            "runner_version":
                result.runner_version,
            "scenario_id":
                result.scenario_id,
            "scenario_sha256":
                result.scenario_sha256,
            "verification_hash":
                result.verification
                .verification_hash,
            "scoring_hash":
                score.scoring_hash,
            "repository_chain_valid":
                result.verification
                .repository_chain_valid,
            "oracle_leakage_detected":
                result.verification
                .oracle_leakage_detected,
            "true_positives":
                list(
                    score.true_positives
                ),
            "false_positives":
                list(
                    score.false_positives
                ),
            "false_negatives":
                list(
                    score.false_negatives
                ),
            "precision":
                score.precision,
            "recall":
                score.recall,
            "f1":
                score.f1,
            "exact_condition_match":
                score.exact_condition_match,
            "event_count_accuracy":
                score.event_count_accuracy,
            "band_accuracy":
                score.band_accuracy,
            "dominant_constraint_match":
                score.dominant_constraint_match,
            "customer_outcome_verified":
                False,
            "production_onboarding_authorized":
                False,
        }

    def _write_json(
        self,
        path: Path,
        payload: Mapping[str, Any],
    ) -> None:
        path.write_text(
            json.dumps(
                dict(payload),
                indent=2,
                sort_keys=True,
                ensure_ascii=False,
            )
            + "\n",
            encoding="utf-8",
        )