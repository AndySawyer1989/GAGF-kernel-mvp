from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import Final


CAPABILITY_VOCABULARY_ID: Final[str] = (
    "gagf-agent-capability-vocabulary"
)
CAPABILITY_VOCABULARY_VERSION: Final[str] = "1.0.0"
CAPABILITY_VOCABULARY_SCHEMA_VERSION: Final[int] = 1


class AgentCapabilityVocabularyError(ValueError):
    """Base error for capability vocabulary validation."""


class UnknownAgentCapabilityError(AgentCapabilityVocabularyError):
    """Raised when a capability identifier is not canonical."""


class InvalidAgentCapabilityCollectionError(
    AgentCapabilityVocabularyError
):
    """Raised when a capability collection is malformed."""


class AgentCapabilityCategory(str, Enum):
    RUNTIME = "runtime"
    TOOL = "tool"
    EXPERTISE = "expertise"


@dataclass(frozen=True, slots=True)
class AgentCapabilityDefinition:
    capability_id: str
    category: AgentCapabilityCategory
    description: str


_DEFINITIONS: Final[tuple[AgentCapabilityDefinition, ...]] = (
    AgentCapabilityDefinition(
        capability_id="runtime.python",
        category=AgentCapabilityCategory.RUNTIME,
        description="Worker declares support for the Python runtime.",
    ),
    AgentCapabilityDefinition(
        capability_id="tool.pytest",
        category=AgentCapabilityCategory.TOOL,
        description="Worker declares availability of the pytest tool.",
    ),
    AgentCapabilityDefinition(
        capability_id="expertise.security_review",
        category=AgentCapabilityCategory.EXPERTISE,
        description="Worker declares competence in security review.",
    ),
)

CAPABILITY_DEFINITIONS: Final = MappingProxyType(
    {
        definition.capability_id: definition
        for definition in _DEFINITIONS
    }
)

CAPABILITY_IDS: Final[tuple[str, ...]] = tuple(
    sorted(CAPABILITY_DEFINITIONS)
)

# Migration-only aliases. Canonical validation never accepts these.
LEGACY_CAPABILITY_ALIASES: Final = MappingProxyType(
    {
        "python": "runtime.python",
        "pytest": "tool.pytest",
        "security-review": "expertise.security_review",
    }
)


def get_agent_capability_definition(
    capability_id: str,
) -> AgentCapabilityDefinition:
    if not isinstance(capability_id, str) or not capability_id.strip():
        raise InvalidAgentCapabilityCollectionError(
            "capability_id must be a non-empty string"
        )

    normalized = capability_id.strip()
    definition = CAPABILITY_DEFINITIONS.get(normalized)

    if definition is None:
        raise UnknownAgentCapabilityError(
            f"Unknown agent capability: {normalized}"
        )

    return definition


def list_agent_capability_definitions(
) -> tuple[AgentCapabilityDefinition, ...]:
    return tuple(
        CAPABILITY_DEFINITIONS[capability_id]
        for capability_id in CAPABILITY_IDS
    )


def normalize_agent_capabilities(
    capabilities: Iterable[str],
) -> tuple[str, ...]:
    if isinstance(capabilities, (str, bytes)):
        raise InvalidAgentCapabilityCollectionError(
            "capabilities must be a collection of strings"
        )

    try:
        supplied = tuple(capabilities)
    except TypeError as exc:
        raise InvalidAgentCapabilityCollectionError(
            "capabilities must be iterable"
        ) from exc

    normalized: set[str] = set()

    for capability_id in supplied:
        if (
            not isinstance(capability_id, str)
            or not capability_id.strip()
        ):
            raise InvalidAgentCapabilityCollectionError(
                "capabilities must contain non-empty strings"
            )

        canonical_id = capability_id.strip()
        get_agent_capability_definition(canonical_id)
        normalized.add(canonical_id)

    return tuple(sorted(normalized))


def resolve_legacy_agent_capability(legacy_id: str) -> str:
    """Resolve an explicitly recognized identifier for migration tooling."""
    if not isinstance(legacy_id, str) or not legacy_id.strip():
        raise InvalidAgentCapabilityCollectionError(
            "legacy_id must be a non-empty string"
        )

    normalized = legacy_id.strip()

    try:
        return LEGACY_CAPABILITY_ALIASES[normalized]
    except KeyError as exc:
        raise UnknownAgentCapabilityError(
            f"Unknown legacy agent capability: {normalized}"
        ) from exc