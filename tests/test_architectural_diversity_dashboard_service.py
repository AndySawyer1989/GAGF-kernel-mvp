from backend.app.gagf.architectural_diversity_dashboard_service import (
    ArchitecturalDiversityDashboardService,
)


class FakePlatformService:
    def __init__(self, result):
        self.result = result

    def diagnose_platform(self):
        return self.result


def build_platform_result(
    platform_architecture_status="platform_architecture_balanced",
    architecture_posture="mixed_resilience_architecture",
    concentration_risk="moderate",
    architectural_diversity_index=0.5682,
    complexity_resilience_ratio=0.6637,
    mononal_risk_score=0.4318,
    dominant_component_type="connector",
):
    return {
        "status": "ok",
        "component_origin": "platform_telemetry",
        "source_count": 7,
        "kernel_component_count": 4,
        "source_component_count": 7,
        "component_count": 11,
        "architectural_diversity_index": architectural_diversity_index,
        "complexity_resilience_ratio": complexity_resilience_ratio,
        "mononal_risk_score": mononal_risk_score,
        "architecture_posture": architecture_posture,
        "concentration_risk": concentration_risk,
        "platform_architecture_status": platform_architecture_status,
        "dominant_component_type": dominant_component_type,
        "component_type_counts": {
            "kernel": 1,
            "ledger": 2,
            "worker": 1,
            "connector": 7,
        },
        "subsystem_counts": {
            "decision": 2,
            "evidence": 1,
            "diagnostics": 1,
            "delivery": 1,
            "security": 2,
            "identity": 2,
            "workflow": 1,
            "operations": 1,
        },
        "authority_zone_counts": {
            "kernel": 1,
            "ledger": 2,
            "diagnostic": 1,
            "source_connector": 7,
        },
        "redundancy_group_counts": {
            "kernel-core": 1,
            "evidence-ledgers": 1,
            "decision-ledgers": 1,
            "diagnostic-workers": 1,
            "delivery_sources": 1,
            "workflow_sources": 1,
            "identity_sources": 2,
            "security_sources": 2,
            "operations_sources": 1,
        },
        "diversity_breakdown": {},
        "component_diagnostics": [],
        "components": [],
    }


def build_dashboard_service(platform_result):
    return ArchitecturalDiversityDashboardService(
        platform_service=FakePlatformService(platform_result)
    )


def test_architectural_diversity_dashboard_service_returns_summary():
    service = build_dashboard_service(build_platform_result())

    result = service.get_summary()

    assert result["status"] == "ok"
    assert result["summary_type"] == "architectural_diversity_dashboard"
    assert result["platform_architecture_status"] == (
        "platform_architecture_balanced"
    )
    assert result["architecture_posture"] == "mixed_resilience_architecture"
    assert result["concentration_risk"] == "moderate"


def test_architectural_diversity_dashboard_service_builds_scorecards():
    service = build_dashboard_service(build_platform_result())

    result = service.get_summary()

    assert result["scorecards"] == [
        {
            "label": "Architectural Diversity Index",
            "metric": "architectural_diversity_index",
            "value": 0.5682,
            "interpretation": "moderate_diversity",
        },
        {
            "label": "Complexity Resilience Ratio",
            "metric": "complexity_resilience_ratio",
            "value": 0.6637,
            "interpretation": "moderate_resilience",
        },
        {
            "label": "Mononal Risk Score",
            "metric": "mononal_risk_score",
            "value": 0.4318,
            "interpretation": "moderate_mononal_risk",
        },
    ]


def test_architectural_diversity_dashboard_service_builds_component_summary():
    service = build_dashboard_service(build_platform_result())

    result = service.get_summary()
    component_summary = result["component_summary"]

    assert component_summary["component_count"] == 11
    assert component_summary["kernel_component_count"] == 4
    assert component_summary["source_component_count"] == 7
    assert component_summary["dominant_component_type"] == "connector"
    assert component_summary["component_type_counts"]["connector"] == 7
    assert component_summary["subsystem_counts"]["security"] == 2
    assert component_summary["authority_zone_counts"]["source_connector"] == 7


def test_architectural_diversity_dashboard_service_builds_risk_summary():
    service = build_dashboard_service(
        build_platform_result(
            platform_architecture_status=(
                "platform_architecture_concentrated"
            ),
            architecture_posture="concentrated_architecture",
            concentration_risk="high",
            mononal_risk_score=0.55,
            dominant_component_type="connector",
        )
    )

    result = service.get_summary()
    risk_summary = result["risk_summary"]

    assert risk_summary == {
        "architecture_posture": "concentrated_architecture",
        "concentration_risk": "high",
        "mononal_risk_score": 0.55,
        "platform_architecture_status": (
            "platform_architecture_concentrated"
        ),
        "highest_attention_area": "dominant_component_type:connector",
    }


def test_architectural_diversity_dashboard_service_recommends_resilient_action():
    service = build_dashboard_service(
        build_platform_result(
            platform_architecture_status="platform_architecture_resilient",
            architecture_posture="adaptive_diverse_architecture",
            concentration_risk="low",
            architectural_diversity_index=0.8125,
            complexity_resilience_ratio=0.8875,
            mononal_risk_score=0.1875,
            dominant_component_type="ledger",
        )
    )

    result = service.get_summary()

    assert result["operator_message"] == (
        "Architecture is currently diverse and resilient."
    )
    assert result["recommended_action"] == "continue_monitoring"


def test_architectural_diversity_dashboard_service_recommends_balanced_action():
    service = build_dashboard_service(build_platform_result())

    result = service.get_summary()

    assert result["operator_message"] == (
        "Architecture is balanced with manageable concentration risk."
    )
    assert result["recommended_action"] == (
        "monitor_architecture_concentration"
    )


def test_architectural_diversity_dashboard_service_recommends_mononal_action():
    service = build_dashboard_service(
        build_platform_result(
            platform_architecture_status=(
                "platform_architecture_mononal_risk"
            ),
            architecture_posture="mononal_architecture_risk",
            concentration_risk="critical",
            architectural_diversity_index=0.25,
            complexity_resilience_ratio=0.2625,
            mononal_risk_score=0.75,
            dominant_component_type="worker",
        )
    )

    result = service.get_summary()

    assert result["operator_message"] == (
        "Architecture shows mononal-risk conditions requiring "
        "priority attention."
    )
    assert result["recommended_action"] == (
        "reduce_authority_and_component_concentration"
    )
    assert result["risk_summary"]["highest_attention_area"] == (
        "dominant_component_type:worker"
    )




