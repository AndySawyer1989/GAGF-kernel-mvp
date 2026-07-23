import json
from pathlib import Path


MANIFEST_PATH = Path(
    "docs/ARR_012_RELEASE_MANIFEST.json"
)
CLOSURE_PATH = Path(
    "docs/ARR_012_SPRINT_CLOSURE.md"
)
THREAT_MODEL_PATH = Path(
    "docs/ARR_012_MULTI_TENANT_COGNITIVE_ISOLATION.md"
)
END_TO_END_TEST_PATH = Path(
    "tests/test_tenant_end_to_end_isolation.py"
)


def load_manifest():
    return json.loads(
        MANIFEST_PATH.read_text(encoding="utf-8-sig")
    )


def test_arr_012_release_artifacts_exist():
    assert MANIFEST_PATH.is_file()
    assert CLOSURE_PATH.is_file()
    assert THREAT_MODEL_PATH.is_file()
    assert END_TO_END_TEST_PATH.is_file()


def test_release_manifest_identity():
    manifest = load_manifest()

    assert manifest["epic_id"] == "ARR-012"
    assert manifest["status"] == "complete"
    assert manifest["release_readiness"] == "verified"


def test_release_manifest_story_range():
    story_range = load_manifest()["story_range"]

    assert story_range["first"] == "ARR-012-001"
    assert story_range["last"] == "ARR-012-025"
    assert story_range["total"] == 25


def test_manifest_contains_all_completed_capabilities():
    capabilities = load_manifest()[
        "completed_capabilities"
    ]

    assert len(capabilities) == 25
    assert len(set(capabilities)) == 25
    assert "tenant-bound-scientific-authority" in capabilities
    assert "multi-tenant-end-to-end-isolation-proof" in capabilities
    assert "sprint-closure-and-release-milestone" in capabilities


def test_manifest_preserves_authoritative_baseline():
    manifest = load_manifest()

    assert (
        manifest[
            "authoritative_test_count_before_closure"
        ]
        == 3086
    )


def test_manifest_declares_fail_closed_security():
    manifest = load_manifest()

    assert manifest["security_posture"] == "fail-closed"
    assert manifest["isolation_unit"] == "tenant"
    assert manifest["authority_model"] == (
        "deterministic-gagf-kernel"
    )


def test_manifest_requires_release_evidence():
    evidence = set(
        load_manifest()["required_release_evidence"]
    )

    required = {
        "full-regression-suite-green",
        "changes-pushed-to-git",
        "end-to-end-two-tenant-isolation-green",
        "runtime-boundary-enforcement-green",
        "tenant-scoped-query-isolation-green",
        "snapshot-pagination-green",
        "threat-model-documented",
    }

    assert required.issubset(evidence)


def test_closure_document_declares_core_invariant():
    content = CLOSURE_PATH.read_text(
        encoding="utf-8-sig"
    )

    assert "## Constitutional Invariant" in content
    assert (
        "No request authenticated in one tenant"
        in content
    )
    assert "belonging exclusively to another tenant" in content


def test_closure_document_declares_product_milestone():
    content = CLOSURE_PATH.read_text(
        encoding="utf-8-sig"
    )

    assert "## Product Milestone" in content
    assert (
        "coherent multi-tenant security boundary"
        in content
    )
    assert "commercial product composition" in content


def test_closure_document_preserves_portfolio_allocation():
    content = CLOSURE_PATH.read_text(
        encoding="utf-8-sig"
    )

    assert "70 percent Core Platform" in content
    assert "20 percent Active Commercial Product" in content
    assert "10 percent Private or Internal Product" in content
