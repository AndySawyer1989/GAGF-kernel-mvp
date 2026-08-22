"""Governed human-delivery approval handoff for a real paid assessment.

PILOT-007 CLI.

This command:
- verifies the completed PA015 execution through PILOT-006;
- reads a separately supplied human approval artifact;
- delegates approval binding to PILOT-007;
- delegates delivery-envelope authority to existing PA003;
- emits approved_for_human_delivery evidence.

It does not:
- authorize paid work;
- execute or recover an assessment;
- manufacture human approval;
- default approval decisions to True;
- deliver or send the report;
- create a delivery event;
- record client receipt;
- establish client acceptance or customer outcome.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from backend.app.gagf.governance_real_paid_assessment_delivery_approval_handoff import (
    GovernanceRealPaidAssessmentDeliveryApprovalHandoffService,
)
from backend.app.gagf.governance_real_paid_assessment_delivery_readiness import (
    GovernanceRealPaidAssessmentDeliveryReadinessService,
)


def _load_json_object(
    path: Path,
    *,
    field_name: str,
) -> dict[str, Any]:
    if not path.exists():
        raise ValueError(
            f"{field_name} does not exist: {path}"
        )

    if not path.is_file():
        raise ValueError(
            f"{field_name} is not a file: {path}"
        )

    try:
        payload = json.loads(
            path.read_text(
                encoding="utf-8"
            )
        )
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(
            f"{field_name} is not valid UTF-8 JSON"
        ) from exc

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
    ) as stream:
        json.dump(
            payload,
            stream,
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
        )
        stream.write("\n")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Bind explicit human delivery approval to a verified "
            "real paid assessment and produce the existing PA003 "
            "approved-for-human-delivery envelope."
        )
    )

    parser.add_argument(
        "--database",
        required=True,
        help="Canonical paid-assessment SQLite database.",
    )

    parser.add_argument(
        "--operator-result-json",
        required=True,
        help="Successful PA015 operator result JSON.",
    )

    parser.add_argument(
        "--human-approval-json",
        required=True,
        help=(
            "Separate explicit human delivery approval JSON. "
            "All four approval decisions must already be true."
        ),
    )

    parser.add_argument(
        "--output-json",
        required=True,
        help=(
            "New output path for the governed "
            "approved-for-human-delivery result."
        ),
    )

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    database_path = Path(args.database).resolve()
    operator_result_path = Path(
        args.operator_result_json
    ).resolve()
    human_approval_path = Path(
        args.human_approval_json
    ).resolve()
    output_path = Path(
        args.output_json
    ).resolve()

    # Preserve existing operator evidence exactly.
    if output_path.exists():
        print(
            json.dumps(
                {
                    "error": (
                        "output path already exists; refusing "
                        "to overwrite"
                    ),
                    "output_json": str(output_path),
                },
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return 1

    try:
        operator_payload = _load_json_object(
            operator_result_path,
            field_name="operator_result_json",
        )

        approval_payload = _load_json_object(
            human_approval_path,
            field_name="human_approval_json",
        )

        readiness = (
            GovernanceRealPaidAssessmentDeliveryReadinessService()
            .verify(
                database_path=database_path,
                operator_payload=operator_payload,
            )
        )

        result = (
            GovernanceRealPaidAssessmentDeliveryApprovalHandoffService()
            .handoff(
                readiness=readiness,
                approval_payload=approval_payload,
            )
        )

        payload = {
            "operator_handoff_passed": True,
            "approved_for_human_delivery": True,
            "result": result.to_dict(),
            "boundaries": {
                "command_is_not_paid_work_authorization": True,
                "command_is_not_assessment_execution_authority": True,
                "command_is_not_recovery_authority": True,
                "human_approval_must_preexist_command": True,
                "command_does_not_manufacture_human_approval": True,
                "pa003_remains_delivery_envelope_authority": True,
                "approved_for_human_delivery_is_not_delivery": True,
                "command_does_not_create_delivery_event": True,
                "command_does_not_record_client_receipt": True,
                "command_does_not_establish_client_acceptance": True,
                "command_does_not_establish_customer_outcome": True,
            },
        }

        _write_json_exclusive(
            output_path,
            payload,
        )

    except Exception as exc:
        print(
            json.dumps(
                {
                    "error": str(exc),
                    "error_type": type(exc).__name__,
                },
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())