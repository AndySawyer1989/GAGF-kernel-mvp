export type GovernanceAssessmentDashboardSummary = {
  tenant_id: string;
  audit_event_count: number;
  audit_chain_valid: boolean;
  checkpoint_count: number;
  signed_checkpoint_count: number;
  active_signing_key_id: string | null;
  signing_key_count: number;
  key_activation_event_count: number;
};

export type GovernanceAssessmentRecord = {
  tenant_id: string;
  client_id: string;
  engagement_id: string;
  assessment_id: string;
  assessment_name: string;
  status: string;
  created_at: string;
  updated_at: string;
  record_hash: string;
  schema_version: string;
};

export type GovernanceAssessmentListItem =
  GovernanceAssessmentRecord;

export type GovernanceAssessmentListResponse = {
  items: GovernanceAssessmentListItem[];
  count: number;
};

export type GovernanceAssessmentListFilters = {
  clientId?: string;
  engagementId?: string;
};

export type GovernanceAssessmentIdentity = {
  tenantId: string;
  clientId: string;
  engagementId: string;
  assessmentId: string;
};

export type GovernanceAssessmentArtifactInventoryItem = {
  artifact_type: string;
  artifact_id: string;
  artifact_hash: string;
  sequence_number: number;
};

export type GovernanceAssessmentSummary = {
  hierarchy_key: string;
  assessment: GovernanceAssessmentRecord;
  artifact_inventory:
    GovernanceAssessmentArtifactInventoryItem[];
  artifact_count: number;
  repository_chain_valid: boolean;
  summary_hash: string;
  schema_version: string;
};

export type GovernanceAssessmentArtifact = {
  artifact_id: string;
  tenant_id: string;
  client_id: string;
  engagement_id: string;
  assessment_id: string;
  artifact_type: string;
  artifact_hash: string;
  payload: Record<string, unknown>;
  created_at: string;
  sequence_number: number;
  previous_artifact_hash: string | null;
  chain_hash: string;
  schema_version: string;
};

export type GovernanceAssessmentArtifactList = {
  hierarchy_key: string;
  items: GovernanceAssessmentArtifact[];
  count: number;
};


export type GovernanceAssessmentReportSection = {
  section_id: string;
  kind: string;
  order: number;
  title: string;
  markdown: string;
};

export type GovernanceAssessmentReportManifest = {
  tenant_id: string;
  client_id: string;
  engagement_id: string;
  assessment_id: string;
  assessment_name: string;
  report_id: string;
  section_count: number;
  section_ids: string[];
  markdown_hash: string;
  package_hash: string;
  schema_version: string;
  source_commitments: Record<string, string>;
};

export type GovernanceAssessmentClientReport = {
  hierarchy_key: string;
  title: string;
  report_id: string;
  markdown: string;
  manifest: GovernanceAssessmentReportManifest;
  sections: GovernanceAssessmentReportSection[];
};

export function extractClientReport(
  artifacts: GovernanceAssessmentArtifactList
): GovernanceAssessmentClientReport | null {
  const artifact = artifacts.items.find(
    (item) =>
      item.artifact_type === "client-report-package"
  );

  if (!artifact) {
    return null;
  }

  const payload = artifact.payload;

  if (
    typeof payload.title !== "string" ||
    typeof payload.report_id !== "string" ||
    typeof payload.markdown !== "string" ||
    !Array.isArray(payload.sections) ||
    typeof payload.manifest !== "object" ||
    payload.manifest === null
  ) {
    return null;
  }

  return payload as GovernanceAssessmentClientReport;
}


export type AssessmentEvidenceRequirement = {
  requirement_id: string;
  source_kind: "csv";
  description: string;
  required: boolean;
  minimum_record_count: number;
};

export type AssessmentEvidenceInput = {
  source: {
    source_id: string;
    kind: "csv";
    display_name: string;
    source_location?: string;
  };
  csv_text: string;
};

export type AssessmentExecutionRequest = {
  tenant_id: string;
  client_id: string;
  engagement_id: string;
  assessment_id: string;
  assessment_name: string;
  workflow_names: string[];
  organizational_units: string[];
  period_start: string;
  period_end: string;
  objectives: string[];
  expected_outcomes: string[];
  evidence_requirements: AssessmentEvidenceRequirement[];
  evidence_inputs: AssessmentEvidenceInput[];
  client_display_name: string;
  prepared_by: string;
  exclusions?: string[];
  maximum_priorities?: number;
};

export type AssessmentExecutionResponse = {
  completed: boolean;
  hierarchy_key: string;
  artifact_count: number;
  request_hash: string;
  demonstration_hash: string;
  persistence_hash: string;
  report_id: string;
  application_hash: string;
  schema_version?: string;
};

export type CommercialEvidenceDeclarationRequest = {
  evidence_id: string;
  source_kind: string;
  description: string;
  classification: string;
  client_authorized_for_assessment: boolean;
  minimization_review_completed: boolean;
  direct_identifiers_removed: boolean;
};

export type CommercialStorageDeclarationRequest = {
  operator_controlled_location: boolean;
  access_restricted: boolean;
  storage_protection_confirmed: boolean;
  backup_plan_recorded: boolean;
  retention_period_recorded: boolean;
  deletion_plan_recorded: boolean;
};

export type CommercialPaidAssessmentIntakeRequest = {
  tenant_id: string;
  client_id: string;
  engagement_id: string;
  assessment_id: string;
  client_display_name: string;
  assessment_name: string;
  operator_name: string;
  client_contact_name: string;
  assessment_scope_confirmed: boolean;
  evidence_scope_confirmed: boolean;
  client_data_use_confirmed: boolean;
  operator_readiness_confirmed: boolean;
  evidence: CommercialEvidenceDeclarationRequest[];
  storage: CommercialStorageDeclarationRequest;
};

export type CommercialContractExecutionEventRequest = {
  contract_execution_event_id: string;
  contract_executed: boolean;
  contract_execution_review_ready: boolean;
  contract_execution_confirmed: boolean;
  executed_contract_reference_recorded: boolean;
  executed_at_recorded: boolean;
  all_required_signatures_recorded: boolean;
  human_operator_confirmed_execution: boolean;
  requires_final_paid_work_authorization: boolean;
  human_boundary_required: boolean;
  gagf_kernel_authoritative: boolean;
  ai_override_allowed: boolean;
};

export type CommercialPaidWorkAuthorizationRequest = {
  authorization_id: string;
  tenant_id: string;
  client_id: string;
  engagement_id: string;
  assessment_id: string;
  contract_execution_event_id: string;
  authorized_by: string;
  authorized_at: string;
  paid_assessment_authorized: boolean;
};

export type CommercialExecutionEvidenceApprovalRequest = {
  evidence_id: string;
  approved_content_sha256: string;
  approved_by: string;
  approved_at: string;
  execution_evidence_approved: boolean;
};

export type CommercialPaidAssessmentExecutionRequest = {
  intake: CommercialPaidAssessmentIntakeRequest;
  contract_execution_event: CommercialContractExecutionEventRequest;
  paid_work_authorization: CommercialPaidWorkAuthorizationRequest;
  execution_evidence_approvals:
    CommercialExecutionEvidenceApprovalRequest[];
};

export type CommercialPaidAssessmentDisposition =
  | "executed"
  | "resumed"
  | "reconciled";

export type CommercialPaidAssessmentExecutionResult = {
  recovery_type: string;
  recovery_version: string;
  schema_version: string;
  attempt_hash: string;
  record_hash: string;
  hierarchy_key: string;
  disposition: CommercialPaidAssessmentDisposition;
  artifact_count_before: number;
  artifact_count_after: number;
  execution_result: unknown;
  boundaries: Record<string, boolean>;
};

export type CommercialPaidAssessmentExecutionInputBinding = {
  hierarchy_key: string;
  assessment_execution_request_hash: string;
  execution_input_hash: string;
  binding_hash: string;
  schema_version: string;
};

export type CommercialPaidAssessmentEvidenceBindingMetadata = {
  evidence_id: string;
  source_id: string;
  source_kind: string;
  display_name: string;
  source_location: string | null;
  content_sha256: string;
};

export type CommercialPaidAssessmentExecutionInputBindingMetadata = {
  hierarchy_key: string;
  assessment_name: string;
  client_display_name: string;
  assessment_execution_request_hash: string;
  execution_input_hash: string;
  binding_hash: string;
  schema_version: string;
  evidence: CommercialPaidAssessmentEvidenceBindingMetadata[];
  boundaries: {
    raw_evidence_not_exposed: boolean;
    binding_metadata_is_not_execution_authority: boolean;
    binding_metadata_is_not_evidence_approval: boolean;
  };
};

export type CommercialPaidAssessmentExecutionResponse = {
  operator_run_passed: true;
  result: CommercialPaidAssessmentExecutionResult;
  execution_input_binding:
    CommercialPaidAssessmentExecutionInputBinding;
  boundaries: {
    api_request_is_not_paid_work_authorization: boolean;
    api_request_is_not_execution_authority: boolean;
    api_request_is_not_recovery_authority: boolean;
    assessment_execution_request_is_server_bound: boolean;
    raw_execution_evidence_is_not_browser_resubmitted: boolean;
    browser_cannot_replace_bound_execution_input: boolean;
    repository_path_is_server_assigned: boolean;
    execution_database_is_hierarchy_scoped: boolean;
    recovery_service_remains_governed_authority_path: boolean;
  };
};

export type GovernanceAssessmentAuditEvent = {
  event_id: string;
  request_id: string;
  tenant_id: string;
  actor_id: string;
  actor_roles: string[];
  method: string;
  route: string;
  outcome: string;
  status_code: number;
  reason_code: string | null;
  occurred_at: string;
  previous_hash: string;
  event_hash: string;
  hash_version: string;
};

export type GovernanceAssessmentAuditEventList = {
  tenant_id: string;
  items: GovernanceAssessmentAuditEvent[];
  count: number;
  limit: number;
};

export type GovernanceAssessmentAuditIntegrity = {
  tenant_id: string;
  valid: boolean;
  checked_count: number;
  failure_index: number | null;
  failure_event_id: string | null;
  reason_code: string | null;
};

export type GovernanceAssessmentCheckpointList = {
  tenant_id: string;
  items: Array<Record<string, unknown>>;
  count: number;
  limit: number;
};

export type GovernanceAssessmentSignedVerification =
  | {
      available: true;
      payload: Record<string, unknown>;
    }
  | {
      available: false;
      status: number;
      code: string;
      message: string;
    };

export type GovernanceAssessmentSigningKey = {
  tenant_id: string;
  key_id: string;
  secret_reference: string;
  active: boolean;
  created_at: string;
  retired_at: string | null;
};

export type GovernanceAssessmentSigningKeyList = {
  tenant_id: string;
  items: GovernanceAssessmentSigningKey[];
  count: number;
};

export type GovernanceAssessmentSigningKeyAuditEvent = {
  tenant_id: string;
  event_id?: string;
  actor_id?: string;
  previous_key_id?: string | null;
  active_key_id?: string;
  event_type?: string;
  occurred_at?: string;
  created_at?: string;
  metadata?: Record<string, unknown>;
  [key: string]: unknown;
};

export type GovernanceAssessmentSigningKeyAuditList = {
  tenant_id: string;
  items: GovernanceAssessmentSigningKeyAuditEvent[];
  count: number;
  limit: number;
};

export type GovernanceAssessmentSignedCheckpointVerification = {
  tenant_id: string;
  items: Array<Record<string, unknown>>;
  count: number;
  valid_count: number;
  invalid_count: number;
  limit: number;
};

export type GovernanceAssessmentSigningKeyActivation = {
  tenant_id: string;
  key_id: string;
  active: boolean;
  retired_at: string | null;
};

export type GovernanceAssessmentAuditCheckpoint = {
  checkpoint_id: string;
  tenant_id: string;
  chain_head_hash: string;
  checked_count: number;
  valid: boolean;
  reason_code: string | null;
  created_at: string;
  checkpoint_version: string;
};

export type GovernanceAssessmentSignedAuditCheckpoint = {
  checkpoint: GovernanceAssessmentAuditCheckpoint;
  key_id: string;
  signature: string;
  signature_algorithm: string;
  signature_version: string;
};

export type GovernanceAssessmentSignedCheckpointList = {
  tenant_id: string;
  items: GovernanceAssessmentSignedAuditCheckpoint[];
  count: number;
  limit: number;
};

export type GovernanceAssessmentSignedCheckpointVerificationItem = {
  checkpoint_id: string;
  key_id: string;
  valid: boolean;
  reason_code: string | null;
};

export type GovernanceAssessmentSignedCheckpointVerificationList = {
  tenant_id: string;
  items: GovernanceAssessmentSignedCheckpointVerificationItem[];
  count: number;
  valid_count: number;
  invalid_count: number;
  limit: number;
};

export type GovernanceAssessmentCheckpointCreationResult = {
  checkpoint: GovernanceAssessmentAuditCheckpoint;
  key_id: string;
  signature: string;
  signature_algorithm: string;
  signature_version: string;
  signed: boolean;
};

export type GovernanceAssessmentApiConfig = {
  baseUrl: string;
  tenantId: string;
  actorId: string;
  actorRoles: string;
};

export class GovernanceAssessmentApiError extends Error {
  readonly status: number;
  readonly payload: unknown;

  constructor(
    message: string,
    status: number,
    payload: unknown
  ) {
    super(message);
    this.name = "GovernanceAssessmentApiError";
    this.status = status;
    this.payload = payload;
  }
}

export function getGovernanceAssessmentApiConfig():
  GovernanceAssessmentApiConfig {
  return {
    baseUrl:
      process.env.NEXT_PUBLIC_GAGF_API_BASE_URL ??
      "http://127.0.0.1:8000",
    tenantId:
      process.env.NEXT_PUBLIC_GAGF_TENANT_ID ??
      "tenant-alpha",
    actorId:
      process.env.NEXT_PUBLIC_GAGF_ACTOR_ID ??
      "console-admin",
    actorRoles:
      process.env.NEXT_PUBLIC_GAGF_ACTOR_ROLES ??
      "assessment:admin"
  };
}

export async function fetchDashboardSummary(
  config: GovernanceAssessmentApiConfig,
  signal?: AbortSignal
): Promise<GovernanceAssessmentDashboardSummary> {
  const url = new URL(
    "/api/v1/governance-assessments/dashboard-summary",
    config.baseUrl
  );

  url.searchParams.set("tenant_id", config.tenantId);

  const response = await fetch(url, {
    method: "GET",
    headers: {
      "X-Tenant-ID": config.tenantId,
      "X-Actor-ID": config.actorId,
      "X-Actor-Roles": config.actorRoles
    },
    cache: "no-store",
    signal
  });

  const payload: unknown = await response.json().catch(
    () => null
  );

  if (!response.ok) {
    throw new GovernanceAssessmentApiError(
      `Dashboard request failed with status ${response.status}`,
      response.status,
      payload
    );
  }

  return payload as GovernanceAssessmentDashboardSummary;
}

export async function fetchAssessments(
  config: GovernanceAssessmentApiConfig,
  filters: GovernanceAssessmentListFilters = {},
  signal?: AbortSignal
): Promise<GovernanceAssessmentListResponse> {
  const url = new URL(
    "/api/v1/governance-assessments",
    config.baseUrl
  );

  url.searchParams.set("tenant_id", config.tenantId);

  if (filters.clientId?.trim()) {
    url.searchParams.set(
      "client_id",
      filters.clientId.trim()
    );
  }

  if (filters.engagementId?.trim()) {
    url.searchParams.set(
      "engagement_id",
      filters.engagementId.trim()
    );
  }

  const response = await fetch(url, {
    method: "GET",
    headers: {
      "X-Tenant-ID": config.tenantId,
      "X-Actor-ID": config.actorId,
      "X-Actor-Roles": config.actorRoles
    },
    cache: "no-store",
    signal
  });

  const payload: unknown = await response.json().catch(
    () => null
  );

  if (!response.ok) {
    throw new GovernanceAssessmentApiError(
      `Assessment list request failed with status ${response.status}`,
      response.status,
      payload
    );
  }

if (
  typeof payload !== "object" ||
  payload === null ||
  (payload as AssessmentExecutionResponse).completed !== true ||
  typeof (
    payload as AssessmentExecutionResponse
  ).hierarchy_key !== "string" ||
  typeof (
    payload as AssessmentExecutionResponse
  ).artifact_count !== "number" ||
  typeof (
    payload as AssessmentExecutionResponse
  ).request_hash !== "string" ||
  typeof (
    payload as AssessmentExecutionResponse
  ).demonstration_hash !== "string" ||
  typeof (
    payload as AssessmentExecutionResponse
  ).persistence_hash !== "string" ||
  typeof (
    payload as AssessmentExecutionResponse
  ).report_id !== "string" ||
  typeof (
    payload as AssessmentExecutionResponse
  ).application_hash !== "string"
) {
  throw new GovernanceAssessmentApiError(
    "Assessment execution response did not match the expected contract",
    response.status,
    payload
  );
}
  return payload as GovernanceAssessmentListResponse;
}

export async function executeAssessment(
  config: GovernanceAssessmentApiConfig,
  request: AssessmentExecutionRequest,
  signal?: AbortSignal
): Promise<AssessmentExecutionResponse> {
  const url = new URL(
    "/api/v1/governance-assessments/execute",
    config.baseUrl
  );

  const response = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Tenant-ID": config.tenantId,
      "X-Actor-ID": config.actorId,
      "X-Actor-Roles": config.actorRoles
    },
    body: JSON.stringify(request),
    cache: "no-store",
    signal
  });

  const payload: unknown = await response.json().catch(
    () => null
  );

  if (!response.ok) {
    throw new GovernanceAssessmentApiError(
      `Assessment execution failed with status ${response.status}`,
      response.status,
      payload
    );
  }

  if (
    typeof payload !== "object" ||
    payload === null ||
    (payload as AssessmentExecutionResponse).completed !== true ||
    typeof (
      payload as AssessmentExecutionResponse
    ).application_hash !== "string"
  ) {
    throw new GovernanceAssessmentApiError(
      "Assessment execution response did not match the expected contract",
      response.status,
      payload
    );
  }

  return payload as AssessmentExecutionResponse;
}

export async function fetchPaidAssessmentExecutionInputBinding(
  config: GovernanceAssessmentApiConfig,
  identity: GovernanceAssessmentIdentity,
  signal?: AbortSignal
): Promise<CommercialPaidAssessmentExecutionInputBindingMetadata> {
  const segments = [
    identity.tenantId,
    identity.clientId,
    identity.engagementId,
    identity.assessmentId
  ].map(encodeURIComponent);

  const url = new URL(
    `/api/v1/governance-paid-assessments/${segments.join("/")}/execution-input-binding`,
    config.baseUrl
  );

  const response = await fetch(url, {
    method: "GET",
    headers: {
      "X-Tenant-ID": config.tenantId,
      "X-Actor-ID": config.actorId,
      "X-Actor-Roles": config.actorRoles
    },
    cache: "no-store",
    signal
  });

  const payload: unknown =
    await response.json().catch(
      () => null
    );

  if (!response.ok) {
    throw new GovernanceAssessmentApiError(
      `Paid assessment execution-input binding request failed with status ${response.status}`,
      response.status,
      payload
    );
  }

  if (
    typeof payload !== "object" ||
    payload === null
  ) {
    throw new GovernanceAssessmentApiError(
      "Paid assessment execution-input binding response did not match the expected contract",
      response.status,
      payload
    );
  }

  const binding =
    payload as CommercialPaidAssessmentExecutionInputBindingMetadata;

  if (
    typeof binding.hierarchy_key !== "string" ||
    typeof binding.assessment_name !== "string" ||
    typeof binding.client_display_name !== "string" ||
    typeof binding.assessment_execution_request_hash !==
      "string" ||
    typeof binding.execution_input_hash !== "string" ||
    typeof binding.binding_hash !== "string" ||
    typeof binding.schema_version !== "string" ||
    !Array.isArray(binding.evidence)
  ) {
    throw new GovernanceAssessmentApiError(
      "Paid assessment execution-input binding response did not match the expected contract",
      response.status,
      payload
    );
  }

  const expectedHierarchy = [
    identity.tenantId,
    identity.clientId,
    identity.engagementId,
    identity.assessmentId
  ].join("/");

  if (
    binding.hierarchy_key !==
    expectedHierarchy
  ) {
    throw new GovernanceAssessmentApiError(
      "Paid assessment execution-input binding hierarchy did not match the requested assessment",
      response.status,
      payload
    );
  }

  const validEvidence =
    binding.evidence.every(
      (item) =>
        typeof item === "object" &&
        item !== null &&
        typeof item.evidence_id === "string" &&
        typeof item.source_id === "string" &&
        typeof item.source_kind === "string" &&
        typeof item.display_name === "string" &&
        (
          item.source_location === null ||
          typeof item.source_location === "string"
        ) &&
        typeof item.content_sha256 === "string"
    );

  if (!validEvidence) {
    throw new GovernanceAssessmentApiError(
      "Paid assessment execution-input binding evidence did not match the expected contract",
      response.status,
      payload
    );
  }

  if (
    typeof binding.boundaries !== "object" ||
    binding.boundaries === null ||
    binding.boundaries.raw_evidence_not_exposed !==
      true ||
    binding.boundaries.binding_metadata_is_not_execution_authority !==
      true ||
    binding.boundaries.binding_metadata_is_not_evidence_approval !==
      true
  ) {
    throw new GovernanceAssessmentApiError(
      "Paid assessment execution-input binding boundaries did not match the expected contract",
      response.status,
      payload
    );
  }

  return binding;
}

export async function executePaidAssessment(
  config: GovernanceAssessmentApiConfig,
  request: CommercialPaidAssessmentExecutionRequest,
  signal?: AbortSignal
): Promise<CommercialPaidAssessmentExecutionResponse> {
  const url = new URL(
    "/api/v1/governance-paid-assessments/execute",
    config.baseUrl
  );

  const response = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Tenant-ID": config.tenantId,
      "X-Actor-ID": config.actorId,
      "X-Actor-Roles": config.actorRoles
    },
    body: JSON.stringify(request),
    cache: "no-store",
    signal
  });

  const payload: unknown = await response.json().catch(
    () => null
  );

  if (!response.ok) {
    throw new GovernanceAssessmentApiError(
      `Paid assessment execution failed with status ${response.status}`,
      response.status,
      payload
    );
  }

  if (
    typeof payload !== "object" ||
    payload === null ||
    (
      payload as CommercialPaidAssessmentExecutionResponse
    ).operator_run_passed !== true
  ) {
    throw new GovernanceAssessmentApiError(
      "Paid assessment execution response did not match the expected contract",
      response.status,
      payload
    );
  }

  const typedPayload =
    payload as CommercialPaidAssessmentExecutionResponse;

  const result = typedPayload.result;
  const binding =
    typedPayload.execution_input_binding;
  const boundaries =
    typedPayload.boundaries;

  if (
    typeof result !== "object" ||
    result === null ||
    typeof result.hierarchy_key !== "string" ||
    typeof result.attempt_hash !== "string" ||
    typeof result.record_hash !== "string" ||
    typeof result.artifact_count_before !== "number" ||
    typeof result.artifact_count_after !== "number" ||
    !(
      result.disposition === "executed" ||
      result.disposition === "resumed" ||
      result.disposition === "reconciled"
    )
  ) {
    throw new GovernanceAssessmentApiError(
      "Paid assessment execution result did not match the expected contract",
      response.status,
      payload
    );
  }

  if (
    typeof binding !== "object" ||
    binding === null ||
    typeof binding.hierarchy_key !== "string" ||
    typeof binding.assessment_execution_request_hash !==
      "string" ||
    typeof binding.execution_input_hash !== "string" ||
    typeof binding.binding_hash !== "string" ||
    typeof binding.schema_version !== "string" ||
    binding.hierarchy_key !== result.hierarchy_key
  ) {
    throw new GovernanceAssessmentApiError(
      "Paid assessment execution binding did not match the expected contract",
      response.status,
      payload
    );
  }

  if (
    typeof boundaries !== "object" ||
    boundaries === null ||
    boundaries.assessment_execution_request_is_server_bound !==
      true ||
    boundaries.raw_execution_evidence_is_not_browser_resubmitted !==
      true ||
    boundaries.browser_cannot_replace_bound_execution_input !==
      true ||
    boundaries.repository_path_is_server_assigned !==
      true ||
    boundaries.execution_database_is_hierarchy_scoped !==
      true ||
    boundaries.recovery_service_remains_governed_authority_path !==
      true
  ) {
    throw new GovernanceAssessmentApiError(
      "Paid assessment execution boundaries did not match the expected contract",
      response.status,
      payload
    );
  }

  return typedPayload;
}

function buildAssessmentPath(
  config: GovernanceAssessmentApiConfig,
  identity: GovernanceAssessmentIdentity
): URL {
  const segments = [
    identity.tenantId,
    identity.clientId,
    identity.engagementId,
    identity.assessmentId
  ].map(encodeURIComponent);

  return new URL(
    `/api/v1/governance-assessments/${segments.join("/")}`,
    config.baseUrl
  );
}

function assessmentHeaders(
  config: GovernanceAssessmentApiConfig
): HeadersInit {
  return {
    "X-Tenant-ID": config.tenantId,
    "X-Actor-ID": config.actorId,
    "X-Actor-Roles": config.actorRoles
  };
}

async function readAssessmentResponse<T>(
  response: Response,
  operation: string
): Promise<T> {
  const payload: unknown = await response.json().catch(
    () => null
  );

  if (!response.ok) {
    throw new GovernanceAssessmentApiError(
      `${operation} failed with status ${response.status}`,
      response.status,
      payload
    );
  }

  if (
    typeof payload !== "object" ||
    payload === null
  ) {
    throw new GovernanceAssessmentApiError(
      `${operation} returned an invalid response`,
      response.status,
      payload
    );
  }

  return payload as T;
}

export async function fetchAssessment(
  config: GovernanceAssessmentApiConfig,
  identity: GovernanceAssessmentIdentity,
  signal?: AbortSignal
): Promise<GovernanceAssessmentRecord> {
  const response = await fetch(
    buildAssessmentPath(config, identity),
    {
      method: "GET",
      headers: assessmentHeaders(config),
      cache: "no-store",
      signal
    }
  );

  return readAssessmentResponse<
    GovernanceAssessmentRecord
  >(response, "Assessment detail request");
}

export async function fetchAssessmentSummary(
  config: GovernanceAssessmentApiConfig,
  identity: GovernanceAssessmentIdentity,
  signal?: AbortSignal
): Promise<GovernanceAssessmentSummary> {
  const url = buildAssessmentPath(
    config,
    identity
  );

  url.pathname += "/summary";

  const response = await fetch(url, {
    method: "GET",
    headers: assessmentHeaders(config),
    cache: "no-store",
    signal
  });

  return readAssessmentResponse<
    GovernanceAssessmentSummary
  >(response, "Assessment summary request");
}

export async function fetchAssessmentArtifacts(
  config: GovernanceAssessmentApiConfig,
  identity: GovernanceAssessmentIdentity,
  signal?: AbortSignal
): Promise<GovernanceAssessmentArtifactList> {
  const url = buildAssessmentPath(
    config,
    identity
  );

  url.pathname += "/artifacts";

  const response = await fetch(url, {
    method: "GET",
    headers: assessmentHeaders(config),
    cache: "no-store",
    signal
  });

  return readAssessmentResponse<
    GovernanceAssessmentArtifactList
  >(response, "Assessment artifact request");
}

function buildAuditUrl(
  config: GovernanceAssessmentApiConfig,
  path: string
): URL {
  const url = new URL(path, config.baseUrl);

  url.searchParams.set(
    "tenant_id",
    config.tenantId
  );

  return url;
}

export async function fetchAuditEvents(
  config: GovernanceAssessmentApiConfig,
  signal?: AbortSignal
): Promise<GovernanceAssessmentAuditEventList> {
  const response = await fetch(
    buildAuditUrl(
      config,
      "/api/v1/governance-assessments/audit-events"
    ),
    {
      method: "GET",
      headers: assessmentHeaders(config),
      cache: "no-store",
      signal
    }
  );

  return readAssessmentResponse<
    GovernanceAssessmentAuditEventList
  >(response, "Audit event request");
}

export async function fetchAuditIntegrity(
  config: GovernanceAssessmentApiConfig,
  signal?: AbortSignal
): Promise<GovernanceAssessmentAuditIntegrity> {
  const response = await fetch(
    buildAuditUrl(
      config,
      "/api/v1/governance-assessments/audit-integrity"
    ),
    {
      method: "GET",
      headers: assessmentHeaders(config),
      cache: "no-store",
      signal
    }
  );

  return readAssessmentResponse<
    GovernanceAssessmentAuditIntegrity
  >(response, "Audit integrity request");
}

export async function fetchAuditCheckpoints(
  config: GovernanceAssessmentApiConfig,
  signal?: AbortSignal
): Promise<GovernanceAssessmentCheckpointList> {
  const response = await fetch(
    buildAuditUrl(
      config,
      "/api/v1/governance-assessments/audit-checkpoints"
    ),
    {
      method: "GET",
      headers: assessmentHeaders(config),
      cache: "no-store",
      signal
    }
  );

  return readAssessmentResponse<
    GovernanceAssessmentCheckpointList
  >(response, "Audit checkpoint request");
}

export async function fetchSignedAuditCheckpoints(
  config: GovernanceAssessmentApiConfig,
  signal?: AbortSignal
): Promise<GovernanceAssessmentCheckpointList> {
  const response = await fetch(
    buildAuditUrl(
      config,
      "/api/v1/governance-assessments/audit-checkpoints/signed"
    ),
    {
      method: "GET",
      headers: assessmentHeaders(config),
      cache: "no-store",
      signal
    }
  );

  return readAssessmentResponse<
    GovernanceAssessmentCheckpointList
  >(response, "Signed checkpoint request");
}

export async function verifySignedAuditCheckpoints(
  config: GovernanceAssessmentApiConfig,
  signal?: AbortSignal
): Promise<GovernanceAssessmentSignedVerification> {
  const response = await fetch(
    buildAuditUrl(
      config,
      "/api/v1/governance-assessments/audit-checkpoints/signed/verification"
    ),
    {
      method: "GET",
      headers: assessmentHeaders(config),
      cache: "no-store",
      signal
    }
  );

  const payload: unknown =
    await response.json().catch(() => null);

  if (response.ok) {
    return {
      available: true,
      payload:
        typeof payload === "object" &&
        payload !== null
          ? payload as Record<string, unknown>
          : {}
    };
  }

  if (
    response.status === 503 &&
    typeof payload === "object" &&
    payload !== null &&
    "detail" in payload
  ) {
    const detail = (
      payload as {
        detail?: unknown;
      }
    ).detail;

    if (
      typeof detail === "object" &&
      detail !== null
    ) {
      const record =
        detail as Record<string, unknown>;

      return {
        available: false,
        status: response.status,
        code:
          typeof record.code === "string"
            ? record.code
            : "VERIFIER_UNAVAILABLE",
        message:
          typeof record.message === "string"
            ? record.message
            : "Signed checkpoint verification is unavailable."
      };
    }
  }

  throw new GovernanceAssessmentApiError(
    `Signed checkpoint verification failed with status ${response.status}`,
    response.status,
    payload
  );
}

export async function createAuditCheckpoint(
  config: GovernanceAssessmentApiConfig,
  signal?: AbortSignal
): Promise<Record<string, unknown>> {
  const response = await fetch(
    buildAuditUrl(
      config,
      "/api/v1/governance-assessments/audit-checkpoints"
    ),
    {
      method: "POST",
      headers: assessmentHeaders(config),
      cache: "no-store",
      signal
    }
  );

  return readAssessmentResponse<
    Record<string, unknown>
  >(response, "Audit checkpoint creation");
}

function buildSigningKeyUrl(
  config: GovernanceAssessmentApiConfig,
  path: string
): URL {
  const url = new URL(path, config.baseUrl);

  url.searchParams.set(
    "tenant_id",
    config.tenantId
  );

  return url;
}

export async function fetchSigningKeys(
  config: GovernanceAssessmentApiConfig,
  signal?: AbortSignal
): Promise<GovernanceAssessmentSigningKeyList> {
  const response = await fetch(
    buildSigningKeyUrl(
      config,
      "/api/v1/governance-assessments/checkpoint-signing-keys"
    ),
    {
      method: "GET",
      headers: assessmentHeaders(config),
      cache: "no-store",
      signal
    }
  );

  return readAssessmentResponse<
    GovernanceAssessmentSigningKeyList
  >(response, "Signing key list request");
}

export async function fetchActiveSigningKey(
  config: GovernanceAssessmentApiConfig,
  signal?: AbortSignal
): Promise<GovernanceAssessmentSigningKey> {
  const response = await fetch(
    buildSigningKeyUrl(
      config,
      "/api/v1/governance-assessments/checkpoint-signing-keys/active"
    ),
    {
      method: "GET",
      headers: assessmentHeaders(config),
      cache: "no-store",
      signal
    }
  );

  return readAssessmentResponse<
    GovernanceAssessmentSigningKey
  >(response, "Active signing key request");
}

export async function fetchSigningKeyAuditEvents(
  config: GovernanceAssessmentApiConfig,
  signal?: AbortSignal
): Promise<GovernanceAssessmentSigningKeyAuditList> {
  const response = await fetch(
    buildSigningKeyUrl(
      config,
      "/api/v1/governance-assessments/checkpoint-signing-keys/audit-events"
    ),
    {
      method: "GET",
      headers: assessmentHeaders(config),
      cache: "no-store",
      signal
    }
  );

  return readAssessmentResponse<
    GovernanceAssessmentSigningKeyAuditList
  >(response, "Signing key audit request");
}

export async function fetchSignedCheckpointVerification(
  config: GovernanceAssessmentApiConfig,
  signal?: AbortSignal
): Promise<GovernanceAssessmentSignedCheckpointVerification> {
  const response = await fetch(
    buildSigningKeyUrl(
      config,
      "/api/v1/governance-assessments/audit-checkpoints/signed/verification"
    ),
    {
      method: "GET",
      headers: assessmentHeaders(config),
      cache: "no-store",
      signal
    }
  );

  return readAssessmentResponse<
    GovernanceAssessmentSignedCheckpointVerification
  >(response, "Signed checkpoint verification request");
}

export async function activateSigningKey(
  config: GovernanceAssessmentApiConfig,
  keyId: string,
  signal?: AbortSignal
): Promise<GovernanceAssessmentSigningKeyActivation> {
  const encodedKeyId = encodeURIComponent(keyId);

  const response = await fetch(
    buildSigningKeyUrl(
      config,
      `/api/v1/governance-assessments/checkpoint-signing-keys/${encodedKeyId}/activate`
    ),
    {
      method: "POST",
      headers: assessmentHeaders(config),
      cache: "no-store",
      signal
    }
  );

  return readAssessmentResponse<
    GovernanceAssessmentSigningKeyActivation
  >(response, "Signing key activation request");
}

export async function createSignedAuditCheckpoint(
  config: GovernanceAssessmentApiConfig,
  signal?: AbortSignal
): Promise<GovernanceAssessmentCheckpointCreationResult> {
  const response = await fetch(
    buildAuditUrl(
      config,
      "/api/v1/governance-assessments/audit-checkpoints"
    ),
    {
      method: "POST",
      headers: assessmentHeaders(config),
      cache: "no-store",
      signal
    }
  );

  return readAssessmentResponse<
    GovernanceAssessmentCheckpointCreationResult
  >(response, "Signed audit checkpoint creation");
}

export async function fetchSignedAuditCheckpointRecords(
  config: GovernanceAssessmentApiConfig,
  signal?: AbortSignal
): Promise<GovernanceAssessmentSignedCheckpointList> {
  const response = await fetch(
    buildAuditUrl(
      config,
      "/api/v1/governance-assessments/audit-checkpoints/signed"
    ),
    {
      method: "GET",
      headers: assessmentHeaders(config),
      cache: "no-store",
      signal
    }
  );

  return readAssessmentResponse<
    GovernanceAssessmentSignedCheckpointList
  >(response, "Signed audit checkpoint list request");
}

export async function fetchSignedAuditCheckpointVerificationRecords(
  config: GovernanceAssessmentApiConfig,
  signal?: AbortSignal
): Promise<GovernanceAssessmentSignedCheckpointVerificationList> {
  const response = await fetch(
    buildAuditUrl(
      config,
      "/api/v1/governance-assessments/audit-checkpoints/signed/verification"
    ),
    {
      method: "GET",
      headers: assessmentHeaders(config),
      cache: "no-store",
      signal
    }
  );

  return readAssessmentResponse<
    GovernanceAssessmentSignedCheckpointVerificationList
  >(response, "Signed audit checkpoint verification request");
}
export type CommercialPaidAssessmentExecutionStatusMetadata = {
  disposition: CommercialPaidAssessmentDisposition;
  artifact_count_before: number;
  artifact_count_after: number;
  attempt_hash: string;
  attempt_record_hash: string;
  assessment_execution_request_hash: string;
  execution_input_binding_hash: string;
  status_recorded_at: string;
  schema_version: string;
};

export type CommercialPaidAssessmentExecutionStatusResponse = {
  found: boolean;
  hierarchy_key: string;
  status:
    | CommercialPaidAssessmentExecutionStatusMetadata
    | null;
  boundaries: {
    status_is_read_only: boolean;
    status_is_not_execution_authority: boolean;
    status_is_not_recovery_authority: boolean;
    raw_execution_evidence_not_exposed: boolean;
    browser_cannot_select_execution_repository: boolean;
  };
};

function paidExecutionStatusRecord(
  value: unknown
): value is Record<string, unknown> {
  return (
    typeof value === "object" &&
    value !== null &&
    !Array.isArray(value)
  );
}

function paidExecutionStatusString(
  value: unknown,
  field: string
): string {
  if (
    typeof value !== "string" ||
    value.length === 0
  ) {
    throw new Error(
      `Paid execution status ${field} is invalid`
    );
  }

  return value;
}

function paidExecutionStatusNumber(
  value: unknown,
  field: string
): number {
  if (
    typeof value !== "number" ||
    !Number.isInteger(value) ||
    value < 0
  ) {
    throw new Error(
      `Paid execution status ${field} is invalid`
    );
  }

  return value;
}

function paidExecutionDisposition(
  value: unknown
): CommercialPaidAssessmentDisposition {
  if (
    value !== "executed" &&
    value !== "resumed" &&
    value !== "reconciled"
  ) {
    throw new Error(
      "Paid execution status disposition is invalid"
    );
  }

  return value;
}

export async function fetchPaidAssessmentExecutionStatus(
  config: GovernanceAssessmentApiConfig,
  identity: GovernanceAssessmentIdentity,
  signal?: AbortSignal
): Promise<CommercialPaidAssessmentExecutionStatusResponse> {
  const hierarchySegments = [
    identity.tenantId,
    identity.clientId,
    identity.engagementId,
    identity.assessmentId
  ];

  const expectedHierarchy =
    hierarchySegments.join("/");

  const encodedSegments =
    hierarchySegments.map(
      encodeURIComponent
    );

  const url = new URL(
    (
      "/api/v1/governance-paid-assessments/"
      + encodedSegments.join("/")
      + "/execution-status"
    ),
    config.baseUrl
  );

  const response = await fetch(
    url,
    {
      method: "GET",
      headers: assessmentHeaders(config),
      cache: "no-store",
      signal
    }
  );

  const payload =
    await readAssessmentResponse<
      Record<string, unknown>
    >(
      response,
      "Paid assessment execution status request"
    );

  if (
    typeof payload.found !== "boolean"
  ) {
    throw new Error(
      "Paid execution status found flag is invalid"
    );
  }

  const hierarchyKey =
    paidExecutionStatusString(
      payload.hierarchy_key,
      "hierarchy_key"
    );

  if (
    hierarchyKey !== expectedHierarchy
  ) {
    throw new Error(
      "Paid execution status hierarchy mismatch"
    );
  }

  if (
    !paidExecutionStatusRecord(
      payload.boundaries
    )
  ) {
    throw new Error(
      "Paid execution status boundaries are invalid"
    );
  }

  const boundaries =
    payload.boundaries;

  const requiredBoundaries = [
    "status_is_read_only",
    "status_is_not_execution_authority",
    "status_is_not_recovery_authority",
    "raw_execution_evidence_not_exposed",
    "browser_cannot_select_execution_repository"
  ] as const;

  for (
    const boundary
    of requiredBoundaries
  ) {
    if (
      boundaries[boundary] !== true
    ) {
      throw new Error(
        `Paid execution status boundary ${boundary} is invalid`
      );
    }
  }

  const validatedBoundaries = {
    status_is_read_only: true,
    status_is_not_execution_authority: true,
    status_is_not_recovery_authority: true,
    raw_execution_evidence_not_exposed: true,
    browser_cannot_select_execution_repository: true
  };

  if (
    payload.found === false
  ) {
    if (
      payload.status !== null
    ) {
      throw new Error(
        "Missing paid execution status must return null status"
      );
    }

    return {
      found: false,
      hierarchy_key: hierarchyKey,
      status: null,
      boundaries: validatedBoundaries
    };
  }

  if (
    !paidExecutionStatusRecord(
      payload.status
    )
  ) {
    throw new Error(
      "Paid execution status payload is invalid"
    );
  }

  const statusPayload =
    payload.status;

  const artifactCountBefore =
    paidExecutionStatusNumber(
      statusPayload.artifact_count_before,
      "artifact_count_before"
    );

  const artifactCountAfter =
    paidExecutionStatusNumber(
      statusPayload.artifact_count_after,
      "artifact_count_after"
    );

  if (
    artifactCountAfter <
    artifactCountBefore
  ) {
    throw new Error(
      "Paid execution status artifact count regressed"
    );
  }

  const statusMetadata:
    CommercialPaidAssessmentExecutionStatusMetadata = {
      disposition:
        paidExecutionDisposition(
          statusPayload.disposition
        ),

      artifact_count_before:
        artifactCountBefore,

      artifact_count_after:
        artifactCountAfter,

      attempt_hash:
        paidExecutionStatusString(
          statusPayload.attempt_hash,
          "attempt_hash"
        ),

      attempt_record_hash:
        paidExecutionStatusString(
          statusPayload.attempt_record_hash,
          "attempt_record_hash"
        ),

      assessment_execution_request_hash:
        paidExecutionStatusString(
          statusPayload
            .assessment_execution_request_hash,
          "assessment_execution_request_hash"
        ),

      execution_input_binding_hash:
        paidExecutionStatusString(
          statusPayload
            .execution_input_binding_hash,
          "execution_input_binding_hash"
        ),

      status_recorded_at:
        paidExecutionStatusString(
          statusPayload.status_recorded_at,
          "status_recorded_at"
        ),

      schema_version:
        paidExecutionStatusString(
          statusPayload.schema_version,
          "schema_version"
        )
    };

  return {
    found: true,
    hierarchy_key: hierarchyKey,
    status: statusMetadata,
    boundaries: validatedBoundaries
  };
}

export type CommercialPaidAssessmentResultsInventoryItem = {
  artifact_id: string;
  artifact_type: string;
  artifact_hash: string;
  sequence_number: number;
  chain_hash: string;
  schema_version: string;
};

export type CommercialPaidAssessmentResultArtifact = {
  artifact_id: string;
  artifact_type: string;
  artifact_hash: string;
  payload: Record<string, unknown>;
  created_at: string;
  sequence_number: number;
  previous_artifact_hash: string | null;
  chain_hash: string;
  schema_version: string;
};

export type CommercialPaidAssessmentResultsResponse = {
  read_model_type: string;
  version: string;
  schema_version: string;
  tenant_id: string;
  client_id: string;
  engagement_id: string;
  assessment_id: string;
  assessment_name: string;
  hierarchy_key: string;
  execution_disposition:
    CommercialPaidAssessmentDisposition;
  execution_status_hash: string;
  execution_input_binding_hash: string;
  assessment_execution_request_hash: string;
  artifact_count: number;
  repository_chain_valid: true;
  artifact_inventory:
    CommercialPaidAssessmentResultsInventoryItem[];
  result_artifacts:
    CommercialPaidAssessmentResultArtifact[];
  boundaries: {
    read_model_is_read_only: true;
    read_model_is_not_execution_authority: true;
    read_model_is_not_recovery_authority: true;
    read_model_is_not_delivery_approval: true;
    repository_path_not_exposed: true;
    raw_evidence_payloads_not_exposed: true;
    evidence_intake_payload_not_exposed: true;
    scope_configuration_payload_not_exposed: true;
    result_payloads_are_canonical_paid_artifacts: true;
  };
};

const PAID_RESULT_ARTIFACT_TYPES = [
  "evidence-quality",
  "friction-summary",
  "governance-debt-score",
  "intervention-plan",
  "assessment-roadmap",
  "executive-projection",
  "client-report-package",
  "demonstration-manifest"
] as const;

const PAID_ARTIFACT_INVENTORY_TYPES = [
  "scope-configuration",
  "evidence-intake-batch",
  ...PAID_RESULT_ARTIFACT_TYPES
] as const;

function paidResultsRecord(
  value: unknown
): value is Record<string, unknown> {
  return (
    typeof value === "object" &&
    value !== null &&
    !Array.isArray(value)
  );
}

function paidResultsString(
  value: unknown,
  field: string
): string {
  if (
    typeof value !== "string" ||
    value.length === 0
  ) {
    throw new Error(
      `Paid results ${field} is invalid`
    );
  }

  return value;
}

function paidResultsInteger(
  value: unknown,
  field: string
): number {
  if (
    typeof value !== "number" ||
    !Number.isInteger(value) ||
    value < 0
  ) {
    throw new Error(
      `Paid results ${field} is invalid`
    );
  }

  return value;
}

function paidResultsDisposition(
  value: unknown
): CommercialPaidAssessmentDisposition {
  if (
    value !== "executed" &&
    value !== "resumed" &&
    value !== "reconciled"
  ) {
    throw new Error(
      "Paid results execution disposition is invalid"
    );
  }

  return value;
}

export async function fetchPaidAssessmentResults(
  config: GovernanceAssessmentApiConfig,
  identity: GovernanceAssessmentIdentity,
  signal?: AbortSignal
): Promise<CommercialPaidAssessmentResultsResponse> {
  const hierarchySegments = [
    identity.tenantId,
    identity.clientId,
    identity.engagementId,
    identity.assessmentId
  ];

  const expectedHierarchy =
    hierarchySegments.join("/");

  const url = new URL(
    (
      "/api/v1/governance-paid-assessments/"
      + hierarchySegments
        .map(encodeURIComponent)
        .join("/")
      + "/results"
    ),
    config.baseUrl
  );

  const response = await fetch(
    url,
    {
      method: "GET",
      headers: assessmentHeaders(config),
      cache: "no-store",
      signal
    }
  );

  const payload =
    await readAssessmentResponse<
      Record<string, unknown>
    >(
      response,
      "Paid assessment results request"
    );

  const hierarchyKey =
    paidResultsString(
      payload.hierarchy_key,
      "hierarchy_key"
    );

  if (
    hierarchyKey !== expectedHierarchy
  ) {
    throw new Error(
      "Paid results hierarchy mismatch"
    );
  }

  if (
    payload.tenant_id !==
      identity.tenantId ||
    payload.client_id !==
      identity.clientId ||
    payload.engagement_id !==
      identity.engagementId ||
    payload.assessment_id !==
      identity.assessmentId
  ) {
    throw new Error(
      "Paid results hierarchy fields mismatch"
    );
  }

  if (
    payload.repository_chain_valid !== true
  ) {
    throw new Error(
      "Paid results repository chain is not valid"
    );
  }

  const artifactCount =
    paidResultsInteger(
      payload.artifact_count,
      "artifact_count"
    );

  if (
    artifactCount !== 10
  ) {
    throw new Error(
      "Paid results artifact count is invalid"
    );
  }

  if (
    !Array.isArray(
      payload.artifact_inventory
    ) ||
    payload.artifact_inventory.length
      !== 10
  ) {
    throw new Error(
      "Paid results artifact inventory is invalid"
    );
  }

  const inventory =
    payload.artifact_inventory.map(
      (item, index) => {
        if (
          !paidResultsRecord(item)
        ) {
          throw new Error(
            "Paid results inventory item is invalid"
          );
        }

        const artifactType =
          paidResultsString(
            item.artifact_type,
            "artifact_inventory.artifact_type"
          );

        if (
          artifactType !==
          PAID_ARTIFACT_INVENTORY_TYPES[
            index
          ]
        ) {
          throw new Error(
            "Paid results artifact inventory order is invalid"
          );
        }

        const sequenceNumber =
          paidResultsInteger(
            item.sequence_number,
            "artifact_inventory.sequence_number"
          );

        if (
          sequenceNumber !==
          index + 1
        ) {
          throw new Error(
            "Paid results artifact sequence is invalid"
          );
        }

        return {
          artifact_id:
            paidResultsString(
              item.artifact_id,
              "artifact_inventory.artifact_id"
            ),
          artifact_type:
            artifactType,
          artifact_hash:
            paidResultsString(
              item.artifact_hash,
              "artifact_inventory.artifact_hash"
            ),
          sequence_number:
            sequenceNumber,
          chain_hash:
            paidResultsString(
              item.chain_hash,
              "artifact_inventory.chain_hash"
            ),
          schema_version:
            paidResultsString(
              item.schema_version,
              "artifact_inventory.schema_version"
            )
        };
      }
    );

  if (
    !Array.isArray(
      payload.result_artifacts
    ) ||
    payload.result_artifacts.length
      !==
      PAID_RESULT_ARTIFACT_TYPES.length
  ) {
    throw new Error(
      "Paid results artifact projection is invalid"
    );
  }

  const resultArtifacts =
    payload.result_artifacts.map(
      (item, index) => {
        if (
          !paidResultsRecord(item)
        ) {
          throw new Error(
            "Paid result artifact is invalid"
          );
        }

        const artifactType =
          paidResultsString(
            item.artifact_type,
            "result_artifacts.artifact_type"
          );

        if (
          artifactType !==
          PAID_RESULT_ARTIFACT_TYPES[
            index
          ]
        ) {
          throw new Error(
            "Paid result artifact order is invalid"
          );
        }

        if (
          !paidResultsRecord(
            item.payload
          )
        ) {
          throw new Error(
            "Paid result artifact payload is invalid"
          );
        }

        const previousArtifactHash =
          item.previous_artifact_hash;

        if (
          previousArtifactHash !== null &&
          (
            typeof previousArtifactHash
              !== "string" ||
            previousArtifactHash.length
              === 0
          )
        ) {
          throw new Error(
            "Paid result previous artifact hash is invalid"
          );
        }

        return {
          artifact_id:
            paidResultsString(
              item.artifact_id,
              "result_artifacts.artifact_id"
            ),
          artifact_type:
            artifactType,
          artifact_hash:
            paidResultsString(
              item.artifact_hash,
              "result_artifacts.artifact_hash"
            ),
          payload:
            item.payload,
          created_at:
            paidResultsString(
              item.created_at,
              "result_artifacts.created_at"
            ),
          sequence_number:
            paidResultsInteger(
              item.sequence_number,
              "result_artifacts.sequence_number"
            ),
          previous_artifact_hash:
            previousArtifactHash,
          chain_hash:
            paidResultsString(
              item.chain_hash,
              "result_artifacts.chain_hash"
            ),
          schema_version:
            paidResultsString(
              item.schema_version,
              "result_artifacts.schema_version"
            )
        };
      }
    );

  if (
    !paidResultsRecord(
      payload.boundaries
    )
  ) {
    throw new Error(
      "Paid results boundaries are invalid"
    );
  }

  const requiredBoundaries = [
    "read_model_is_read_only",
    "read_model_is_not_execution_authority",
    "read_model_is_not_recovery_authority",
    "read_model_is_not_delivery_approval",
    "repository_path_not_exposed",
    "raw_evidence_payloads_not_exposed",
    "evidence_intake_payload_not_exposed",
    "scope_configuration_payload_not_exposed",
    "result_payloads_are_canonical_paid_artifacts"
  ] as const;

  for (
    const boundary
    of requiredBoundaries
  ) {
    if (
      payload.boundaries[
        boundary
      ] !== true
    ) {
      throw new Error(
        `Paid results boundary ${boundary} is invalid`
      );
    }
  }

  return {
    read_model_type:
      paidResultsString(
        payload.read_model_type,
        "read_model_type"
      ),
    version:
      paidResultsString(
        payload.version,
        "version"
      ),
    schema_version:
      paidResultsString(
        payload.schema_version,
        "schema_version"
      ),
    tenant_id:
      identity.tenantId,
    client_id:
      identity.clientId,
    engagement_id:
      identity.engagementId,
    assessment_id:
      identity.assessmentId,
    assessment_name:
      paidResultsString(
        payload.assessment_name,
        "assessment_name"
      ),
    hierarchy_key:
      hierarchyKey,
    execution_disposition:
      paidResultsDisposition(
        payload.execution_disposition
      ),
    execution_status_hash:
      paidResultsString(
        payload.execution_status_hash,
        "execution_status_hash"
      ),
    execution_input_binding_hash:
      paidResultsString(
        payload.execution_input_binding_hash,
        "execution_input_binding_hash"
      ),
    assessment_execution_request_hash:
      paidResultsString(
        payload.assessment_execution_request_hash,
        "assessment_execution_request_hash"
      ),
    artifact_count:
      artifactCount,
    repository_chain_valid:
      true,
    artifact_inventory:
      inventory,
    result_artifacts:
      resultArtifacts,
    boundaries: {
      read_model_is_read_only: true,
      read_model_is_not_execution_authority: true,
      read_model_is_not_recovery_authority: true,
      read_model_is_not_delivery_approval: true,
      repository_path_not_exposed: true,
      raw_evidence_payloads_not_exposed: true,
      evidence_intake_payload_not_exposed: true,
      scope_configuration_payload_not_exposed: true,
      result_payloads_are_canonical_paid_artifacts: true
    }
  };
}

