from backend.app.gagf.source_kernel_role_service import SourceKernelRoleService


def test_source_kernel_role_service_returns_summary():
    summary = SourceKernelRoleService().get_kernel_role_summary()

    assert summary["status"] == "ok"
    assert summary["kernel_role_count"] >= 5
    assert isinstance(summary["kernel_roles"], list)


def test_source_kernel_role_service_groups_identity_evidence_sources():
    summary = SourceKernelRoleService().get_kernel_role_summary()

    kernel_roles = {
        kernel_role["kernel_role"]: kernel_role
        for kernel_role in summary["kernel_roles"]
    }

    assert "identity_evidence" in kernel_roles
    assert kernel_roles["identity_evidence"]["source_count"] == 2

    source_systems = {
        source["source_system"]
        for source in kernel_roles["identity_evidence"]["sources"]
    }

    assert "okta" in source_systems
    assert "entra" in source_systems


def test_source_kernel_role_service_groups_threat_evidence_sources():
    summary = SourceKernelRoleService().get_kernel_role_summary()

    kernel_roles = {
        kernel_role["kernel_role"]: kernel_role
        for kernel_role in summary["kernel_roles"]
    }

    assert "threat_evidence" in kernel_roles
    assert kernel_roles["threat_evidence"]["source_count"] == 2

    source_systems = {
        source["source_system"]
        for source in kernel_roles["threat_evidence"]["sources"]
    }

    assert "defender" in source_systems
    assert "sentinelone" in source_systems


def test_source_kernel_role_service_groups_single_source_roles():
    summary = SourceKernelRoleService().get_kernel_role_summary()

    kernel_roles = {
        kernel_role["kernel_role"]: kernel_role
        for kernel_role in summary["kernel_roles"]
    }

    assert kernel_roles["delivery_evidence"]["source_count"] == 1
    assert kernel_roles["delivery_evidence"]["sources"][0]["source_system"] == "github"

    assert kernel_roles["workflow_evidence"]["source_count"] == 1
    assert kernel_roles["workflow_evidence"]["sources"][0]["source_system"] == "jira"

    assert kernel_roles["incident_evidence"]["source_count"] == 1
    assert kernel_roles["incident_evidence"]["sources"][0]["source_system"] == "servicenow"


def test_source_kernel_role_service_gets_sources_for_kernel_role():
    service = SourceKernelRoleService()

    sources = service.get_sources_for_kernel_role("threat_evidence")
    source_systems = {source["source_system"] for source in sources}

    assert len(sources) == 2
    assert "defender" in source_systems
    assert "sentinelone" in source_systems


def test_source_kernel_role_service_gets_kernel_role_detail():
    service = SourceKernelRoleService()

    detail = service.get_kernel_role_detail("threat_evidence")
    source_systems = {source["source_system"] for source in detail["sources"]}

    assert detail["status"] == "ok"
    assert detail["kernel_role"] == "threat_evidence"
    assert detail["source_count"] == 2
    assert "defender" in source_systems
    assert "sentinelone" in source_systems


def test_source_kernel_role_service_returns_failure_for_unknown_kernel_role_detail():
    service = SourceKernelRoleService()

    detail = service.get_kernel_role_detail("unknown-role")

    assert detail["status"] == "failed"
    assert detail["error"] == "kernel_role_not_found"
    assert detail["kernel_role"] == "unknown-role"
    assert detail["source_count"] == 0
    assert detail["sources"] == []


def test_source_kernel_role_service_returns_empty_list_for_unknown_kernel_role():
    service = SourceKernelRoleService()

    sources = service.get_sources_for_kernel_role("unknown-role")

    assert sources == []