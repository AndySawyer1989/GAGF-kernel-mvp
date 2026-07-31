from backend.app.gagf.governance_assessment_audit import (
    AssessmentAuditLedger,
)
from backend.app.gagf.governance_assessment_audit_checkpoint import (
    AssessmentAuditCheckpointStore,
)
from backend.app.gagf.governance_assessment_audit_checkpoint_signature_store import (
    SignedAssessmentAuditCheckpointStore,
)
from backend.app.gagf.governance_assessment_checkpoint_key_audit import (
    AssessmentCheckpointKeyAuditStore,
)
from backend.app.gagf.governance_assessment_checkpoint_key_store import (
    AssessmentCheckpointSigningKeyMetadataStore,
)
from backend.app.gagf.governance_assessment_dashboard import (
    GovernanceAssessmentDashboardService,
)


def build_service(tmp_path, *, with_keys=True):
    audit_ledger = AssessmentAuditLedger(
        tmp_path / "audit.sqlite3"
    )
    checkpoint_store = AssessmentAuditCheckpointStore(
        tmp_path / "checkpoints.sqlite3"
    )
    signed_store = SignedAssessmentAuditCheckpointStore(
        tmp_path / "signed.sqlite3"
    )

    key_store = None
    key_audit_store = None

    if with_keys:
        key_store = AssessmentCheckpointSigningKeyMetadataStore(
            tmp_path / "keys.sqlite3"
        )
        key_audit_store = AssessmentCheckpointKeyAuditStore(
            tmp_path / "key-audit.sqlite3"
        )

    return GovernanceAssessmentDashboardService(
        audit_ledger=audit_ledger,
        checkpoint_store=checkpoint_store,
        signed_checkpoint_store=signed_store,
        key_metadata_store=key_store,
        key_audit_store=key_audit_store,
    )


def test_empty_dashboard_summary_has_zero_counts(tmp_path):
    service = build_service(tmp_path)

    summary = service.build_summary(
        tenant_id="tenant-alpha"
    )

    assert summary.tenant_id == "tenant-alpha"
    assert summary.audit_event_count == 0
    assert summary.checkpoint_count == 0
    assert summary.signed_checkpoint_count == 0
    assert summary.signing_key_count == 0
    assert summary.key_activation_event_count == 0


def test_empty_audit_chain_is_valid(tmp_path):
    service = build_service(tmp_path)

    summary = service.build_summary(
        tenant_id="tenant-alpha"
    )

    assert summary.audit_chain_valid is True


def test_dashboard_without_key_services_is_supported(tmp_path):
    service = build_service(
        tmp_path,
        with_keys=False,
    )

    summary = service.build_summary(
        tenant_id="tenant-alpha"
    )

    assert summary.active_signing_key_id is None
    assert summary.signing_key_count == 0
    assert summary.key_activation_event_count == 0


def test_dashboard_summary_serializes_for_frontend(tmp_path):
    service = build_service(tmp_path)

    payload = service.build_summary(
        tenant_id="tenant-alpha"
    ).to_dict()

    assert payload == {
        "tenant_id": "tenant-alpha",
        "audit_event_count": 0,
        "audit_chain_valid": True,
        "checkpoint_count": 0,
        "signed_checkpoint_count": 0,
        "active_signing_key_id": None,
        "signing_key_count": 0,
        "key_activation_event_count": 0,
    }
