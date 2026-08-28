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

