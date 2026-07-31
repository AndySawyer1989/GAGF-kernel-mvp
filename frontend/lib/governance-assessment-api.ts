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

export type GovernanceAssessmentListItem =
  Record<string, unknown>;

export type GovernanceAssessmentListResponse = {
  items: GovernanceAssessmentListItem[];
  count: number;
};

export type GovernanceAssessmentListFilters = {
  clientId?: string;
  engagementId?: string;
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
    !Array.isArray(
      (payload as GovernanceAssessmentListResponse).items
    ) ||
    typeof (
      payload as GovernanceAssessmentListResponse
    ).count !== "number"
  ) {
    throw new GovernanceAssessmentApiError(
      "Assessment list response did not match the expected contract",
      response.status,
      payload
    );
  }

  return payload as GovernanceAssessmentListResponse;
}
