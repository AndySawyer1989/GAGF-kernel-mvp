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
  report_id: string;
  boundaries?: Record<string, boolean>;
};

export type PaidAssessmentDeliveryStatusResponse = {
  found: boolean;
  delivery_recorded: boolean;
  delivery_status: string | null;
  report_id: string | null;
  delivered_by: string | null;
  delivered_at: string | null;
  delivery_method: string | null;
  delivery_reference: string | null;
  repository_chain_valid: boolean;
  boundaries?: Record<string, boolean>;
};

export type PaidAssessmentRecordedDeliveryProjection = {
  deliveredAt: string;
  deliveredBy: string;
};

export type PaidAssessmentLifecycleStatusResponse = {
  tenant_id: string;
  client_id: string;
  engagement_id: string;
  assessment_id: string;
  hierarchy_key: string;
  current_stage: string;
  pending_next_step: string | null;
  delivery_recorded: boolean;
  receipt_acknowledged: boolean;
  client_response_recorded: boolean;
  report_id: string | null;
  findings_disposition: string | null;
  recommendations_disposition: string | null;
  lifecycle_artifact_count: number;
  repository_chain_valid: boolean;
  boundaries?: Record<string, boolean>;
};

export type PaidAssessmentClientAcknowledgmentRequest = {
  acknowledgment_id: string;
  acknowledged_by: string;
  acknowledged_at: string;
  acknowledgment_method: string;
  acknowledgment_reference: string;
  client_acknowledged_receipt: boolean;
};

export type PaidAssessmentClientAcknowledgmentResponse = {
  acknowledgment_status: string;
  client_receipt_acknowledged: boolean;
  report_id: string;
  acknowledgment_id: string;
  acknowledged_by: string;
  acknowledged_at: string;
  acknowledgment_method: string;
  acknowledgment_reference: string;
  boundaries?: Record<string, boolean>;
};

export type PaidAssessmentClientResponseRequest = {
  response_id: string;
  responded_by: string;
  responded_at: string;
  response_method: string;
  response_reference: string;
  findings_disposition: string;
  recommendations_disposition: string;
  response_note: string;
};

export type PaidAssessmentClientResponseResponse = {
  response_status: string;
  client_response_recorded: boolean;
  report_id: string;
  response_id: string;
  responded_by: string;
  responded_at: string;
  response_method: string;
  response_reference: string;
  findings_disposition: string;
  recommendations_disposition: string;
  response_note: string;
  boundaries?: Record<string, boolean>;
};


export type PaidAssessmentCloseoutStatusResponse = {
  status_type: string;
  version: string;
  schema_version: string;
  tenant_id: string;
  client_id: string;
  engagement_id: string;
  assessment_id: string;
  hierarchy_key: string;
  found: boolean;
  closeout_recorded: boolean;
  closeout_status: string | null;
  report_id: string | null;
  closed_by: string | null;
  closed_at: string | null;
  closeout_reason: string | null;
  repository_chain_valid: boolean;
  boundaries?: Record<string, boolean>;
};

export type PaidAssessmentAdministrativeCloseoutRequest = {
  closed_by: string;
  closeout_reason: string;
  administrative_closeout_confirmed: boolean;
};

export type PaidAssessmentAdministrativeCloseoutResponse = {
  closeout_type: string;
  version: string;
  schema_version: string;
  tenant_id: string;
  client_id: string;
  engagement_id: string;
  assessment_id: string;
  hierarchy_key: string;
  report_id: string;
  closeout_status: string;
  administrative_closeout_recorded: boolean;
  closed_by: string;
  closeout_reason: string;
  closeout_artifact_id: string;
  closeout_artifact_hash: string;
  repository_chain_valid: boolean;
  boundaries?: Record<string, boolean>;
};

export function projectPaidAssessmentRecordedDelivery(
  status: PaidAssessmentDeliveryStatusResponse
): PaidAssessmentRecordedDeliveryProjection | null {
  if (
    !status.found ||
    !status.delivery_recorded ||
    status.delivery_status !== "delivered" ||
    status.repository_chain_valid !== true ||
    status.delivered_at === null ||
    status.delivered_by === null
  ) {
    return null;
  }

  return {
    deliveredAt: status.delivered_at,
    deliveredBy: status.delivered_by
  };
}

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
    | "delivery-status"
    | "delivery-readiness"
    | "delivery-approval"
    | "delivery-recording"
    | "lifecycle-status"
    | "client-acknowledgment"
    | "client-response"
    | "closeout-status"
    | "administrative-closeout"
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

export async function fetchPaidAssessmentDeliveryStatus(
  config: GovernanceAssessmentApiConfig,
  hierarchy: PaidAssessmentHierarchy,
  signal?: AbortSignal
): Promise<PaidAssessmentDeliveryStatusResponse> {
  const response = await fetch(
    buildDeliveryUrl(
      config,
      hierarchy,
      "delivery-status"
    ),
    {
      method: "GET",
      headers: assessmentHeaders(config),
      cache: "no-store",
      signal
    }
  );

  return parseResponse<PaidAssessmentDeliveryStatusResponse>(
    response,
    "Failed to fetch paid assessment delivery status"
  );
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

export async function fetchPaidAssessmentLifecycleStatus(
  config: GovernanceAssessmentApiConfig,
  hierarchy: PaidAssessmentHierarchy,
  signal?: AbortSignal
): Promise<PaidAssessmentLifecycleStatusResponse> {
  const response = await fetch(
    buildDeliveryUrl(
      config,
      hierarchy,
      "lifecycle-status"
    ),
    {
      method: "GET",
      headers: assessmentHeaders(config),
      cache: "no-store",
      signal
    }
  );

  return parseResponse<PaidAssessmentLifecycleStatusResponse>(
    response,
    "Failed to fetch paid assessment lifecycle status"
  );
}


export async function recordPaidAssessmentClientAcknowledgment(
  config: GovernanceAssessmentApiConfig,
  hierarchy: PaidAssessmentHierarchy,
  request: PaidAssessmentClientAcknowledgmentRequest,
  signal?: AbortSignal
): Promise<PaidAssessmentClientAcknowledgmentResponse> {
  const response = await fetch(
    buildDeliveryUrl(
      config,
      hierarchy,
      "client-acknowledgment"
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
    PaidAssessmentClientAcknowledgmentResponse
  >(
    response,
    "Paid assessment client acknowledgment request failed"
  );
}


export async function recordPaidAssessmentClientResponse(
  config: GovernanceAssessmentApiConfig,
  hierarchy: PaidAssessmentHierarchy,
  request: PaidAssessmentClientResponseRequest,
  signal?: AbortSignal
): Promise<PaidAssessmentClientResponseResponse> {
  const response = await fetch(
    buildDeliveryUrl(
      config,
      hierarchy,
      "client-response"
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
    PaidAssessmentClientResponseResponse
  >(
    response,
    "Paid assessment client response request failed"
  );
}


export async function fetchPaidAssessmentCloseoutStatus(
  config: GovernanceAssessmentApiConfig,
  hierarchy: PaidAssessmentHierarchy,
  signal?: AbortSignal
): Promise<PaidAssessmentCloseoutStatusResponse> {
  const response = await fetch(
    buildDeliveryUrl(
      config,
      hierarchy,
      "closeout-status"
    ),
    {
      method: "GET",
      headers: assessmentHeaders(config),
      cache: "no-store",
      signal
    }
  );

  return parseResponse<
    PaidAssessmentCloseoutStatusResponse
  >(
    response,
    "Failed to fetch paid assessment closeout status"
  );
}


export async function recordPaidAssessmentAdministrativeCloseout(
  config: GovernanceAssessmentApiConfig,
  hierarchy: PaidAssessmentHierarchy,
  request: PaidAssessmentAdministrativeCloseoutRequest,
  signal?: AbortSignal
): Promise<PaidAssessmentAdministrativeCloseoutResponse> {
  const response = await fetch(
    buildDeliveryUrl(
      config,
      hierarchy,
      "administrative-closeout"
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
    PaidAssessmentAdministrativeCloseoutResponse
  >(
    response,
    "Paid assessment administrative closeout request failed"
  );
}
