from __future__ import annotations

import pytest

from backend.app.gagf.governance_agent_task_capability_policy import (
    AgentTaskCapabilityPolicy,
    AgentTaskCapabilityPolicyError,
    ENGINEERING_TASK_CAPABILITY_POLICY_ID,
    ENGINEERING_TASK_CAPABILITY_POLICY_SCHEMA_VERSION,
    ENGINEERING_TASK_CAPABILITY_POLICY_VERSION,
    default_engineering_task_capability_policy,
)
from backend.app.gagf.governance_agent_task_taxonomy import (
    EngineeringTaskType,
)


def test_policy_has_versioned_identity():
    assert ENGINEERING_TASK_CAPABILITY_POLICY_ID == (
        "gagf-engineering-task-capability-policy"
    )
    assert ENGINEERING_TASK_CAPABILITY_POLICY_VERSION == "1.0.0"
    assert ENGINEERING_TASK_CAPABILITY_POLICY_SCHEMA_VERSION == 1


def test_default_policy_covers_every_taxonomy_task_type():
    policy = default_engineering_task_capability_policy()

    assert tuple(policy.requirements_by_task_type) == tuple(
        task_type.value for task_type in EngineeringTaskType
    )


def test_default_policy_declares_security_review_capability():
    policy = default_engineering_task_capability_policy()

    assert policy.get_required_capabilities("security.review") == (
        "expertise.security_review",
    )


def test_default_policy_uses_explicit_empty_requirements_for_other_tasks():
    policy = default_engineering_task_capability_policy()

    for task_type in EngineeringTaskType:
        if task_type is not EngineeringTaskType.SECURITY_REVIEW:
            assert policy.get_required_capabilities(task_type.value) == ()


def test_policy_mapping_is_immutable():
    policy = default_engineering_task_capability_policy()

    with pytest.raises(TypeError):
        policy.requirements_by_task_type["code.review"] = (
            "expertise.security_review",
        )


def test_policy_dataclass_is_frozen():
    policy = default_engineering_task_capability_policy()

    with pytest.raises((AttributeError, TypeError)):
        policy.requirements_by_task_type = {}


def test_partial_policy_preserves_missing_entry_for_fail_closed_dispatch():
    policy = AgentTaskCapabilityPolicy(
        requirements_by_task_type={}
    )

    assert policy.get_required_capabilities("code.review") is None


def test_unknown_task_type_is_rejected():
    with pytest.raises(AgentTaskCapabilityPolicyError):
        AgentTaskCapabilityPolicy(
            requirements_by_task_type={
                "unknown.task": (),
            }
        )


def test_unknown_capability_is_rejected():
    with pytest.raises(AgentTaskCapabilityPolicyError):
        AgentTaskCapabilityPolicy(
            requirements_by_task_type={
                "code.review": ("capability.not_registered",),
            }
        )


def test_text_is_not_accepted_as_a_capability_collection():
    with pytest.raises(AgentTaskCapabilityPolicyError):
        AgentTaskCapabilityPolicy(
            requirements_by_task_type={
                "code.review": "runtime.python",
            }
        )




def test_policy_lookup_rejects_unknown_task_type():
    policy = default_engineering_task_capability_policy()

    with pytest.raises(AgentTaskCapabilityPolicyError):
        policy.get_required_capabilities("unknown.task")


def test_policy_validation_succeeds_for_default_policy():
    policy = default_engineering_task_capability_policy()

    policy.validate()
