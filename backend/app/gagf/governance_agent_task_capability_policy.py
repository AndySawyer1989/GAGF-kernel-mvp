"""Versioned task-to-capability policy for the Engineering Agent.

This policy declares worker capability requirements for recognized task types.
It does not grant operating-system permissions or authorize execution.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping as TypingMapping

from backend.app.gagf.governance_agent_capability_vocabulary import (
    normalize_agent_capabilities,
)
from backend.app.gagf.governance_agent_task_taxonomy import (
    EngineeringTaskType,
    get_engineering_task_definition,
)


ENGINEERING_TASK_CAPABILITY_POLICY_ID = (
    "gagf-engineering-task-capability-policy"
)
ENGINEERING_TASK_CAPABILITY_POLICY_VERSION = "1.0.0"
ENGINEERING_TASK_CAPABILITY_POLICY_SCHEMA_VERSION = 1


class AgentTaskCapabilityPolicyError(ValueError):
    """Raised when a task capability policy is invalid."""


@dataclass(frozen=True, slots=True)
class AgentTaskCapabilityPolicy:
    """Immutable mapping from recognized task types to required capabilities."""

    requirements_by_task_type: TypingMapping[str, tuple[str, ...]]

    def __post_init__(self) -> None:
        supplied = self.requirements_by_task_type

        if not isinstance(supplied, Mapping):
            raise AgentTaskCapabilityPolicyError(
                "requirements_by_task_type must be a mapping"
            )

        normalized: dict[str, tuple[str, ...]] = {}

        for raw_task_type, raw_capabilities in supplied.items():
            try:
                definition = get_engineering_task_definition(raw_task_type)
            except (TypeError, ValueError) as exc:
                raise AgentTaskCapabilityPolicyError(
                    f"Unknown task type in capability policy: {raw_task_type!r}"
                ) from exc

            if isinstance(raw_capabilities, (str, bytes)):
                raise AgentTaskCapabilityPolicyError(
                    "Task capabilities must be a collection, not text"
                )

            try:
                capabilities = normalize_agent_capabilities(raw_capabilities)
            except (TypeError, ValueError) as exc:
                raise AgentTaskCapabilityPolicyError(
                    f"Invalid capabilities for task type "
                    f"{definition.task_type.value!r}: {exc}"
                ) from exc

            task_key = definition.task_type.value

            if task_key in normalized:
                raise AgentTaskCapabilityPolicyError(
                    f"Duplicate task type in capability policy: {task_key}"
                )

            normalized[task_key] = capabilities

        ordered = {
            task_type.value: normalized[task_type.value]
            for task_type in EngineeringTaskType
            if task_type.value in normalized
        }

        object.__setattr__(
            self,
            "requirements_by_task_type",
            MappingProxyType(ordered),
        )

    def validate(self) -> None:
        """Revalidate the policy before dispatch candidate listing."""

        if not isinstance(self.requirements_by_task_type, Mapping):
            raise AgentTaskCapabilityPolicyError(
                "Capability policy mapping is invalid"
            )

        for task_type, capabilities in self.requirements_by_task_type.items():
            try:
                definition = get_engineering_task_definition(task_type)
                normalized = normalize_agent_capabilities(capabilities)
            except (TypeError, ValueError) as exc:
                raise AgentTaskCapabilityPolicyError(
                    f"Invalid capability policy entry for {task_type!r}: {exc}"
                ) from exc

            if normalized != capabilities:
                raise AgentTaskCapabilityPolicyError(
                    f"Capabilities are not canonical for {task_type!r}"
                )

            if definition.task_type.value != task_type:
                raise AgentTaskCapabilityPolicyError(
                    f"Task type is not canonical: {task_type!r}"
                )

    def get_required_capabilities(
        self,
        task_type: str,
    ) -> tuple[str, ...] | None:
        """Return requirements, or None when the task has no policy entry."""

        try:
            definition = get_engineering_task_definition(task_type)
        except (TypeError, ValueError) as exc:
            raise AgentTaskCapabilityPolicyError(
                f"Unknown task type: {task_type!r}"
            ) from exc

        return self.requirements_by_task_type.get(
            definition.task_type.value
        )


def default_engineering_task_capability_policy() -> AgentTaskCapabilityPolicy:
    """Return the complete, conservative Engineering Agent policy."""

    return AgentTaskCapabilityPolicy(
        requirements_by_task_type={
            EngineeringTaskType.REPOSITORY_ANALYSIS.value: (),
            EngineeringTaskType.CODE_CHANGE.value: (),
            EngineeringTaskType.TEST_EXECUTION.value: (),
            EngineeringTaskType.DEFECT_INVESTIGATION.value: (),
            EngineeringTaskType.DOCUMENTATION_UPDATE.value: (),
            EngineeringTaskType.CODE_REVIEW.value: (),
            EngineeringTaskType.ARCHITECTURE_ANALYSIS.value: (),
            EngineeringTaskType.VALIDATION_VERIFICATION.value: (),
            EngineeringTaskType.SECURITY_REVIEW.value: (
                "expertise.security_review",
            ),
        }
    )
