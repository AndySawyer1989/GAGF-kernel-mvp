import {
  fetchActiveSigningKey,
  GovernanceAssessmentApiError,
  type GovernanceAssessmentApiConfig,
  type GovernanceAssessmentSigningKey
} from "./governance-assessment-api";

export type SigningCapabilityStatus =
  | "loading"
  | "available"
  | "unconfigured"
  | "unauthorized"
  | "unreachable"
  | "error";

export type SigningCapability = {
  status: SigningCapabilityStatus;
  available: boolean;
  title: string;
  message: string;
  activeKey: GovernanceAssessmentSigningKey | null;
  statusCode: number | null;
  reasonCode: string | null;
};

type ErrorPayloadDetail = {
  code?: unknown;
  message?: unknown;
};

function readPayloadDetail(
  payload: unknown
): ErrorPayloadDetail | null {
  if (
    typeof payload !== "object" ||
    payload === null
  ) {
    return null;
  }

  const record =
    payload as Record<string, unknown>;

  const detail = record.detail;

  if (
    typeof detail === "object" &&
    detail !== null
  ) {
    return detail as ErrorPayloadDetail;
  }

  return record as ErrorPayloadDetail;
}

function readReasonCode(
  payload: unknown
): string | null {
  const detail =
    readPayloadDetail(payload);

  return typeof detail?.code === "string"
    ? detail.code
    : null;
}

function readServerMessage(
  payload: unknown
): string | null {
  const detail =
    readPayloadDetail(payload);

  return typeof detail?.message === "string"
    ? detail.message
    : null;
}

function isUnconfiguredReason(
  reasonCode: string | null
): boolean {
  if (!reasonCode) {
    return false;
  }

  const normalized =
    reasonCode.toUpperCase();

  return (
    normalized.includes("SIGNING") &&
    (
      normalized.includes("UNAVAILABLE") ||
      normalized.includes("UNCONFIGURED") ||
      normalized.includes("NOT_CONFIGURED") ||
      normalized.includes("KEY_NOT_FOUND") ||
      normalized.includes("NO_ACTIVE_KEY")
    )
  );
}

export function loadingSigningCapability():
  SigningCapability {
  return {
    status: "loading",
    available: false,
    title: "Checking signing capability",
    message:
      "The Console is checking whether durable checkpoint signing is available.",
    activeKey: null,
    statusCode: null,
    reasonCode: null
  };
}

export function availableSigningCapability(
  activeKey: GovernanceAssessmentSigningKey
): SigningCapability {
  return {
    status: "available",
    available: true,
    title: "Durable signing available",
    message:
      `Checkpoint signing is available through active key ${activeKey.key_id}.`,
    activeKey,
    statusCode: 200,
    reasonCode: null
  };
}

export function classifySigningCapabilityError(
  caught: unknown
): SigningCapability {
  if (
    caught instanceof DOMException &&
    caught.name === "AbortError"
  ) {
    throw caught;
  }

  if (
    caught instanceof GovernanceAssessmentApiError
  ) {
    const reasonCode =
      readReasonCode(caught.payload);

    const serverMessage =
      readServerMessage(caught.payload);

    if (
      caught.status === 401 ||
      caught.status === 403
    ) {
      return {
        status: "unauthorized",
        available: false,
        title: "Signing access denied",
        message:
          serverMessage ??
          "Your current operator identity is not authorized to inspect or use the active signing key.",
        activeKey: null,
        statusCode: caught.status,
        reasonCode
      };
    }

    if (
      caught.status === 404 ||
      caught.status === 503 ||
      isUnconfiguredReason(reasonCode)
    ) {
      return {
        status: "unconfigured",
        available: false,
        title: "Durable signing is not configured",
        message:
          serverMessage ??
          "No active durable signing key is available for this tenant. Read-only audit evidence remains available.",
        activeKey: null,
        statusCode: caught.status,
        reasonCode
      };
    }

    return {
      status: "error",
      available: false,
      title: "Signing capability check failed",
      message:
        serverMessage ??
        `The backend returned status ${caught.status} while checking durable signing capability.`,
      activeKey: null,
      statusCode: caught.status,
      reasonCode
    };
  }

  if (
    caught instanceof TypeError
  ) {
    return {
      status: "unreachable",
      available: false,
      title: "Signing service is unreachable",
      message:
        "The Console could not reach the backend while checking durable signing capability.",
      activeKey: null,
      statusCode: null,
      reasonCode: null
    };
  }

  return {
    status: "error",
    available: false,
    title: "Signing capability is unknown",
    message:
      "An unexpected error prevented the Console from determining whether durable signing is available.",
    activeKey: null,
    statusCode: null,
    reasonCode: null
  };
}

export async function detectSigningCapability(
  config: GovernanceAssessmentApiConfig,
  signal?: AbortSignal
): Promise<SigningCapability> {
  try {
    const activeKey =
      await fetchActiveSigningKey(
        config,
        signal
      );

    return availableSigningCapability(
      activeKey
    );
  } catch (caught) {
    return classifySigningCapabilityError(
      caught
    );
  }
}
