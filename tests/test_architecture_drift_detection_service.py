from backend.app.gagf.architecture_drift_detection_service import (
    ArchitectureDriftDetectionService,
)


def build_architecture_result(
    component_count=11,
    architectural_diversity_index=0.5682,
    complexity_resilience_ratio=0.6637,
    mononal_risk_score=0.4318,
    architecture_posture="mixed_resilience_architecture",
    concentration_risk="moderate",
    platform_architecture_status="platform_architecture_balanced",
):
    return {
        "status": "ok",
        "component_count": component_count,
        "architectural_diversity_index": architectural_diversity_index,
        "complexity_resilience_ratio": complexity_resilience_ratio,
        "mononal_risk_score": mononal_risk_score,
        "architecture_posture": architecture_posture,
        "concentration_risk": concentration_risk,
        "platform_architecture_status": platform_architecture_status,
    }


def test_architecture_drift_detection_service_detects_no_drift():
    service = ArchitectureDriftDetectionService()
    baseline = build_architecture_result()
    current = build_architecture_result()

    result = service.detect_drift(
        baseline_result=baseline,
        current_result=current,
    )

    assert result["status"] == "ok"
    assert result["drift_type"] == "architecture_drift"
    assert result["baseline_component_count"] == 11
    assert result["current_component_count"] == 11
    assert result["component_count_delta"] == 0
    assert result["drift_status"] == "no_architecture_drift"
    assert result["recommended_action"] == "continue_monitoring"


def test_architecture_drift_detection_service_calculates_score_deltas():
    service = ArchitectureDriftDetectionService()
    baseline = build_architecture_result(
        architectural_diversity_index=0.8125,
        complexity_resilience_ratio=0.8875,
        mononal_risk_score=0.1875,
        platform_architecture_status="platform_architecture_resilient",
    )
    current = build_architecture_result(
        architectural_diversity_index=0.5682,
        complexity_resilience_ratio=0.6637,
        mononal_risk_score=0.4318,
        platform_architecture_status="platform_architecture_balanced",
    )

    result = service.detect_drift(
        baseline_result=baseline,
        current_result=current,
    )

    assert result["score_drift"] == {
        "architectural_diversity_index_delta": -0.2443,
        "complexity_resilience_ratio_delta": -0.2238,
        "mononal_risk_score_delta": 0.2443,
        "diversity_regressed": True,
        "resilience_regressed": True,
        "mononal_risk_increased": True,
        "severity": "high",
    }


def test_architecture_drift_detection_service_detects_posture_regression():
    service = ArchitectureDriftDetectionService()
    baseline = build_architecture_result(
        architecture_posture="adaptive_diverse_architecture",
        concentration_risk="low",
        platform_architecture_status="platform_architecture_resilient",
    )
    current = build_architecture_result(
        architecture_posture="mixed_resilience_architecture",
        concentration_risk="moderate",
        platform_architecture_status="platform_architecture_balanced",
    )

    result = service.detect_drift(
        baseline_result=baseline,
        current_result=current,
    )

    assert result["posture_drift"] == {
        "architecture_posture_changed": True,
        "concentration_risk_changed": True,
        "platform_architecture_status_changed": True,
        "baseline_architecture_posture": "adaptive_diverse_architecture",
        "current_architecture_posture": "mixed_resilience_architecture",
        "baseline_concentration_risk": "low",
        "current_concentration_risk": "moderate",
        "baseline_platform_architecture_status": (
            "platform_architecture_resilient"
        ),
        "current_platform_architecture_status": (
            "platform_architecture_balanced"
        ),
        "posture_regressed": True,
    }


def test_architecture_drift_detection_service_marks_high_drift():
    service = ArchitectureDriftDetectionService()
    baseline = build_architecture_result(
        architectural_diversity_index=0.8125,
        complexity_resilience_ratio=0.8875,
        mononal_risk_score=0.1875,
        platform_architecture_status="platform_architecture_resilient",
    )
    current = build_architecture_result(
        architectural_diversity_index=0.5682,
        complexity_resilience_ratio=0.6637,
        mononal_risk_score=0.4318,
        platform_architecture_status="platform_architecture_balanced",
    )

    result = service.detect_drift(
        baseline_result=baseline,
        current_result=current,
    )

    assert result["drift_status"] == "high_architecture_drift"
    assert result["recommended_action"] == (
        "review_architecture_regression_sources"
    )


def test_architecture_drift_detection_service_marks_critical_drift():
    service = ArchitectureDriftDetectionService()
    baseline = build_architecture_result(
        architectural_diversity_index=0.8125,
        complexity_resilience_ratio=0.8875,
        mononal_risk_score=0.1875,
        platform_architecture_status="platform_architecture_resilient",
    )
    current = build_architecture_result(
        architectural_diversity_index=0.25,
        complexity_resilience_ratio=0.2625,
        mononal_risk_score=0.75,
        architecture_posture="mononal_architecture_risk",
        concentration_risk="critical",
        platform_architecture_status="platform_architecture_mononal_risk",
    )

    result = service.detect_drift(
        baseline_result=baseline,
        current_result=current,
    )

    assert result["score_drift"]["severity"] == "critical"
    assert result["drift_status"] == "critical_architecture_drift"
    assert result["recommended_action"] == (
        "stabilize_architecture_and_reduce_mononal_risk"
    )


def test_architecture_drift_detection_service_marks_moderate_drift():
    service = ArchitectureDriftDetectionService()
    baseline = build_architecture_result(
        architectural_diversity_index=0.70,
        complexity_resilience_ratio=0.70,
        mononal_risk_score=0.30,
    )
    current = build_architecture_result(
        architectural_diversity_index=0.60,
        complexity_resilience_ratio=0.62,
        mononal_risk_score=0.40,
    )

    result = service.detect_drift(
        baseline_result=baseline,
        current_result=current,
    )

    assert result["score_drift"]["severity"] == "moderate"
    assert result["drift_status"] == "moderate_architecture_drift"
    assert result["recommended_action"] == (
        "monitor_architecture_diversity_regression"
    )


def test_architecture_drift_detection_service_marks_component_count_delta():
    service = ArchitectureDriftDetectionService()
    baseline = build_architecture_result(component_count=11)
    current = build_architecture_result(component_count=14)

    result = service.detect_drift(
        baseline_result=baseline,
        current_result=current,
    )

    assert result["baseline_component_count"] == 11
    assert result["current_component_count"] == 14
    assert result["component_count_delta"] == 3

