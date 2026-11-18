from dataclasses import FrozenInstanceError

import pytest

from backend.app.gagf.governance_agent_capability_vocabulary import (
    CAPABILITY_DEFINITIONS,
    CAPABILITY_IDS,
    CAPABILITY_VOCABULARY_ID,
    CAPABILITY_VOCABULARY_SCHEMA_VERSION,
    CAPABILITY_VOCABULARY_VERSION,
    LEGACY_CAPABILITY_ALIASES,
    AgentCapabilityCategory,
    AgentCapabilityVocabularyError,
    InvalidAgentCapabilityCollectionError,
    UnknownAgentCapabilityError,
    get_agent_capability_definition,
    list_agent_capability_definitions,
    normalize_agent_capabilities,
    resolve_legacy_agent_capability,
)


def test_vocabulary_has_expected_contract_identity():
    assert CAPABILITY_VOCABULARY_ID == (
        "gagf-agent-capability-vocabulary"
    )
    assert CAPABILITY_VOCABULARY_VERSION == "1.0.0"
    assert CAPABILITY_VOCABULARY_SCHEMA_VERSION == 1


def test_vocabulary_contains_expected_canonical_identifiers():
    assert CAPABILITY_IDS == (
        "expertise.security_review",
        "runtime.python",
        "tool.pytest",
    )


@pytest.mark.parametrize(
    ("capability_id", "category"),
    (
        ("runtime.python", AgentCapabilityCategory.RUNTIME),
        ("tool.pytest", AgentCapabilityCategory.TOOL),
        (
            "expertise.security_review",
            AgentCapabilityCategory.EXPERTISE,
        ),
    ),
)
def test_capability_definition_has_expected_category(
    capability_id,
    category,
):
    definition = get_agent_capability_definition(capability_id)

    assert definition.capability_id == capability_id
    assert definition.category is category
    assert definition.description


def test_capability_definitions_are_immutable():
    definition = get_agent_capability_definition("runtime.python")

    with pytest.raises(FrozenInstanceError):
        definition.description = "Changed"

    with pytest.raises(TypeError):
        CAPABILITY_DEFINITIONS["new.capability"] = definition


def test_legacy_alias_mapping_is_immutable():
    with pytest.raises(TypeError):
        LEGACY_CAPABILITY_ALIASES["new-alias"] = "runtime.python"


def test_definition_listing_is_deterministic():
    first = list_agent_capability_definitions()
    second = list_agent_capability_definitions()

    assert first == second
    assert tuple(item.capability_id for item in first) == CAPABILITY_IDS


def test_normalization_sorts_and_deduplicates_capabilities():
    result = normalize_agent_capabilities(
        (
            "tool.pytest",
            "runtime.python",
            "tool.pytest",
        )
    )

    assert result == ("runtime.python", "tool.pytest")


def test_normalization_accepts_empty_collection():
    assert normalize_agent_capabilities(()) == ()


@pytest.mark.parametrize(
    "capability_id",
    (
        "python",
        "pytest",
        "security-review",
        "unknown.capability",
        "",
        "   ",
    ),
)
def test_canonical_lookup_rejects_unknown_or_legacy_identifiers(
    capability_id,
):
    with pytest.raises(AgentCapabilityVocabularyError):
        get_agent_capability_definition(capability_id)


@pytest.mark.parametrize(
    "capabilities",
    (
        "runtime.python",
        b"runtime.python",
        None,
        42,
    ),
)
def test_normalization_rejects_invalid_collections(capabilities):
    with pytest.raises(InvalidAgentCapabilityCollectionError):
        normalize_agent_capabilities(capabilities)


@pytest.mark.parametrize(
    "capabilities",
    (
        ("runtime.python", ""),
        ("runtime.python", "   "),
        ("runtime.python", None),
        ("runtime.python", 42),
    ),
)
def test_normalization_rejects_invalid_collection_members(
    capabilities,
):
    with pytest.raises(InvalidAgentCapabilityCollectionError):
        normalize_agent_capabilities(capabilities)


def test_normalization_rejects_unknown_capabilities():
    with pytest.raises(UnknownAgentCapabilityError):
        normalize_agent_capabilities(
            ("runtime.python", "unknown.capability")
        )


@pytest.mark.parametrize(
    ("legacy_id", "canonical_id"),
    (
        ("python", "runtime.python"),
        ("pytest", "tool.pytest"),
        ("security-review", "expertise.security_review"),
    ),
)
def test_explicit_legacy_resolution(legacy_id, canonical_id):
    assert resolve_legacy_agent_capability(legacy_id) == canonical_id


def test_legacy_resolution_does_not_change_canonical_validation():
    with pytest.raises(UnknownAgentCapabilityError):
        normalize_agent_capabilities(("python",))


def test_unknown_legacy_identifier_is_rejected():
    with pytest.raises(UnknownAgentCapabilityError):
        resolve_legacy_agent_capability("unknown-legacy-capability")