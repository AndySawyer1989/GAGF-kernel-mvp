from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from backend.app.gagf.governance_real_paid_assessment_preflight import (
    GovernanceRealPaidAssessmentPreflightService,
)
from scripts.run_real_paid_assessment import (
    _build_governed_inputs,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Evaluate first-real-paid-assessment operational "
            "readiness without executing the assessment."
        )
    )

    parser.add_argument(
        "--database",
        required=True,
    )
    parser.add_argument(
        "--intake-json",
        required=True,
    )
    parser.add_argument(
        "--authorization-json",
        required=True,
    )
    parser.add_argument(
        "--contract-event-json",
        required=True,
    )
    parser.add_argument(
        "--request-json",
        required=True,
    )
    parser.add_argument(
        "--evidence-approvals-json",
        required=True,
    )
    parser.add_argument(
        "--output-json",
        required=False,
    )

    return parser


def _error_payload(message: str) -> dict[str, Any]:
    return {
        "preflight_passed": False,
        "error": message,
        "boundaries": {
            "preflight_is_not_paid_work_authorization": True,
            "preflight_is_not_execution": True,
            "preflight_is_not_execution_authority": True,
            "preflight_is_not_recovery_authority": True,
        },
    }


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    database_path = Path(args.database)

    output_path = (
        None
        if not args.output_json
        else Path(args.output_json)
    )

    # Preflight evidence must never overwrite an existing result.
    if output_path is not None and output_path.exists():
        print(
            json.dumps(
                _error_payload(
                    "output JSON already exists; refusing to "
                    f"overwrite preflight evidence: {output_path}"
                ),
                indent=2,
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return 1

    try:
        (
            intake,
            bridge,
            authorization,
            request,
            evidence_binding,
            contract_event,
        ) = _build_governed_inputs(
            database_path=database_path,
            intake_json_path=Path(args.intake_json),
            authorization_json_path=Path(
                args.authorization_json
            ),
            contract_event_json_path=Path(
                args.contract_event_json
            ),
            request_json_path=Path(args.request_json),
            evidence_approvals_json_path=Path(
                args.evidence_approvals_json
            ),
        )

        result = (
            GovernanceRealPaidAssessmentPreflightService()
            .evaluate(
                database_path=database_path,
                intake=intake,
                authorization_bridge=bridge,
                evidence_binding=evidence_binding,
                contract_execution_event=contract_event,
                paid_work_authorization=authorization,
                request=request,
            )
        )
    except Exception as exc:
        print(
            json.dumps(
                _error_payload(
                    "governed real paid-assessment preflight "
                    f"failure: {type(exc).__name__}: {exc}"
                ),
                indent=2,
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return 1

    payload = {
        "preflight_passed": (
            result.ready_for_operator_execution
        ),
        "result": result.to_dict(),
        "boundaries": {
            "preflight_is_not_paid_work_authorization": True,
            "preflight_is_not_execution": True,
            "preflight_is_not_execution_authority": True,
            "preflight_is_not_recovery_authority": True,
            "ready_does_not_mean_executed": True,
            "pa015_remains_operator_execution_entry_point": True,
        },
    }

    serialized = json.dumps(
        payload,
        indent=2,
        sort_keys=True,
    )

    if result.ready_for_operator_execution:
        print(serialized)
    else:
        print(
            serialized,
            file=sys.stderr,
        )

    if output_path is not None:
        if output_path.parent and not output_path.parent.exists():
            output_path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

        try:
            with output_path.open(
                "x",
                encoding="utf-8",
                newline="\n",
            ) as output_file:
                output_file.write(
                    serialized + "\n"
                )
        except FileExistsError:
            print(
                json.dumps(
                    _error_payload(
                        "output JSON appeared during preflight; "
                        "refusing to overwrite evidence: "
                        f"{output_path}"
                    ),
                    indent=2,
                    sort_keys=True,
                ),
                file=sys.stderr,
            )
            return 1

    if result.ready_for_operator_execution:
        return 0

    return 2


if __name__ == "__main__":
    raise SystemExit(main())