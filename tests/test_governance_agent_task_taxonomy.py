import pytest

from backend.app.gagf.governance_agent_task_taxonomy import (
    ENGINEERING_TASK_DEFINITIONS,
    ENGINEERING_TASK_TAXONOMY_VERSION,
    EngineeringTaskDefinition,
    EngineeringTaskTaxonomyError,
    EngineeringTaskType,
    UnknownEngineeringTaskTypeError,
    get_engineering_task_definition,
    list_engineering_task_definitions,
)


def test_taxonomy_has_expected_version():
    assert ENGINEERING_TASK_TAXONOMY_VERSION == "1.1.0"


def test_every_task_type_has_exactly_one_definition():
    definitions = list_engineering_task_definitions()

    assert len(definitions) == len(EngineeringTaskType)
    assert {
        definition.task_type for definition in definitions
    } == set(EngineeringTaskType)


@pytest.mark.parametrize(
    "task_type",
    list(EngineeringTaskType),
)
def test_each_task_type_resolves_by_enum_and_identifier(task_type):
    by_enum = get_engineering_task_definition(task_type)
    by_identifier = get_engineering_task_definition(task_type.value)

    assert by_enum is by_identifier
    assert by_enum.task_type is task_type


def test_unknown_task_type_fails_closed():
    with pytest.raises(UnknownEngineeringTaskTypeError):
        get_engineering_task_definition("repository.execute_anything")


@pytest.mark.parametrize("task_type", ["", " ", None, 123])
def test_invalid_task_type_fails_closed(task_type):
    with pytest.raises(UnknownEngineeringTaskTypeError):
        get_engineering_task_definition(task_type)


def test_taxonomy_registry_is_immutable():
    with pytest.raises(TypeError):
        ENGINEERING_TASK_DEFINITIONS[
            EngineeringTaskType.CODE_CHANGE
        ] = ENGINEERING_TASK_DEFINITIONS[
            EngineeringTaskType.REPOSITORY_ANALYSIS
        ]


def test_task_definition_is_immutable():
    definition = get_engineering_task_definition(
        EngineeringTaskType.CODE_CHANGE
    )

    with pytest.raises((AttributeError, TypeError)):
        definition.name = "Unauthorized replacement"


def test_code_change_has_explicit_integration_approval_boundaries():
    definition = get_engineering_task_definition(
        EngineeringTaskType.CODE_CHANGE
    )

    assert "committing or pushing changes" in definition.approval_boundaries
    assert "merging into a protected branch" in definition.approval_boundaries
    assert "deploying or releasing changes" in definition.approval_boundaries


def test_all_task_types_preserve_common_prohibited_actions():
    expected = {
        "accessing secrets or credentials not explicitly authorized",
        "modifying files outside the assigned workspace",
        "committing, pushing, merging, or deploying changes without approval",
        "changing governance policy or Kernel authority",
        "treating unverified output as validated evidence",
    }

    for definition in list_engineering_task_definitions():
        assert expected.issubset(set(definition.prohibited_actions))


def test_task_definition_rejects_mutable_or_empty_contract_fields():
    with pytest.raises(EngineeringTaskTaxonomyError):
        EngineeringTaskDefinition(
            task_type=EngineeringTaskType.CODE_CHANGE,
            name="Code Change",
            description="A test definition",
            required_inputs=[],
            expected_outputs=("result",),
            approval_boundaries=("approval",),
            prohibited_actions=("prohibited",),
        )


def test_security_review_task_definition():
    definition = get_engineering_task_definition(
        EngineeringTaskType.SECURITY_REVIEW
    )

    assert definition.task_type is EngineeringTaskType.SECURITY_REVIEW
    assert definition.name == "Security Review"
    assert "security risks" in definition.description
    assert "security findings with severity and supporting evidence" in (
        definition.expected_outputs
    )
    assert "accepting residual risk or authorizing a release" in (
        definition.approval_boundaries
    )
