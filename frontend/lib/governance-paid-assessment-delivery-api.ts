import {
  GovernanceAssessmentApiConfig,
  GovernanceAssessmentApiError
} from "./governance-assessment-api";

export type PaidAssessmentHierarchy = {
  tenantId: string;
  clientId: string;
  engagementId: string;
  assessmentId: string;
};

export type PaidAssessmentDeliveryReadinessResponse = {
  delivery_readiness_status: string;
  boundaries?: Record<string, boolean>;
};

export type PaidAssessmentDeliveryApprovalRequest = {
  approval_id: string;
  tenant_id: string;
  client_id: string;
  engagement_id: string;
  assessment_id: string;
  report_id: string;
  approved_by: string;
  approved_at: string;
  scope_approved: boolean;
  evidence_boundary_approved: boolean;
  buyer_language_approved: boolean;
  delivery_approved: boolean;
};

export type PaidAssessmentDeliveryApprovalResponse = {
  handoff_status: string;
  approved_for_human_delivery: boolean;
  boundaries?: Record<string, boolean>;
};

export type PaidAssessmentDeliveryRecordingRequest = {
  delivery_event_id: string;
  tenant_id: string;
  client_id: string;
  engagement_id: string;
  assessment_id: string;
  report_id: string;
  delivered_by: string;
  delivered_at: string;
  delivery_method: string;
  delivery_reference: string;
  delivery_completed: boolean;
};

export type PaidAssessmentDeliveryRecordingResponse = {
  delivery_status: string;
  delivery_recorded: boolean;
  boundaries?: Record<string, boolean>;
};

function assessmentHeaders(
  config: GovernanceAssessmentApiConfig,
  includeJson = false
): HeadersInit {
  return {
    ...(includeJson
      ? {
          "Content-Type": "application/json"
        }
      : {}),
    "X-Tenant-ID": config.tenantId,
    "X-Actor-ID": config.actorId,
    "X-Actor-Roles": config.actorRoles
  };
}

function buildDeliveryUrl(
  config: GovernanceAssessmentApiConfig,
  hierarchy: PaidAssessmentHierarchy,
  action:
    | "delivery-readiness"
    | "delivery-approval"
    | "delivery-recording"
): URL {
  const tenantId = encodeURIComponent(
    hierarchy.tenantId
  );
  const clientId = encodeURIComponent(
    hierarchy.clientId
  );
  const engagementId = encodeURIComponent(
    hierarchy.engagementId
  );
  const assessmentId = encodeURIComponent(
    hierarchy.assessmentId
  );

  return new URL(
    (
      "/api/v1/governance-paid-assessments/" +
      `${tenantId}/${clientId}/` +
      `${engagementId}/${assessmentId}/` +
      action
    ),
    config.baseUrl
  );
}

async function parseResponse<T>(
  response: Response,
  failureMessage: string
): Promise<T> {
  const payload: unknown = await response
    .json()
    .catch(() => null);

  if (!response.ok) {
    throw new GovernanceAssessmentApiError(
      `${failureMessage} with status ${response.status}`,
      response.status,
      payload
    );
  }

  return payload as T;
}

export async function fetchPaidAssessmentDeliveryReadiness(
  config: GovernanceAssessmentApiConfig,
  hierarchy: PaidAssessmentHierarchy,
  signal?: AbortSignal
): Promise<PaidAssessmentDeliveryReadinessResponse> {
  const response = await fetch(
    buildDeliveryUrl(
      config,
      hierarchy,
      "delivery-readiness"
    ),
    {
      method: "GET",
      headers: assessmentHeaders(config),
      cache: "no-store",
      signal
    }
  );

  return parseResponse<
    PaidAssessmentDeliveryReadinessResponse
  >(
    response,
    "Paid assessment delivery readiness request failed"
  );
}

export async function approvePaidAssessmentDelivery(
  config: GovernanceAssessmentApiConfig,
  hierarchy: PaidAssessmentHierarchy,
  request: PaidAssessmentDeliveryApprovalRequest,
  signal?: AbortSignal
): Promise<PaidAssessmentDeliveryApprovalResponse> {
  const response = await fetch(
    buildDeliveryUrl(
      config,
      hierarchy,
      "delivery-approval"
    ),
    {
      method: "POST",
      headers: assessmentHeaders(
        config,
        true
      ),
      body: JSON.stringify(request),
      cache: "no-store",
      signal
    }
  );

  return parseResponse<
    PaidAssessmentDeliveryApprovalResponse
  >(
    response,
    "Paid assessment delivery approval request failed"
  );
}

export async function recordPaidAssessmentDelivery(
  config: GovernanceAssessmentApiConfig,
  hierarchy: PaidAssessmentHierarchy,
  request: PaidAssessmentDeliveryRecordingRequest,
  signal?: AbortSignal
): Promise<PaidAssessmentDeliveryRecordingResponse> {
  const response = await fetch(
    buildDeliveryUrl(
      config,
      hierarchy,
      "delivery-recording"
    ),
    {
      method: "POST",
      headers: assessmentHeaders(
        config,
        true
      ),
      body: JSON.stringify(request),
      cache: "no-store",
      signal
    }
  );

  return parseResponse<
    PaidAssessmentDeliveryRecordingResponse
  >(
    response,
    "Paid assessment delivery recording request failed"
  );
}