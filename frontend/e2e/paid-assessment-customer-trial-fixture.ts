/**
 * 04H-01 — Paid Assessment Customer Trial Fixture
 *
 * Purpose:
 * Provide synthetic-but-realistic commercial assessment input for the
 * real browser-driven FIP paid-assessment workflow.
 *
 * This fixture intentionally separates:
 *
 * 1. submittedFacts
 *    Facts the browser/operator supplies.
 *
 * 2. blindGroundTruth
 *    Independently defined characteristics of the synthetic scenario.
 *    Browser workflow assertions MUST NOT use these values to predict
 *    the dominant diagnosis.
 *
 * The browser test proves workflow correctness.
 * Governed execution proves execution correctness.
 * Separate diagnostic evaluation proves diagnostic correctness.
 */

export const CUSTOMER_TRIAL_ID =
  "04H-01-CUSTOMER-TRIAL-001";

export const customerTrialIdentity = {
  clientId:
    "client-northstar-logistics",
  clientDisplayName:
    "Northstar Logistics Group",
  engagementId:
    "engagement-governance-health-001",
  assessmentId:
    "assessment-customer-trial-001",
  assessmentName:
    "Northstar Logistics Governance Assessment"
} as const;

export const customerTrialScope = {
  periodStart:
    "2026-07-01",

  periodEnd:
    "2026-07-31",

  workflowNames: [
    "Production change approval",
    "Security exception review",
    "Cross-team dependency resolution",
    "Release readiness"
  ],

  organizationalUnits: [
    "Platform Engineering",
    "Security Engineering",
    "Application Delivery",
    "Operations"
  ],

  objectives: [
    "Measure governance friction affecting production delivery",
    "Identify recurring structural constraints in approval and dependency workflows",
    "Produce an evidence-bound governed diagnostic"
  ],

  expectedOutcomes: [
    "Governed assessment results",
    "Explainable friction findings",
    "Prioritized structural observations",
    "Delivery-ready assessment package"
  ]
} as const;

export const customerTrialEvidenceCommitment = {
  requirementId:
    "REQ-CUSTOMER-TRIAL-001",

  minimumRecordCount:
    30,

  requirementDescription:
    "Workflow event evidence covering approvals, dependencies, blocks, security reviews, escalations, ownership gaps, and environment failures during the assessment period.",

  sourceId:
    "source-synthetic-workflow-export",

  sourceDisplayName:
    "Synthetic Workflow Event Export"
} as const;

/**
 * Synthetic evidence is deliberately realistic but does not encode a
 * declared diagnosis.
 *
 * Repeated events exist because the customer-trial scenario is intended
 * to contain measurable friction rather than a trivial happy path.
 *
 * Do not infer:
 *
 *   frequency == dominance
 *   dominance == root cause
 *   rank #1 == primary diagnosis
 *   significance == systemic scope
 */
export const customerTrialEvidenceCsv = `event_id,event_type,occurred_at,work_item_id
trial-event-001,APPROVAL_REQUIRED,2026-07-01T13:05:00Z,CHANGE-1001
trial-event-002,APPROVAL_DELAYED,2026-07-01T17:40:00Z,CHANGE-1001
trial-event-003,DEPENDENCY_WAIT,2026-07-02T14:10:00Z,CHANGE-1002
trial-event-004,WORK_BLOCKED,2026-07-02T18:25:00Z,CHANGE-1002
trial-event-005,SECURITY_REVIEW,2026-07-03T15:20:00Z,CHANGE-1003
trial-event-006,APPROVAL_DELAYED,2026-07-04T16:45:00Z,CHANGE-1003
trial-event-007,OWNERSHIP_GAP,2026-07-07T13:15:00Z,CHANGE-1004
trial-event-008,ESCALATION,2026-07-07T18:30:00Z,CHANGE-1004
trial-event-009,APPROVAL_REQUIRED,2026-07-08T14:05:00Z,CHANGE-1005
trial-event-010,APPROVAL_DELAYED,2026-07-09T12:50:00Z,CHANGE-1005
trial-event-011,DEPENDENCY_WAIT,2026-07-09T16:10:00Z,CHANGE-1006
trial-event-012,WORK_BLOCKED,2026-07-10T15:35:00Z,CHANGE-1006
trial-event-013,ENVIRONMENT_FAILURE,2026-07-11T17:00:00Z,CHANGE-1007
trial-event-014,WORK_BLOCKED,2026-07-11T18:20:00Z,CHANGE-1007
trial-event-015,SECURITY_REVIEW,2026-07-14T13:25:00Z,CHANGE-1008
trial-event-016,APPROVAL_DELAYED,2026-07-14T19:05:00Z,CHANGE-1008
trial-event-017,APPROVAL_REJECTED,2026-07-15T14:40:00Z,CHANGE-1009
trial-event-018,SECURITY_REVIEW,2026-07-16T12:15:00Z,CHANGE-1009
trial-event-019,DEPENDENCY_WAIT,2026-07-17T13:55:00Z,CHANGE-1010
trial-event-020,ESCALATION,2026-07-17T17:30:00Z,CHANGE-1010
trial-event-021,APPROVAL_REQUIRED,2026-07-20T13:10:00Z,CHANGE-1011
trial-event-022,APPROVAL_DELAYED,2026-07-20T18:45:00Z,CHANGE-1011
trial-event-023,OWNERSHIP_GAP,2026-07-21T14:20:00Z,CHANGE-1012
trial-event-024,DEPENDENCY_WAIT,2026-07-22T12:40:00Z,CHANGE-1012
trial-event-025,WORK_BLOCKED,2026-07-22T16:55:00Z,CHANGE-1012
trial-event-026,SECURITY_REVIEW,2026-07-23T13:35:00Z,CHANGE-1013
trial-event-027,APPROVAL_DELAYED,2026-07-24T17:10:00Z,CHANGE-1013
trial-event-028,ENVIRONMENT_FAILURE,2026-07-27T15:00:00Z,CHANGE-1014
trial-event-029,DEPENDENCY_WAIT,2026-07-27T16:35:00Z,CHANGE-1014
trial-event-030,WORK_BLOCKED,2026-07-28T13:50:00Z,CHANGE-1014
trial-event-031,APPROVAL_REQUIRED,2026-07-29T12:25:00Z,CHANGE-1015
trial-event-032,APPROVAL_DELAYED,2026-07-29T18:05:00Z,CHANGE-1015
trial-event-033,ESCALATION,2026-07-30T14:30:00Z,CHANGE-1016
trial-event-034,OVERRIDE,2026-07-30T17:45:00Z,CHANGE-1016
trial-event-035,SECURITY_REVIEW,2026-07-31T13:05:00Z,CHANGE-1017
trial-event-036,APPROVAL_DELAYED,2026-07-31T18:15:00Z,CHANGE-1017`;

export const customerTrialDelivery = {
  preparedBy:
    "FIP Customer Trial Operator",

  maximumPriorities:
    5
} as const;

/**
 * Browser-visible facts that may safely be asserted by the E2E test.
 *
 * There is deliberately no expected dominant constraint, primary
 * diagnosis, root cause, or intervention authority here.
 */
export const customerTrialWorkflowExpectations = {
  evidenceRecordCount:
    36,

  completionSignals: [
    "Assessment executed",
    "Open assessment"
  ]
} as const;

/**
 * Independent blind-test ground truth.
 *
 * This describes the synthetic scenario design, NOT what FIP is required
 * to rank first.
 *
 * It is intentionally excluded from browser workflow expectations.
 */
export const customerTrialBlindGroundTruth = {
  scenarioId:
    "northstar-governance-friction-001",

  knownFacts: [
    "The evidence contains repeated approval delays.",
    "The evidence contains repeated dependency waits.",
    "The evidence contains work-blocking events.",
    "The evidence contains security-review events.",
    "The evidence contains ownership gaps.",
    "The evidence contains escalations.",
    "The evidence contains environment failures.",
    "The evidence contains one governed override event."
  ],

  prohibitedAssumptions: [
    "The most frequent event type is automatically the dominant constraint.",
    "The dominant constraint is automatically the primary diagnosis.",
    "The primary diagnosis is automatically a root cause.",
    "A root cause automatically confers intervention authority.",
    "Significance automatically implies systemic scope.",
    "Evidence confidence is overall diagnostic confidence."
  ]
} as const;