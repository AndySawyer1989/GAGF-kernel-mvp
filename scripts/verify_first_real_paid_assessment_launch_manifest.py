from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from backend.app.gagf.governance_first_real_paid_assessment_execution_readiness import (
    GovernanceFirstRealPaidAssessmentExecutionReadinessService,
)
from backend.app.gagf.governance_first_real_paid_assessment_launch_manifest import (
    GovernanceFirstRealPaidAssessmentLaunchManifestService,
)
from scripts.run_real_paid_assessment import (
    _build_governed_inputs,
)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Evaluate the first real paid assessment launch manifest. "
            "This command is read-only and does not execute PA015."
        )
    )

    parser.add_argument(
        "--database",
        required=True,
        help="Fresh assessment database path.",
    )

    parser.add_argument(
        "--intake-json",
        required=True,
        help="Real paid assessment intake JSON.",
    )

    parser.add_argument(
        "--authorization-json",
        required=True,
        help="Final paid-work authorization JSON.",
    )

    parser.add_argument(
        "--contract-event-json",
        required=True,
        help="Contract execution event JSON.",
    )

    parser.add_argument(
        "--request-json",
        required=True,
        help="Assessment execution request JSON.",
    )

    parser.add_argument(
        "--evidence-approvals-json",
        required=True,
        help="Execution evidence approvals JSON.",
    )

    parser.add_argument(
        "--payment-confirmation-json",
        required=True,
        help=(
            "Recorded Assessment Factory Lite payment confirmation "
            "event JSON."
        ),
    )

    parser.add_argument(
        "--output-json",
        required=True,
        help="Exclusive output path for the PILOT-013 manifest.",
    )

    return parser


def _require_input_file(
    path: Path,
    field_name: str,
) -> None:
    if not path.exists():
        raise FileNotFoundError(
            f"{field_name} does not exist: {path}"
        )

    if not path.is_file():
        raise ValueError(
            f"{field_name} must be a file: {path}"
        )


def _load_json_object(
    path: Path,
    field_name: str,
) -> dict[str, Any]:
    _require_input_file(path, field_name)

    with path.open(
        "r",
        encoding="utf-8-sig",
    ) as handle:
        payload = json.load(handle)

    if not isinstance(payload, dict):
        raise ValueError(
            f"{field_name} must contain a JSON object"
        )

    return payload


def _write_json_exclusive(
    path: Path,
    payload: dict[str, Any],
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with path.open(
        "x",
        encoding="utf-8",
        newline="\n",
    ) as handle:
        json.dump(
            payload,
            handle,
            indent=2,
            sort_keys=True,
        )
        handle.write("\n")


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    database_path = Path(args.database)

    intake_path = Path(args.intake_json)
    authorization_path = Path(args.authorization_json)
    contract_event_path = Path(args.contract_event_json)
    request_path = Path(args.request_json)
    evidence_approvals_path = Path(
        args.evidence_approvals_json
    )
    payment_confirmation_path = Path(
        args.payment_confirmation_json
    )
    output_path = Path(args.output_json)

    try:
        # Fail before governed input construction if output already exists.
        if output_path.exists():
            raise FileExistsError(
                f"output_json already exists: {output_path}"
            )

        for path, field_name in (
            (intake_path, "intake_json"),
            (authorization_path, "authorization_json"),
            (contract_event_path, "contract_event_json"),
            (request_path, "request_json"),
            (
                evidence_approvals_path,
                "evidence_approvals_json",
            ),
            (
                payment_confirmation_path,
                "payment_confirmation_json",
            ),
        ):
            _require_input_file(
                path,
                field_name,
            )

        payment_confirmation_event = _load_json_object(
            payment_confirmation_path,
            "payment_confirmation_json",
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
            evidence_approvals_json_path=(
                evidence_approvals_path
            ),
        )

        execution_readiness = (
            GovernanceFirstRealPaidAssessmentExecutionReadinessService()
            .evaluate(
                database_path=database_path,
                intake=intake,
                authorization_bridge=authorization_bridge,
                evidence_binding=evidence_binding,
                contract_execution_event=(
                    contract_execution_event
                ),
                paid_work_authorization=(
                    paid_work_authorization
                ),
                request=request,
            )
        )

        manifest = (
            GovernanceFirstRealPaidAssessmentLaunchManifestService()
            .build_manifest(
                contract_execution_event=(
                    contract_execution_event
                ),
                payment_confirmation_event=(
                    payment_confirmation_event
                ),
                paid_work_authorization=(
                    paid_work_authorization
                ),
                authorization_bridge=(
                    authorization_bridge
                ),
                execution_readiness=(
                    execution_readiness
                ),
            )
        )

        payload = {
            "first_real_paid_assessment_launch_manifest_evaluated": True,
            "ready_for_human_launch_review": (
                manifest.ready_for_human_launch_review
            ),
            "status": manifest.status,
            "required_operator_action": (
                manifest.required_operator_action
            ),
            "result": manifest.to_dict(),
            "boundaries": {
                "pilot013_is_read_only": True,
                "manifest_evaluation_is_not_execution": True,
                "launch_ready_is_not_execution_authority": True,
                "launch_ready_is_not_human_launch_approval": True,
                "payment_confirmation_is_not_paid_work_authorization": True,
                "paid_work_authorization_remains_independent": True,
                "pilot012_remains_execution_readiness_authority": True,
                "pa015_remains_execution_entry_point": True,
                "no_commercial_event_created": True,
                "no_paid_work_authorization_created": True,
                "no_execution_performed": True,
                "no_delivery_performed": True,
                "no_customer_outcome_claimed": True,
                "blocked_is_a_governed_result_not_an_execution_failure": True,
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

        # READY and BLOCKED are both successful governed evaluations.
        return 0

    except Exception as exc:
        print(
            f"PILOT-013 launch manifest evaluation failed: {exc}",
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())