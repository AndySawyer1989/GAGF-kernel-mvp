export type CustomerTrialApiConfig = {
  baseUrl: string;
  tenantId: string;
  actorId: string;
  actorRoles: string;
};


export type CustomerTrialHierarchy = {
  tenantId: string;
  clientId: string;
  engagementId: string;
  assessmentId: string;
};


export type CustomerTrialPreflightReceipt = {
  hierarchy_key?: string;
  package_hash?: string;
  decision_payload_hash?: string;
  receipt_hash?: string;
  [key: string]: unknown;
};


export type CustomerTrialPreflightStatus = {
  status: string;
  api_version: string;
  authority: "READ_ONLY";

  result: {
    receipt_found: boolean;
    receipt:
      | CustomerTrialPreflightReceipt
      | null;

    [key: string]: unknown;
  };

  boundaries?:
    Record<string, boolean>;
};


export type CustomerTrialExecutionHandoffReceipt = {
  hierarchy_key?: string;

  preflight_receipt_hash?: string;
  preflight_decision_payload_hash?: string;
  preflight_package_hash?: string;

  lineage_hash?: string;
  receipt_hash?: string;

  execution_handoff_lineage?: {
    contract_execution_event_hash?: string;
    paid_work_authorization_hash?: string;
    assessment_execution_request_hash?: string;
    handoff_hash?: string;

    [key: string]: unknown;
  };

  [key: string]: unknown;
};


export type CustomerTrialExecutionHandoffStatus = {
  status: string;
  api_version: string;
  authority: "READ_ONLY";

  result: {
    receipt_found: boolean;

    receipt:
      | CustomerTrialExecutionHandoffReceipt
      | null;

    [key: string]: unknown;
  };

  boundaries: {
    status_is_read_only: boolean;

    status_is_not_execution_authority:
      boolean;

    status_is_not_recovery_authority:
      boolean;

    status_is_not_delivery_authority:
      boolean;

    status_is_not_closeout_authority:
      boolean;

    status_is_not_intervention_authority:
      boolean;
  };
};


export type CustomerTrialContractExecutionEvent = {
  contract_execution_event_id: string;

  contract_executed: boolean;

  contract_execution_review_ready:
    boolean;

  contract_execution_confirmed:
    boolean;

  executed_contract_reference_recorded:
    boolean;

  executed_at_recorded:
    boolean;

  all_required_signatures_recorded:
    boolean;

  human_operator_confirmed_execution:
    boolean;

  requires_final_paid_work_authorization:
    boolean;

  human_boundary_required:
    boolean;

  gagf_kernel_authoritative:
    boolean;

  ai_override_allowed:
    boolean;
};


export type CustomerTrialPaidWorkAuthorization = {
  authorization_id: string;

  tenant_id: string;
  client_id: string;
  engagement_id: string;
  assessment_id: string;

  contract_execution_event_id: string;

  authorized_by: string;
  authorized_at: string;

  paid_assessment_authorized:
    boolean;
};


export type CustomerTrialExecutionHandoffRequest = {
  tenant_id: string;
  client_id: string;
  engagement_id: string;
  assessment_id: string;

  execution_input_binding_hash:
    string;

  contract_execution_event:
    CustomerTrialContractExecutionEvent;

  paid_work_authorization:
    CustomerTrialPaidWorkAuthorization;
};


export type CustomerTrialExecutionHandoffPreparationResponse = {
  status: string;
  api_version: string;

  authority:
    "HANDOFF_PREPARATION_ONLY";

  binding_metadata:
    Record<string, unknown>;

  result:
    Record<string, unknown>;

  boundaries:
    Record<string, boolean>;
};


export class GovernanceCustomerTrialApiError
  extends Error {
  constructor(
    message: string
  ) {
    super(message);

    this.name =
      "GovernanceCustomerTrialApiError";
  }
}


function headers(
  config:
    CustomerTrialApiConfig
): Record<string, string> {
  return {
    "X-Tenant-ID":
      config.tenantId,

    "X-Actor-ID":
      config.actorId,

    "X-Actor-Roles":
      config.actorRoles
  };
}


function hierarchyPath(
  hierarchy:
    CustomerTrialHierarchy
): string {
  return [
    hierarchy.tenantId,
    hierarchy.clientId,
    hierarchy.engagementId,
    hierarchy.assessmentId
  ]
    .map(
      encodeURIComponent
    )
    .join("/");
}


function objectValue(
  value: unknown,
  name: string
): Record<string, unknown> {
  if (
    typeof value !== "object" ||
    value === null ||
    Array.isArray(value)
  ) {
    throw new GovernanceCustomerTrialApiError(
      `Invalid ${name} response.`
    );
  }

  return value as Record<
    string,
    unknown
  >;
}


function stringValue(
  payload:
    Record<string, unknown>,
  key: string
): string {
  const value =
    payload[key];

  if (
    typeof value !== "string"
  ) {
    throw new GovernanceCustomerTrialApiError(
      `Invalid ${key} response value.`
    );
  }

  return value;
}


function booleanValue(
  payload:
    Record<string, unknown>,
  key: string
): boolean {
  const value =
    payload[key];

  if (
    typeof value !== "boolean"
  ) {
    throw new GovernanceCustomerTrialApiError(
      `Invalid ${key} response value.`
    );
  }

  return value;
}


async function responsePayload(
  response: Response,
  failureMessage: string
): Promise<
  Record<string, unknown>
> {
  let payload: unknown;

  try {
    payload =
      await response.json();
  } catch {
    throw new GovernanceCustomerTrialApiError(
      (
        `${failureMessage}: ` +
        "invalid JSON response."
      )
    );
  }

  if (
    !response.ok
  ) {
    const body =
      objectValue(
        payload,
        "customer-trial error"
      );

    const detail =
      typeof body.detail === "object" &&
      body.detail !== null
        ? (
            body.detail as
              Record<
                string,
                unknown
              >
          )
        : null;

    const message =
      detail &&
      typeof detail.message === "string"
        ? detail.message
        : failureMessage;

    throw new GovernanceCustomerTrialApiError(
      message
    );
  }

  return objectValue(
    payload,
    "customer-trial"
  );
}


function parsePreflightStatus(
  payload:
    Record<string, unknown>
): CustomerTrialPreflightStatus {
  const authority =
    stringValue(
      payload,
      "authority"
    );

  if (
    authority !==
    "READ_ONLY"
  ) {
    throw new GovernanceCustomerTrialApiError(
      (
        "Customer-trial preflight "
        + "status is not read-only."
      )
    );
  }

  const result =
    objectValue(
      payload.result,
      "preflight result"
    );

  const receiptFound =
    booleanValue(
      result,
      "receipt_found"
    );

  const rawReceipt =
    result.receipt;

  let receipt:
    | CustomerTrialPreflightReceipt
    | null = null;

  if (
    receiptFound
  ) {
    receipt =
      objectValue(
        rawReceipt,
        "preflight receipt"
      );
  } else if (
    rawReceipt !== null
  ) {
    throw new GovernanceCustomerTrialApiError(
      (
        "Preflight receipt must "
        + "be null when not found."
      )
    );
  }

  return {
    status:
      stringValue(
        payload,
        "status"
      ),

    api_version:
      stringValue(
        payload,
        "api_version"
      ),

    authority:
      "READ_ONLY",

    result: {
      ...result,

      receipt_found:
        receiptFound,

      receipt
    },

    boundaries:
      typeof payload.boundaries ===
        "object" &&
      payload.boundaries !== null
        ? (
            payload.boundaries as
              Record<
                string,
                boolean
              >
          )
        : undefined
  };
}


function parseExecutionHandoffStatus(
  payload:
    Record<string, unknown>
): CustomerTrialExecutionHandoffStatus {
  const authority =
    stringValue(
      payload,
      "authority"
    );

  if (
    authority !==
    "READ_ONLY"
  ) {
    throw new GovernanceCustomerTrialApiError(
      (
        "Customer-trial execution "
        + "handoff status is not "
        + "read-only."
      )
    );
  }

  const result =
    objectValue(
      payload.result,
      "execution handoff result"
    );

  const receiptFound =
    booleanValue(
      result,
      "receipt_found"
    );

  const rawReceipt =
    result.receipt;

  let receipt:
    | CustomerTrialExecutionHandoffReceipt
    | null = null;

  if (
    receiptFound
  ) {
    receipt =
      objectValue(
        rawReceipt,
        "execution handoff receipt"
      );
  } else if (
    rawReceipt !== null
  ) {
    throw new GovernanceCustomerTrialApiError(
      (
        "Execution handoff receipt "
        + "must be null when not found."
      )
    );
  }

  const boundaries =
    objectValue(
      payload.boundaries,
      "execution handoff boundaries"
    );

  return {
    status:
      stringValue(
        payload,
        "status"
      ),

    api_version:
      stringValue(
        payload,
        "api_version"
      ),

    authority:
      "READ_ONLY",

    result: {
      ...result,

      receipt_found:
        receiptFound,

      receipt
    },

    boundaries: {
      status_is_read_only:
        booleanValue(
          boundaries,
          "status_is_read_only"
        ),

      status_is_not_execution_authority:
        booleanValue(
          boundaries,
          (
            "status_is_not_"
            + "execution_authority"
          )
        ),

      status_is_not_recovery_authority:
        booleanValue(
          boundaries,
          (
            "status_is_not_"
            + "recovery_authority"
          )
        ),

      status_is_not_delivery_authority:
        booleanValue(
          boundaries,
          (
            "status_is_not_"
            + "delivery_authority"
          )
        ),

      status_is_not_closeout_authority:
        booleanValue(
          boundaries,
          (
            "status_is_not_"
            + "closeout_authority"
          )
        ),

      status_is_not_intervention_authority:
        booleanValue(
          boundaries,
          (
            "status_is_not_"
            + "intervention_authority"
          )
        )
    }
  };
}


function parseExecutionHandoffPreparation(
  payload:
    Record<string, unknown>
): CustomerTrialExecutionHandoffPreparationResponse {
  const authority =
    stringValue(
      payload,
      "authority"
    );

  if (
    authority !==
    "HANDOFF_PREPARATION_ONLY"
  ) {
    throw new GovernanceCustomerTrialApiError(
      (
        "Customer-trial handoff "
        + "response claimed "
        + "unexpected authority."
      )
    );
  }

  return {
    status:
      stringValue(
        payload,
        "status"
      ),

    api_version:
      stringValue(
        payload,
        "api_version"
      ),

    authority:
      "HANDOFF_PREPARATION_ONLY",

    binding_metadata:
      objectValue(
        payload.binding_metadata,
        (
          "execution handoff "
          + "binding metadata"
        )
      ),

    result:
      objectValue(
        payload.result,
        (
          "execution handoff "
          + "preparation result"
        )
      ),

    boundaries:
      objectValue(
        payload.boundaries,
        (
          "execution handoff "
          + "preparation boundaries"
        )
      ) as Record<
        string,
        boolean
      >
  };
}


export async function
fetchCustomerTrialPreflightStatus(
  config:
    CustomerTrialApiConfig,
  hierarchy:
    CustomerTrialHierarchy,
  signal?:
    AbortSignal
): Promise<
  CustomerTrialPreflightStatus
> {
  const url =
    new URL(
      (
        "/api/v1/"
        + "governance-customer-trials/"
        + hierarchyPath(
          hierarchy
        )
        + "/preflight-status"
      ),
      config.baseUrl
    );

  const response =
    await fetch(
      url,
      {
        method:
          "GET",

        headers:
          headers(
            config
          ),

        cache:
          "no-store",

        signal
      }
    );

  return parsePreflightStatus(
    await responsePayload(
      response,
      (
        "Unable to restore "
        + "customer-trial "
        + "preflight status"
      )
    )
  );
}


export async function
fetchCustomerTrialExecutionHandoffStatus(
  config:
    CustomerTrialApiConfig,
  hierarchy:
    CustomerTrialHierarchy,
  signal?:
    AbortSignal
): Promise<
  CustomerTrialExecutionHandoffStatus
> {
  const url =
    new URL(
      (
        "/api/v1/"
        + "governance-customer-trials/"
        + hierarchyPath(
          hierarchy
        )
        + "/execution-handoff-status"
      ),
      config.baseUrl
    );

  const response =
    await fetch(
      url,
      {
        method:
          "GET",

        headers:
          headers(
            config
          ),

        cache:
          "no-store",

        signal
      }
    );

  return parseExecutionHandoffStatus(
    await responsePayload(
      response,
      (
        "Unable to restore "
        + "customer-trial "
        + "execution handoff status"
      )
    )
  );
}


export async function
prepareCustomerTrialExecutionHandoff(
  config:
    CustomerTrialApiConfig,
  request:
    CustomerTrialExecutionHandoffRequest,
  signal?:
    AbortSignal
): Promise<
  CustomerTrialExecutionHandoffPreparationResponse
> {
  const url =
    new URL(
      (
        "/api/v1/"
        + "governance-customer-trials/"
        + "execution-handoff"
      ),
      config.baseUrl
    );

  const response =
    await fetch(
      url,
      {
        method:
          "POST",

        headers: {
          ...headers(
            config
          ),

          "Content-Type":
            "application/json"
        },

        cache:
          "no-store",

        body:
          JSON.stringify(
            request
          ),

        signal
      }
    );

  return parseExecutionHandoffPreparation(
    await responsePayload(
      response,
      (
        "Unable to prepare "
        + "customer-trial "
        + "execution handoff"
      )
    )
  );
}