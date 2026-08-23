from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from backend.app.gagf.governance_real_paid_assessment_client_response import (
    GovernanceRealPaidAssessmentClientResponseService,
)


def _load_json_object(
    path: Path,
    field_name: str,
) -> dict[str, Any]:
    if not path.exists():
        raise RuntimeError(
            f"{field_name} does not exist: {path}"
        )

    if not path.is_file():
        raise RuntimeError(
            f"{field_name} is not a file: {path}"
        )

    try:
        payload = json.loads(
            path.read_text(
                encoding="utf-8"
            )
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(
            f"{field_name} is not valid UTF-8 JSON"
        ) from exc

    if not isinstance(payload, dict):
        raise RuntimeError(
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

    serialized = json.dumps(
        payload,
        indent=2,
        sort_keys=True,
    )

    with path.open(
        "x",
        encoding="utf-8",
        newline="\n",
    ) as handle:
        handle.write(serialized)
        handle.write("\n")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Record an explicit client response for a real paid "
            "assessment after governed client receipt acknowledgment."
        )
    )

    parser.add_argument(
        "--database",
        required=True,
        help="Canonical paid-assessment SQLite database.",
    )

    parser.add_argument(
        "--acknowledged-json",
        required=True,
        help=(
            "Serialized PILOT-009 durable client-receipt "
            "acknowledgment JSON."
        ),
    )

    parser.add_argument(
        "--client-response-json",
        required=True,
        help=(
            "Separate explicit client findings/recommendations "
            "response evidence JSON."
        ),
    )

    parser.add_argument(
        "--output-json",
        required=True,
        help=(
            "Exclusive output path for the governed real "
            "client-response result."
        ),
    )

    return parser


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()

    database_path = Path(
        args.database
    ).resolve()

    acknowledged_path = Path(
        args.acknowledged_json
    ).resolve()

    response_path = Path(
        args.client_response_json
    ).resolve()

    output_path = Path(
        args.output_json
    ).resolve()

    try:
        if output_path.exists():
            raise RuntimeError(
                f"output path already exists: {output_path}"
            )

        acknowledged_payload = _load_json_object(
            acknowledged_path,
            "acknowledged_json",
        )

        response_payload = _load_json_object(
            response_path,
            "client_response_json",
        )

        result = (
            GovernanceRealPaidAssessmentClientResponseService()
            .record(
                database_path=database_path,
                acknowledged_payload=acknowledged_payload,
                response_payload=response_payload,
            )
        )

        output_payload = {
            "client_response_recording_passed": True,
            "client_response_recorded": True,
            "result": result.to_dict(),
            "boundaries": {
                "receipt_does_not_imply_client_response": True,
                "client_response_evidence_must_preexist_command": True,
                "command_does_not_infer_response_from_receipt": True,
                "pa007_remains_client_response_authority": True,
                "pa013_remains_operator_coordination_authority": True,
                "pa012_remains_lifecycle_persistence_authority": True,
                "findings_disposition_is_not_intervention_authority": True,
                "recommendation_acceptance_is_not_implementation": True,
                "client_response_is_not_intervention_authorization": True,
                "client_response_is_not_execution": True,
                "client_response_is_not_remediation_success": True,
                "client_response_is_not_roi_verification": True,
                "client_response_is_not_customer_outcome": True,
                "client_response_is_not_administrative_closeout": True,
            },
        }

        _write_json_exclusive(
            output_path,
            output_payload,
        )

        return 0

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


if __name__ == "__main__":
    raise SystemExit(main())