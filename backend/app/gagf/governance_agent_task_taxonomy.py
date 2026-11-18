"""Versioned task taxonomy for the FIP/GAGF Engineering Agent.

The taxonomy defines recognized engineering work and its governance
boundaries. It does not grant worker capabilities or authorize execution.

Capability mappings and execution authorization are separate contracts.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import Mapping


ENGINEERING_TASK_TAXONOMY_ID = "gagf-engineering-task-taxonomy"
ENGINEERING_TASK_TAXONOMY_VERSION = "1.1.0"
ENGINEERING_TASK_TAXONOMY_SCHEMA_VERSION = 1


class EngineeringTaskTaxonomyError(ValueError):
    """Base error for Engineering Agent task taxonomy violations."""


class UnknownEngineeringTaskTypeError(EngineeringTaskTaxonomyError):
    """Raised when a task type is not recognized by the taxonomy."""


class EngineeringTaskType(str, Enum):
    REPOSITORY_ANALYSIS = "repository.analysis"
    CODE_CHANGE = "code.change"
    TEST_EXECUTION = "test.execution"
    DEFECT_INVESTIGATION = "defect.investigation"
    DOCUMENTATION_UPDATE = "documentation.update"
    CODE_REVIEW = "code.review"
    ARCHITECTURE_ANALYSIS = "architecture.analysis"
    VALIDATION_VERIFICATION = "validation.verification"
    SECURITY_REVIEW = "security.review"


@dataclass(frozen=True, slots=True)
class EngineeringTaskDefinition:
    """Immutable definition of one recognized Engineering Agent task."""

    task_type: EngineeringTaskType
    name: str
    description: str
    required_inputs: tuple[str, ...]
    expected_outputs: tuple[str, ...]
    approval_boundaries: tuple[str, ...]
    prohibited_actions: tuple[str, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.task_type, EngineeringTaskType):
            raise EngineeringTaskTaxonomyError(
                "task_type must be an EngineeringTaskType"
            )

        for field_name in ("name", "description"):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise EngineeringTaskTaxonomyError(
                    f"{field_name} must be a non-empty string"
                )

        for field_name in (
            "required_inputs",
            "expected_outputs",
            "approval_boundaries",
            "prohibited_actions",
        ):
            values = getattr(self, field_name)

            if not isinstance(values, tuple) or not values:
                raise EngineeringTaskTaxonomyError(
                    f"{field_name} must be a non-empty tuple"
                )

            if any(
                not isinstance(value, str) or not value.strip()
                for value in values
            ):
                raise EngineeringTaskTaxonomyError(
                    f"{field_name} must contain non-empty strings"
                )

            if len(set(values)) != len(values):
                raise EngineeringTaskTaxonomyError(
                    f"{field_name} cannot contain duplicates"
                )


_COMMON_PROHIBITED_ACTIONS = (
    "accessing secrets or credentials not explicitly authorized",
    "modifying files outside the assigned workspace",
    "committing, pushing, merging, or deploying changes without approval",
    "changing governance policy or Kernel authority",
    "treating unverified output as validated evidence",
)


_TASK_DEFINITIONS = {
    EngineeringTaskType.REPOSITORY_ANALYSIS: EngineeringTaskDefinition(
        task_type=EngineeringTaskType.REPOSITORY_ANALYSIS,
        name="Repository Analysis",
        description=(
            "Inspect an assigned repository and report its structure, "
            "implementation characteristics, dependencies, and findings."
        ),
        required_inputs=(
            "tenant and work-item identity",
            "authorized repository and workspace identity",
            "analysis objective and scope",
        ),
        expected_outputs=(
            "repository structure summary",
            "evidence-linked findings",
            "identified risks and unresolved questions",
        ),
        approval_boundaries=(
            "modifying repository files",
            "accessing external systems or network resources",
        ),
        prohibited_actions=_COMMON_PROHIBITED_ACTIONS,
    ),
    EngineeringTaskType.CODE_CHANGE: EngineeringTaskDefinition(
        task_type=EngineeringTaskType.CODE_CHANGE,
        name="Code Change",
        description=(
            "Implement a specifically authorized code change within "
            "the assigned isolated workspace."
        ),
        required_inputs=(
            "tenant and work-item identity",
            "authorized workspace identity",
            "change objective and acceptance criteria",
            "relevant source and test evidence",
        ),
        expected_outputs=(
            "proposed source changes",
            "change summary",
            "verification evidence",
            "known limitations",
        ),
        approval_boundaries=(
            "committing or pushing changes",
            "merging into a protected branch",
            "deploying or releasing changes",
            "modifying files outside the assigned workspace",
        ),
        prohibited_actions=_COMMON_PROHIBITED_ACTIONS,
    ),
    EngineeringTaskType.TEST_EXECUTION: EngineeringTaskDefinition(
        task_type=EngineeringTaskType.TEST_EXECUTION,
        name="Test Execution",
        description=(
            "Execute explicitly approved tests and report their "
            "results without treating test output as governance approval."
        ),
        required_inputs=(
            "tenant and work-item identity",
            "authorized workspace identity",
            "approved test-command specification",
            "test scope and execution limits",
        ),
        expected_outputs=(
            "test execution results",
            "test command and scope record",
            "failure details and verification evidence",
        ),
        approval_boundaries=(
            "executing commands outside the approved command specification",
            "running destructive or externally connected tests",
            "modifying production systems or data",
        ),
        prohibited_actions=_COMMON_PROHIBITED_ACTIONS,
    ),
    EngineeringTaskType.DEFECT_INVESTIGATION: EngineeringTaskDefinition(
        task_type=EngineeringTaskType.DEFECT_INVESTIGATION,
        name="Defect Investigation",
        description=(
            "Investigate a reported defect, establish reproducible "
            "evidence where possible, and identify likely causes."
        ),
        required_inputs=(
            "tenant and work-item identity",
            "defect description and observed behavior",
            "authorized repository and workspace identity",
            "available logs, traces, and reproduction evidence",
        ),
        expected_outputs=(
            "reproduction findings",
            "evidence-linked root-cause analysis",
            "proposed remediation options",
        ),
        approval_boundaries=(
            "applying a remediation",
            "changing production data or systems",
            "accessing additional systems outside the approved scope",
        ),
        prohibited_actions=_COMMON_PROHIBITED_ACTIONS,
    ),
    EngineeringTaskType.DOCUMENTATION_UPDATE: EngineeringTaskDefinition(
        task_type=EngineeringTaskType.DOCUMENTATION_UPDATE,
        name="Documentation Update",
        description=(
            "Prepare or update technical documentation within "
            "the assigned workspace."
        ),
        required_inputs=(
            "tenant and work-item identity",
            "documentation objective and scope",
            "authoritative source material",
            "authorized workspace identity",
        ),
        expected_outputs=(
            "proposed documentation changes",
            "source references and supporting evidence",
            "documentation validation results",
        ),
        approval_boundaries=(
            "publishing or externally distributing documentation",
            "changing approved policy or contractual language",
        ),
        prohibited_actions=_COMMON_PROHIBITED_ACTIONS,
    ),
    EngineeringTaskType.CODE_REVIEW: EngineeringTaskDefinition(
        task_type=EngineeringTaskType.CODE_REVIEW,
        name="Code Review",
        description=(
            "Review a proposed change for correctness, security, "
            "maintainability, and potential regressions."
        ),
        required_inputs=(
            "tenant and work-item identity",
            "change set or commit reference",
            "applicable acceptance criteria",
            "relevant test and architecture evidence",
        ),
        expected_outputs=(
            "review findings with severity and evidence",
            "identified regressions and risks",
            "review disposition and unresolved questions",
        ),
        approval_boundaries=(
            "modifying the reviewed change",
            "approving or merging a protected change",
            "overriding required independent review",
        ),
        prohibited_actions=_COMMON_PROHIBITED_ACTIONS,
    ),
    EngineeringTaskType.ARCHITECTURE_ANALYSIS: EngineeringTaskDefinition(
        task_type=EngineeringTaskType.ARCHITECTURE_ANALYSIS,
        name="Architecture Analysis",
        description=(
            "Evaluate an assigned system design, architecture, "
            "dependencies, and documented constraints."
        ),
        required_inputs=(
            "tenant and work-item identity",
            "architecture question and analysis scope",
            "authoritative architecture records",
            "relevant implementation evidence",
        ),
        expected_outputs=(
            "architecture assessment",
            "dependency and risk analysis",
            "evidence-linked recommendations",
            "assumptions and unresolved questions",
        ),
        approval_boundaries=(
            "changing approved architecture",
            "modifying governance constraints",
            "implementing architectural recommendations",
        ),
        prohibited_actions=_COMMON_PROHIBITED_ACTIONS,
    ),
    EngineeringTaskType.VALIDATION_VERIFICATION: EngineeringTaskDefinition(
        task_type=EngineeringTaskType.VALIDATION_VERIFICATION,
        name="Validation and Verification",
        description=(
            "Evaluate implementation evidence against explicit "
            "acceptance criteria and report verification status."
        ),
        required_inputs=(
            "tenant and work-item identity",
            "versioned acceptance criteria",
            "implementation and test evidence",
            "authorized workspace identity where applicable",
        ),
        expected_outputs=(
            "criterion-by-criterion verification results",
            "evidence references",
            "failed or inconclusive checks",
            "verification limitations",
        ),
        approval_boundaries=(
            "accepting or releasing a deliverable",
            "overriding failed or inconclusive verification",
            "changing acceptance criteria after evaluation begins",
        ),
        prohibited_actions=_COMMON_PROHIBITED_ACTIONS,
    ),
    EngineeringTaskType.SECURITY_REVIEW: EngineeringTaskDefinition(
        task_type=EngineeringTaskType.SECURITY_REVIEW,
        name="Security Review",
        description=(
            "Evaluate an assigned change or system for security risks, "
            "control weaknesses, and evidence-backed remediation needs."
        ),
        required_inputs=(
            "tenant and work-item identity",
            "authorized repository and workspace identity",
            "security review scope and applicable requirements",
            "relevant implementation and test evidence",
        ),
        expected_outputs=(
            "security findings with severity and supporting evidence",
            "affected components and potential impact",
            "recommended remediation options",
            "unresolved risks and verification limitations",
        ),
        approval_boundaries=(
            "modifying the reviewed implementation",
            "changing security policy or approved control requirements",
            "accepting residual risk or authorizing a release",
        ),
        prohibited_actions=_COMMON_PROHIBITED_ACTIONS,
    ),
}


if set(_TASK_DEFINITIONS) != set(EngineeringTaskType):
    raise RuntimeError(
        "Engineering task taxonomy must define every task type exactly once"
    )


ENGINEERING_TASK_DEFINITIONS: Mapping[
    EngineeringTaskType,
    EngineeringTaskDefinition,
] = MappingProxyType(_TASK_DEFINITIONS)


def get_engineering_task_definition(
    task_type: EngineeringTaskType | str,
) -> EngineeringTaskDefinition:
    """Return a recognized task definition; reject unknown identifiers."""

    if isinstance(task_type, EngineeringTaskType):
        normalized = task_type
    elif isinstance(task_type, str) and task_type.strip():
        try:
            normalized = EngineeringTaskType(task_type.strip())
        except ValueError as exc:
            raise UnknownEngineeringTaskTypeError(
                f"Unknown Engineering Agent task type: {task_type!r}"
            ) from exc
    else:
        raise UnknownEngineeringTaskTypeError(
            "task_type must be a recognized non-empty identifier"
        )

    try:
        return ENGINEERING_TASK_DEFINITIONS[normalized]
    except KeyError as exc:
        raise UnknownEngineeringTaskTypeError(
            f"Unknown Engineering Agent task type: {normalized!r}"
        ) from exc


def list_engineering_task_definitions(
) -> tuple[EngineeringTaskDefinition, ...]:
    """Return all definitions in stable taxonomy order."""

    return tuple(
        ENGINEERING_TASK_DEFINITIONS[task_type]
        for task_type in EngineeringTaskType
    )
