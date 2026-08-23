from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from backend.app.gagf.governance_first_real_paid_assessment_execution_readiness import (
    GovernanceFirstRealPaidAssessmentExecutionReadinessService,
)
from scripts.run_real_paid_assessment import (
    _build_governed_inputs,
)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Evaluate whether the first controlled real paid assessment "
            "is ready for governed execution without executing it."
        )
    )

    parser.add_argument(
        "--database",
        required=True,
        help="Target SQLite database for the controlled assessment.",
    )

    parser.add_argument(
        "--intake-json",
        required=True,
        help="Real paid-assessment intake JSON.",
    )

    parser.add_argument(
        "--authorization-json",
        required=True,
        help="Paid-work authorization JSON.",
    )

    parser.add_argument(
        "--contract-event-json",
        required=True,
        help="Contract-execution event JSON.",
    )

    parser.add_argument(
        "--request-json",
        required=True,
        help="Assessment execution request JSON.",
    )

    parser.add_argument(
        "--evidence-approvals-json",
        required=True,
        help="Execution-evidence approvals JSON.",
    )

    parser.add_argument(
        "--output-json",
        required=True,
        help=(
            "Exclusive output path for the consolidated "
            "PILOT-012 readiness artifact."
        ),
    )

    return parser


def _require_input_file(
    value: str,
    field_name: str,
) -> Path:
    path = Path(value)

    if not str(path).strip():
        raise ValueError(
            f"{field_name} is required"
        )

    if not path.exists():
        raise ValueError(
            f"{field_name} does not exist: {path}"
        )

    if not path.is_file():
        raise ValueError(
            f"{field_name} is not a file: {path}"
        )

    return path


def _write_json_exclusive(
    path: Path,
    payload: dict[str, Any],
) -> None:
    if path.exists():
        raise FileExistsError(
            "output JSON already exists; refusing to overwrite "
            f"PILOT-012 readiness evidence: {path}"
        )

    if path.parent and not path.parent.exists():
        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

    serialized = json.dumps(
        payload,
        indent=2,
        sort_keys=True,
    )

    try:
        with path.open(
            "x",
            encoding="utf-8",
            newline="\n",
        ) as output_file:
            output_file.write(
                serialized + "\n"
            )
    except FileExistsError as exc:
        raise FileExistsError(
            "output JSON appeared during PILOT-012 readiness "
            f"evaluation; refusing overwrite: {path}"
        ) from exc


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()

    try:
        output_path = Path(
            args.output_json
        )

        # Output collision is checked before any governed
        # input construction or readiness evaluation.
        if output_path.exists():
            raise FileExistsError(
                "output JSON already exists; refusing to overwrite "
                f"PILOT-012 readiness evidence: {output_path}"
            )

        intake_path = _require_input_file(
            args.intake_json,
            "intake_json",
        )

        authorization_path = _require_input_file(
            args.authorization_json,
            "authorization_json",
        )

        contract_event_path = _require_input_file(
            args.contract_event_json,
            "contract_event_json",
        )

        request_path = _require_input_file(
            args.request_json,
            "request_json",
        )

        evidence_approvals_path = _require_input_file(
            args.evidence_approvals_json,
            "evidence_approvals_json",
        )

        database_path = Path(
            args.database
        )

        (
            intake,
            authorization_bridge,
            paid_work_authorization,
            request,
            evidence_binding,
            contract_execution_event,
        ) = _build_governed_inputs(
            database_path=database_path,
            intake_json_path=intake_path,
            authorization_json_path=authorization_path,
            contract_event_json_path=contract_event_path,
            request_json_path=request_path,
            evidence_approvals_json_path=evidence_approvals_path,
        )

        result = (
            GovernanceFirstRealPaidAssessmentExecutionReadinessService()
            .evaluate(
                database_path=database_path,
                intake=intake,
                authorization_bridge=authorization_bridge,
                evidence_binding=evidence_binding,
                contract_execution_event=contract_execution_event,
                paid_work_authorization=paid_work_authorization,
                request=request,
            )
        )

        payload = {
            "first_real_execution_readiness_evaluated": True,
            "ready_for_controlled_execution": (
                result.ready_for_controlled_execution
            ),
            "status": result.status,
            "required_operator_action": (
                result.required_operator_action
            ),
            "result": result.to_dict(),
            "boundaries": {
                "pilot012_is_read_only": True,
                "readiness_evaluation_is_not_execution": True,
                "ready_is_not_execution_authority": True,
                "blocked_is_a_governed_result_not_an_execution_failure": True,
                "paid_work_authorization_remains_external": True,
                "authorization_bridge_remains_existing_authority": True,
                "execution_evidence_binding_remains_existing_authority": True,
                "preflight_remains_existing_execution_readiness_authority": True,
                "pa015_or_governed_recovery_remains_execution_path": True,
                "no_database_created_by_pilot012": True,
                "no_delivery_authority_created": True,
                "no_intervention_authority_created": True,
                "no_outcome_claim_created": True,
            },
        }

        _write_json_exclusive(
            output_path,
            payload,
        )

        print(
            json.dumps(
                payload,
                indent=2,
                sort_keys=True,
            )
        )

        # READY and BLOCKED are both valid governed evaluations.
        # Structural/IO failures alone produce a non-zero exit.
        return 0

    except Exception as exc:
        error_payload = {
            "first_real_execution_readiness_evaluated": False,
            "error": str(exc),
            "error_type": type(exc).__name__,
        }

        print(
            json.dumps(
                error_payload,
                sort_keys=True,
            ),
            file=sys.stderr,
        )

        return 1


if __name__ == "__main__":
    raise SystemExit(main())