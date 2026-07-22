from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import Mapping


class CalculationAuthority(str, Enum):
    NON_AUTHORITATIVE = "NON_AUTHORITATIVE"
    ADVISORY = "ADVISORY"
    AUTHORITATIVE = "AUTHORITATIVE"


class CalculationStatus(str, Enum):
    LEGACY_HEURISTIC = "LEGACY_HEURISTIC"
    PROVISIONAL_HEURISTIC = "PROVISIONAL_HEURISTIC"
    RESEARCH_CONSTRUCT = "RESEARCH_CONSTRUCT"
    VALIDATED = "VALIDATED"
    DEPRECATED = "DEPRECATED"


@dataclass(frozen=True, slots=True)
class ScientificCalculationContract:
    calculation_id: str
    calculation_version: str
    calculation_status: CalculationStatus
    authority: CalculationAuthority
    description: str

    def __post_init__(self) -> None:
        required_text_fields = {
            "calculation_id": self.calculation_id,
            "calculation_version": self.calculation_version,
            "description": self.description,
        }

        for field_name, value in required_text_fields.items():
            if not isinstance(value, str) or not value.strip():
                raise ValueError(
                    f"{field_name} must be a non-empty string"
                )

    def to_metadata(self) -> dict[str, str]:
        return {
            "calculation_id": self.calculation_id,
            "calculation_version": self.calculation_version,
            "calculation_status": self.calculation_status.value,
            "authority": self.authority.value,
        }


EVIDENCE_CONFIDENCE_CONTRACT = ScientificCalculationContract(
    calculation_id="evidence-confidence",
    calculation_version="0.1.0-diagnostics",
    calculation_status=CalculationStatus.PROVISIONAL_HEURISTIC,
    authority=CalculationAuthority.NON_AUTHORITATIVE,
    description=(
        "Diagnostics-based evidence confidence candidate using "
        "quality, agreement, conflict health, and source coverage."
    ),
)

LEGACY_METRIC_CONFIDENCE_CONTRACT = ScientificCalculationContract(
    calculation_id="metric-adapter-evidence-confidence",
    calculation_version="0.1.0-legacy",
    calculation_status=CalculationStatus.LEGACY_HEURISTIC,
    authority=CalculationAuthority.NON_AUTHORITATIVE,
    description=(
        "Legacy MetricAdapter confidence calculation retained "
        "for snapshot and ingestion compatibility."
    ),
)

ADAPTIVE_STATE_NORMALIZATION_CONTRACT = ScientificCalculationContract(
    calculation_id="adaptive-state-normalization",
    calculation_version="0.1.0-legacy",
    calculation_status=CalculationStatus.LEGACY_HEURISTIC,
    authority=CalculationAuthority.NON_AUTHORITATIVE,
    description=(
        "Legacy event-to-adaptive-state normalization rules."
    ),
)


_CALCULATION_CONTRACTS = {
    EVIDENCE_CONFIDENCE_CONTRACT.calculation_id: (
        EVIDENCE_CONFIDENCE_CONTRACT
    ),
    LEGACY_METRIC_CONFIDENCE_CONTRACT.calculation_id: (
        LEGACY_METRIC_CONFIDENCE_CONTRACT
    ),
    ADAPTIVE_STATE_NORMALIZATION_CONTRACT.calculation_id: (
        ADAPTIVE_STATE_NORMALIZATION_CONTRACT
    ),
}

CALCULATION_CONTRACTS: Mapping[
    str,
    ScientificCalculationContract,
] = MappingProxyType(_CALCULATION_CONTRACTS)


def get_calculation_contract(
    calculation_id: str,
) -> ScientificCalculationContract:
    try:
        return CALCULATION_CONTRACTS[calculation_id]
    except KeyError as exc:
        raise KeyError(
            f"Unknown scientific calculation: {calculation_id}"
        ) from exc


def list_calculation_contracts(
    *,
    authority: CalculationAuthority | None = None,
    status: CalculationStatus | None = None,
) -> tuple[ScientificCalculationContract, ...]:
    contracts = CALCULATION_CONTRACTS.values()

    if authority is not None:
        contracts = (
            contract
            for contract in contracts
            if contract.authority == authority
        )

    if status is not None:
        contracts = (
            contract
            for contract in contracts
            if contract.calculation_status == status
        )

    return tuple(
        sorted(
            contracts,
            key=lambda contract: contract.calculation_id,
        )
    )
