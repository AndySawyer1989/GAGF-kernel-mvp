from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class TimestampQuality(str, Enum):
    SOURCE_OCCURRED_AT = "SOURCE_OCCURRED_AT"
    BACKFILLED_FROM_CREATED_AT = "BACKFILLED_FROM_CREATED_AT"
    MISSING_TIMESTAMP = "MISSING_TIMESTAMP"


class RawSecurityEvent(BaseModel):
    event_id: str
    event_type: str
    event_occurred_at: Optional[str] = None
    event_created_at: Optional[str] = None
    timestamp_quality: TimestampQuality
    kernel_eligible: bool = True
    source_system: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class NormalizationApplied(BaseModel):
    event_id: str
    event_type: str
    indicator: str
    delta: float


class EvidenceConfidence(BaseModel):
    score: float
    factors: Dict[str, float]


class AdaptiveState(BaseModel):
    risk_index: float = 0.10
    uncertainty: float = 0.10
    coherence_psi: float = 0.85
    revision_pressure: float = 0.10
    governance_momentum: float = 0.50


class MetricAdapterResult(BaseModel):
    adaptive_state: AdaptiveState
    evidence_confidence: EvidenceConfidence
    evidence: List[str]
    normalization_applied: List[NormalizationApplied]


class DecisionMeta(BaseModel):
    is_override_triggered: bool
    hysteresis_buffer_active: bool = False
    policy_version: str
    policy_id: str


class ArbitrationResult(BaseModel):
    snapshot_id: Optional[str] = None
    active_strategy: Optional[str] = None
    strategy_proposal: Optional[str] = None
    kernel_decision: str
    selected_strategy: Optional[str] = None
    reason: List[str]
    decision_meta: DecisionMeta


class AdaptiveStateSnapshot(BaseModel):
    snapshot_id: str
    tenant_id: str
    work_item_id: str
    status: str
    adaptive_state: AdaptiveState
    evidence_confidence: EvidenceConfidence
    evidence: List[str]
    timestamp_quality_distribution: Dict[str, int] = Field(default_factory=dict)