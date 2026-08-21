from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

from backend.app.gagf.governance_assessment_isolation import (
    CommercialHierarchyContext,
)
from backend.app.gagf.governance_assessment_repository import (
    GovernanceAssessmentRepository,
)


SCRIPT_PATH = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "run_real_paid_assessment.py"
)


CSV_TEXT = (
    "event_id,event_type,occurred_at,work_item_id\n"
    "event-001,APPROVAL_DELAYED,"
    "2026-01-01T12:00:00Z,TICKET-1\n"
    "event-002,APPROVAL_DELAYED,"
    "2026-01-01T13:00:00Z,TICKET-2\n"
    "event-003,WORK_BLOCKED,"
    "2026-01-02T12:00:00Z,TICKET-3\n"
    "event-004,ESCALATION,"
    "2026-01-03T12:00:00Z,TICKET-4\n"
)


def load_runner():
    spec = importlib.util.spec_from_file_location(
        "run_real_paid_assessment_pa015",
        SCRIPT_PATH,
    )

    assert spec is not None
    assert spec.loader is not None

    module = importlib.util.module_from_spec(spec)

    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    return module


def write_json(path: Path, payload) -> None:
    path.write_text(
        json.dumps(
            payload,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )


def build_contract_event():
    return {
        "status": "ok",
        "event_type": (
            "assessment_factory_lite_contract_execution_event"
        ),
        "package_name": "assessment_factory_lite",
        "release": (
            "assessment-factory-lite-scope-call-conversion"
        ),
        "version": "2.3.0",
        "event_stage": "contract_execution",
        "event_status": "contract_executed",
        "contract_execution_event_id": (
            "contract-event-real-001"
        ),
        "recorded_at": "2026-08-20T18:30:00+00:00",
        "execution_evidence": {
            "executed_contract_reference": (
                "contract-ref-real-001"
            ),
            "executed_at": "2026-08-20T18:25:00+00:00",
            "executed_contract_reference_recorded": True,
            "executed_at_recorded": True,
            "contract_execution_confirmed": True,
            "contract_executed": True,
        },
        "event_checklist": {
            "contract_execution_review_ready": True,
            "contract_execution_confirmed": True,
            "executed_contract_reference_recorded": True,
            "executed_at_recorded": True,
            "execution_method_recorded": True,
            "all_required_signatures_recorded": True,
            "human_operator_confirmed_execution": True,
            "signature_record_is_not_invoice": True,
            "signature_record_is_not_payment": True,
            "invoice_not_created": True,
            "payment_not_requested": True,
            "paid_assessment_not_authorized": True,
            "production_onboarding_not_started": True,
        },
        "event_blockers": [],
        "commercial_boundary": {
            "contract_execution_recorded": True,
            "contract_executed": True,
            "invoice_created": False,
            "payment_requested": False,
            "paid_assessment_authorized": False,
            "production_onboarding_authorized": False,
            "requires_separate_invoice": True,
            "requires_separate_payment_confirmation": True,
            "requires_final_paid_work_authorization": True,
            "requires_separate_production_onboarding": True,
        },
        "governance_boundary": {
            "deterministic_status_required": True,
            "gagf_kernel_authoritative": True,
            "ai_override_allowed": False,
            "human_boundary_required": True,
            "release_marker_preserved": True,
            "contract_execution_event_is_not_invoice": True,
            "contract_execution_event_is_not_payment": True,
            (
                "contract_execution_event_is_not_paid_work_authorization"
            ): True,
        },
    }


def build_operator_files(tmp_path: Path):
    database_path = tmp_path / "assessment.sqlite3"
    csv_path = tmp_path / "evidence.csv"

    csv_path.write_text(
        CSV_TEXT,
        encoding="utf-8",
        newline="",
    )

    csv_hash = hashlib.sha256(
        CSV_TEXT.encode("utf-8")
    ).hexdigest()

    intake_path = tmp_path / "intake.json"
    authorization_path = tmp_path / "authorization.json"
    contract_event_path = tmp_path / "contract-event.json"
    request_path = tmp_path / "request.json"
    approvals_path = tmp_path / "approvals.json"

    write_json(
        intake_path,
        {
            "tenant_id": "tenant-alpha",
            "client_id": "client-acme",
            "engagement_id": "engagement-001",
            "assessment_id": "assessment-001",
            "client_display_name": "ACME Corporation",
            "assessment_name": (
                "Governance Runway Assessment"
            ),
            "operator_name": "FIP Operator",
            "client_contact_name": "Client Representative",
            "assessment_scope_confirmed": True,
            "evidence_scope_confirmed": True,
            "client_data_use_confirmed": True,
            "operator_readiness_confirmed": True,
            "evidence": [
                {
                    "evidence_id": "source-001",
                    "source_kind": "csv",
                    "description": "Redacted workflow export",
                    "classification": "redacted",
                    "client_authorized_for_assessment": True,
                    "minimization_review_completed": True,
                    "direct_identifiers_removed": True,
                }
            ],
            "storage": {
                "repository_path": str(database_path),
                "operator_controlled_location": True,
                "access_restricted": True,
                "storage_protection_confirmed": True,
                "backup_plan_recorded": True,
                "retention_period_recorded": True,
                "deletion_plan_recorded": True,
            },
        },
    )

    write_json(
        authorization_path,
        {
            "authorization_id": "paid-work-auth-real-001",
            "tenant_id": "tenant-alpha",
            "client_id": "client-acme",
            "engagement_id": "engagement-001",
            "assessment_id": "assessment-001",
            "contract_execution_event_id": (
                "contract-event-real-001"
            ),
            "authorized_by": "FIP Operator",
            "authorized_at": "2026-08-20T18:35:00+00:00",
            "paid_assessment_authorized": True,
        },
    )

    write_json(
        contract_event_path,
        build_contract_event(),
    )

    write_json(
        request_path,
        {
            "assessment_name": (
                "Governance Runway Assessment"
            ),
            "workflow_names": [
                "Incident Management"
            ],
            "organizational_units": [
                "IT Operations"
            ],
            "period_start": "2026-01-01",
            "period_end": "2026-06-30",
            "objectives": [
                "Reduce governance friction"
            ],
            "expected_outcomes": [
                "Faster completion"
            ],
            "evidence_requirements": [
                {
                    "requirement_id": "required-csv",
                    "source_kind": "csv",
                    "description": "Workflow evidence",
                    "required": True,
                    "minimum_record_count": 4,
                }
            ],
            "evidence_inputs": [
                {
                    "source_id": "source-001",
                    "kind": "csv",
                    "display_name": (
                        "Redacted Workflow Export"
                    ),
                    "csv_path": csv_path.name,
                }
            ],
            "client_display_name": "ACME Corporation",
            "prepared_by": "FIP Operator",
            "exclusions": [],
            "maximum_priorities": 3,
        },
    )

    write_json(
        approvals_path,
        {
            "approvals": [
                {
                    "evidence_id": "source-001",
                    "approved_content_sha256": csv_hash,
                    "approved_by": "FIP Operator",
                    "approved_at": (
                        "2026-08-20T18:40:00+00:00"
                    ),
                    "execution_evidence_approved": True,
                }
            ]
        },
    )

    return {
        "database": database_path,
        "csv": csv_path,
        "intake": intake_path,
        "authorization": authorization_path,
        "contract_event": contract_event_path,
        "request": request_path,
        "approvals": approvals_path,
    }


def run_main(
    monkeypatch,
    *,
    files,
    output_path: Path | None = None,
):
    runner = load_runner()

    arguments = [
        str(SCRIPT_PATH),
        "--database",
        str(files["database"]),
        "--intake-json",
        str(files["intake"]),
        "--authorization-json",
        str(files["authorization"]),
        "--contract-event-json",
        str(files["contract_event"]),
        "--request-json",
        str(files["request"]),
        "--evidence-approvals-json",
        str(files["approvals"]),
    ]

    if output_path is not None:
        arguments.extend(
            [
                "--output-json",
                str(output_path),
            ]
        )

    monkeypatch.setattr(
        sys,
        "argv",
        arguments,
    )

    exit_code = runner.main()

    return runner, exit_code


def artifact_rows(database_path: Path):
    repository = GovernanceAssessmentRepository(
        database_path
    )

    context = CommercialHierarchyContext(
        tenant_id="tenant-alpha",
        client_id="client-acme",
        engagement_id="engagement-001",
        assessment_id="assessment-001",
    )

    artifacts = repository.list_artifacts(
        context=context
    )

    return [
        (
            artifact.artifact_id,
            artifact.artifact_type,
            artifact.artifact_hash,
            artifact.sequence_number,
        )
        for artifact in artifacts
    ]


def test_fresh_operator_execution_produces_ten_artifacts(
    tmp_path,
    monkeypatch,
    capsys,
):
    files = build_operator_files(tmp_path)
    output_path = tmp_path / "result.json"

    _, exit_code = run_main(
        monkeypatch,
        files=files,
        output_path=output_path,
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert captured.err == ""
    assert output_path.exists()

    payload = json.loads(output_path.read_text(
        encoding="utf-8"
    ))

    assert payload["operator_run_passed"] is True
    assert payload["result"]["disposition"] == "executed"
    assert payload["result"]["artifact_count_before"] == 0
    assert payload["result"]["artifact_count_after"] == 10

    assert (
        payload["boundaries"][
            "operator_command_is_not_paid_work_authorization"
        ]
        is True
    )
    assert (
        payload["boundaries"][
            "operator_command_is_not_execution_authority"
        ]
        is True
    )
    assert (
        payload["boundaries"][
            "recovery_service_remains_governed_authority_path"
        ]
        is True
    )

    assert len(artifact_rows(files["database"])) == 10


def test_completed_exact_retry_reconciles_without_duplicates(
    tmp_path,
    monkeypatch,
    capsys,
):
    files = build_operator_files(tmp_path)

    first_output = tmp_path / "first.json"

    _, first_exit = run_main(
        monkeypatch,
        files=files,
        output_path=first_output,
    )

    capsys.readouterr()

    assert first_exit == 0

    before = artifact_rows(files["database"])

    second_output = tmp_path / "second.json"

    _, second_exit = run_main(
        monkeypatch,
        files=files,
        output_path=second_output,
    )

    capsys.readouterr()

    assert second_exit == 0

    payload = json.loads(second_output.read_text(
        encoding="utf-8"
    ))

    assert payload["result"]["disposition"] == "reconciled"
    assert payload["result"]["artifact_count_before"] == 10
    assert payload["result"]["artifact_count_after"] == 10

    after = artifact_rows(files["database"])

    assert after == before


def test_wrong_evidence_hash_fails_before_database_creation(
    tmp_path,
    monkeypatch,
    capsys,
):
    files = build_operator_files(tmp_path)

    approvals = json.loads(
        files["approvals"].read_text(
            encoding="utf-8"
        )
    )

    approvals["approvals"][0][
        "approved_content_sha256"
    ] = "0" * 64

    write_json(
        files["approvals"],
        approvals,
    )

    _, exit_code = run_main(
        monkeypatch,
        files=files,
    )

    captured = capsys.readouterr()

    assert exit_code == 1
    assert "failure" in captured.err.lower()
    assert not files["database"].exists()


def test_existing_output_fails_before_database_creation(
    tmp_path,
    monkeypatch,
    capsys,
):
    files = build_operator_files(tmp_path)

    output_path = tmp_path / "already-exists.json"
    original = b"preserve-this-evidence\n"
    output_path.write_bytes(original)

    _, exit_code = run_main(
        monkeypatch,
        files=files,
        output_path=output_path,
    )

    captured = capsys.readouterr()

    assert exit_code == 1
    assert "refusing to overwrite evidence" in captured.err
    assert output_path.read_bytes() == original
    assert not files["database"].exists()


def test_intake_database_mismatch_fails_before_execution(
    tmp_path,
    monkeypatch,
    capsys,
):
    files = build_operator_files(tmp_path)

    intake = json.loads(
        files["intake"].read_text(
            encoding="utf-8"
        )
    )

    intake["storage"]["repository_path"] = str(
        tmp_path / "different.sqlite3"
    )

    write_json(
        files["intake"],
        intake,
    )

    _, exit_code = run_main(
        monkeypatch,
        files=files,
    )

    captured = capsys.readouterr()

    assert exit_code == 1
    assert "repository_path does not match" in captured.err
    assert not files["database"].exists()


def test_operator_routes_through_recovery_service(
    tmp_path,
    monkeypatch,
):
    files = build_operator_files(tmp_path)

    runner = load_runner()

    calls = []

    class CapturingRecoveryService:
        def execute(self, **kwargs):
            calls.append(kwargs)

            class Result:
                def to_dict(self):
                    return {
                        "disposition": "executed",
                        "artifact_count_before": 0,
                        "artifact_count_after": 10,
                    }

            return Result()

    monkeypatch.setattr(
        runner,
        "GovernanceRealPaidAssessmentExecutionRecoveryService",
        CapturingRecoveryService,
    )

    monkeypatch.setattr(
        sys,
        "argv",
        [
            str(SCRIPT_PATH),
            "--database",
            str(files["database"]),
            "--intake-json",
            str(files["intake"]),
            "--authorization-json",
            str(files["authorization"]),
            "--contract-event-json",
            str(files["contract_event"]),
            "--request-json",
            str(files["request"]),
            "--evidence-approvals-json",
            str(files["approvals"]),
        ],
    )

    assert runner.main() == 0
    assert len(calls) == 1

    call = calls[0]

    assert call["database_path"] == files["database"]
    assert call["intake"].assessment_id == "assessment-001"
    assert (
        call["paid_work_authorization"].authorization_id
        == "paid-work-auth-real-001"
    )
    assert (
        call["request"].context.assessment_id
        == "assessment-001"
    )


def test_runner_does_not_import_legacy_execution_service():
    source = SCRIPT_PATH.read_text(
        encoding="utf-8"
    )

    assert (
        "GovernanceRealPaidAssessmentExecutionService"
        not in source
    )

    assert (
        "GovernanceRealPaidAssessmentExecutionRecoveryService"
        in source
    )