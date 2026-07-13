from pathlib import Path


DOC_PATH = Path("docs/EVIDENCE_INTELLIGENCE_LAYER.md")


def test_evidence_intelligence_documentation_exists():
    assert DOC_PATH.exists()


def test_evidence_intelligence_documentation_contains_release_marker():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "Version | 0.5.0" in content
    assert "Release | evidence-intelligence" in content
    assert "Sprint | 3.4" in content
    assert "Status | complete" in content


def test_evidence_intelligence_documentation_contains_required_sections():
    content = DOC_PATH.read_text(encoding="utf-8")

    required_sections = [
        "# Evidence Intelligence Layer",
        "## Purpose",
        "## Release Marker",
        "## Core Principle",
        "## Architecture Flow",
        "## Evidence Quality",
        "## Cross-Source Agreement",
        "## Evidence Conflict Detection",
        "## Evidence Diagnostics",
        "## Evidence Confidence",
        "## Snapshot Integration",
        "## Ingestion Integration",
        "## Snapshot Diagnostics Persistence",
        "## Snapshot Diagnostics Summary",
        "## Snapshot Diagnostics Risk",
        "## Determinism Boundary",
        "## Kernel Boundary",
        "## Sprint 3.4 Story Map",
        "## Completed Capabilities",
        "## Next Sprint Direction",
    ]

    for section in required_sections:
        assert section in content


def test_evidence_intelligence_documentation_lists_core_endpoints():
    content = DOC_PATH.read_text(encoding="utf-8")

    required_endpoints = [
        "POST /evidence/quality",
        "POST /evidence/agreement",
        "POST /evidence/conflicts",
        "POST /evidence/diagnostics",
        "POST /evidence/confidence",
        "POST /snapshot",
        "GET /snapshot-diagnostics",
        "GET /snapshot-diagnostics/{snapshot_id}",
        "GET /snapshot-diagnostics/summary",
        "GET /snapshot-diagnostics/risk",
    ]

    for endpoint in required_endpoints:
        assert endpoint in content


def test_evidence_intelligence_documentation_lists_all_sprint_stories():
    content = DOC_PATH.read_text(encoding="utf-8")

    for story_number in range(71, 92):
        assert f"US-{story_number:03d}" in content




