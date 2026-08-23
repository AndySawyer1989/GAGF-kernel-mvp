from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from backend.app.gagf.governance_real_paid_assessment_client_receipt import (
    GovernanceRealPaidAssessmentClientReceiptService,
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
            "Record explicit client receipt acknowledgment "
            "for a durably delivered real paid assessment."
        )
    )

    parser.add_argument(
        "--database",
        required=True,
        help="Canonical paid-assessment SQLite database.",
    )

    parser.add_argument(
        "--delivered-json",
        required=True,
        help=(
            "Serialized PILOT-008 durable delivery-recording "
            "result JSON."
        ),
    )

    parser.add_argument(
        "--client-receipt-json",
        required=True,
        help=(
            "Separate explicit client receipt-acknowledgment "
            "evidence JSON."
        ),
    )

    parser.add_argument(
        "--output-json",
        required=True,
        help=(
            "Exclusive output path for the governed real "
            "client-receipt result."
        ),
    )

    return parser


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()

    database_path = Path(
        args.database
    ).resolve()

    delivered_path = Path(
        args.delivered_json
    ).resolve()

    receipt_path = Path(
        args.client_receipt_json
    ).resolve()

    output_path = Path(
        args.output_json
    ).resolve()

    try:
        if output_path.exists():
            raise RuntimeError(
                f"output path already exists: {output_path}"
            )

        delivered_payload = _load_json_object(
            delivered_path,
            "delivered_json",
        )

        receipt_payload = _load_json_object(
            receipt_path,
            "client_receipt_json",
        )

        result = (
            GovernanceRealPaidAssessmentClientReceiptService()
            .record(
                database_path=database_path,
                delivered_payload=delivered_payload,
                receipt_payload=receipt_payload,
            )
        )

        output_payload = {
            "client_receipt_recording_passed": True,
            "client_receipt_acknowledged": True,
            "result": result.to_dict(),
            "boundaries": {
                "delivery_does_not_imply_client_receipt": True,
                "client_receipt_evidence_must_preexist_command": True,
                "command_does_not_infer_receipt_from_delivery": True,
                "pa006_remains_client_acknowledgment_authority": True,
                "pa013_remains_operator_coordination_authority": True,
                "pa012_remains_lifecycle_persistence_authority": True,
                "client_receipt_is_not_client_response": True,
                "client_receipt_is_not_findings_acceptance": True,
                "client_receipt_is_not_recommendation_acceptance": True,
                "client_receipt_is_not_intervention_authorization": True,
                "client_receipt_is_not_customer_outcome": True,
            },
        }

        _write_json_exclusive(
            output_path,
            output_payload,
        )

        return 0

    except Exception as exc:
        error_payload = {
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