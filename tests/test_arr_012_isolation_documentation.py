from pathlib import Path


DOCUMENT_PATH = Path(
    "docs/ARR_012_MULTI_TENANT_COGNITIVE_ISOLATION.md"
)


def document_text():
    return DOCUMENT_PATH.read_text(
        encoding="utf-8"
    )


def test_arr_012_document_exists():
    assert DOCUMENT_PATH.exists()
    assert DOCUMENT_PATH.is_file()


def test_document_declares_core_isolation_invariant():
    content = document_text()

    assert "## Core Isolation Invariant" in content
    assert (
        "No request authenticated in Tenant A"
        in content
    )
    assert (
        "Identical evidence does not authorize "
        "shared public identity."
        in content
    )


def test_document_covers_identity_binding():
    content = document_text()

    for field in (
        "tenant_id",
        "actor_id",
        "credential_id",
        "session_id",
        "role_id",
        "policy_scope",
        "request_id",
        "correlation_id",
    ):
        assert field in content


def test_document_covers_zero_trust_controls():
    content = document_text()

    for control in (
        "Credential verification",
        "Session verification",
        "Device trust",
        "Tenant-membership verification",
        "Role permission",
        "Policy-scope permission",
    ):
        assert control in content


def test_document_separates_public_and_canonical_ids():
    content = document_text()

    assert (
        "## Canonical and Public Identifier Separation"
        in content
    )
    assert (
        "Canonical identifiers are internal "
        "constitutional evidence."
        in content
    )
    assert (
        "Tenant clients operate through namespaced "
        "public identifiers."
        in content
    )


def test_document_requires_runtime_fail_closed_behavior():
    content = document_text()

    assert (
        "## Runtime Public-Boundary Enforcement"
        in content
    )
    assert "Fail-closed behavior" in content
    assert (
        "A failed boundary audit must never return "
        "the rejected payload."
        in content
    )


def test_document_covers_immutable_audit_evidence():
    content = document_text()

    assert "## Boundary Audit Evidence Ledger" in content
    assert "append-only SQLite ledger" in content
    assert "deterministic hash chain" in content
    assert (
        "An invalid audit cannot be recorded as released."
        in content
    )


def test_document_covers_tenant_scoped_queries():
    content = document_text()

    assert "## Tenant-Scoped Audit Evidence" in content
    assert "Tenant-local sequence numbers" in content
    assert (
        "A tenant cannot resolve another tenant's "
        "public audit-record identifier."
        in content
    )


def test_document_covers_snapshot_pagination():
    content = document_text()

    assert "## Bounded Pagination" in content
    assert "Snapshot sequence" in content
    assert (
        "This prevents recursive audit logging from "
        "creating non-terminating pagination."
        in content
    )


def test_document_contains_required_threats():
    content = document_text()

    required_threats = (
        "Direct Cross-Tenant Artifact Access",
        "Identical Input Collision",
        "Canonical Identifier Leakage",
        "Authorization Context Leakage",
        "Audit Ledger Enumeration",
        "Cursor Replay Across Tenants",
        "Infinite Recursive Pagination",
        "Split Audit Evidence",
        "Boundary Gate Failure",
    )

    for threat in required_threats:
        assert f"### Threat: {threat}" in content


def test_document_states_known_limitations():
    content = document_text()

    assert "## Known Limitations" in content

    for limitation in (
        "Database encryption at rest",
        "Hardware-backed tenant key isolation",
        "Distributed ledger replication",
        "Production identity-provider integration",
        "Rate limiting",
        "Formal verification",
    ):
        assert limitation in content


def test_document_defines_operational_requirements():
    content = document_text()

    assert "## Operational Requirements" in content
    assert (
        "Use the central tenant application router "
        "registry."
        in content
    )
    assert (
        "Prevent direct public access to canonical "
        "services and ledgers."
        in content
    )
    assert (
        "Add isolation tests for every new artifact type."
        in content
    )


def test_document_defines_completion_conditions():
    content = document_text()

    assert "## Definition of Done" in content
    assert (
        "End-to-end two-tenant isolation tests pass."
        in content
    )
    assert (
        "Tenant-scoped audit queries remain isolated "
        "and bounded."
        in content
    )
    assert (
        "The full regression suite passes."
        in content
    )
