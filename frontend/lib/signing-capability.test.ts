import {
  describe,
  expect,
  it
} from "vitest";

import {
  GovernanceAssessmentApiError,
  type GovernanceAssessmentSigningKey
} from "./governance-assessment-api";

import {
  availableSigningCapability,
  classifySigningCapabilityError,
  loadingSigningCapability
} from "./signing-capability";

const ACTIVE_KEY:
  GovernanceAssessmentSigningKey = {
    tenant_id: "tenant-alpha",
    key_id: "assessment-local-2026-01",
    secret_reference:
      "env://GAGF_ASSESSMENT_CHECKPOINT_SECRET",
    active: true,
    created_at:
      "2026-08-02T12:00:00Z",
    retired_at: null
  };

describe("signing capability", () => {
  it("represents the loading state", () => {
    const capability =
      loadingSigningCapability();

    expect(capability.status).toBe(
      "loading"
    );

    expect(capability.available).toBe(
      false
    );

    expect(capability.activeKey).toBeNull();
  });

  it("represents an available active key", () => {
    const capability =
      availableSigningCapability(
        ACTIVE_KEY
      );

    expect(capability.status).toBe(
      "available"
    );

    expect(capability.available).toBe(
      true
    );

    expect(
      capability.activeKey?.key_id
    ).toBe(
      "assessment-local-2026-01"
    );
  });

  it("classifies unauthorized access", () => {
    const capability =
      classifySigningCapabilityError(
        new GovernanceAssessmentApiError(
          "Forbidden",
          403,
          {
            detail: {
              code: "ACCESS_DENIED",
              message:
                "Operator cannot inspect signing keys."
            }
          }
        )
      );

    expect(capability.status).toBe(
      "unauthorized"
    );

    expect(capability.statusCode).toBe(
      403
    );

    expect(capability.reasonCode).toBe(
      "ACCESS_DENIED"
    );
  });

  it("classifies an absent active key as unconfigured", () => {
    const capability =
      classifySigningCapabilityError(
        new GovernanceAssessmentApiError(
          "No active key",
          404,
          {
            detail: {
              code:
                "CHECKPOINT_SIGNING_KEY_NOT_FOUND",
              message:
                "No active signing key exists."
            }
          }
        )
      );

    expect(capability.status).toBe(
      "unconfigured"
    );

    expect(capability.available).toBe(
      false
    );

    expect(capability.message).toBe(
      "No active signing key exists."
    );
  });

  it("classifies a temporarily unavailable signer as unconfigured", () => {
    const capability =
      classifySigningCapabilityError(
        new GovernanceAssessmentApiError(
          "Unavailable",
          503,
          {
            detail: {
              code:
                "CHECKPOINT_SIGNING_UNAVAILABLE"
            }
          }
        )
      );

    expect(capability.status).toBe(
      "unconfigured"
    );

    expect(capability.statusCode).toBe(
      503
    );
  });

  it("classifies network failure as unreachable", () => {
    const capability =
      classifySigningCapabilityError(
        new TypeError("Failed to fetch")
      );

    expect(capability.status).toBe(
      "unreachable"
    );

    expect(capability.statusCode).toBeNull();
  });

  it("classifies unexpected backend errors", () => {
    const capability =
      classifySigningCapabilityError(
        new GovernanceAssessmentApiError(
          "Server error",
          500,
          null
        )
      );

    expect(capability.status).toBe(
      "error"
    );

    expect(capability.statusCode).toBe(
      500
    );
  });

  it("classifies unknown errors", () => {
    const capability =
      classifySigningCapabilityError(
        new Error("Unexpected")
      );

    expect(capability.status).toBe(
      "error"
    );

    expect(capability.available).toBe(
      false
    );
  });

  it("preserves abort behavior", () => {
    expect(() =>
      classifySigningCapabilityError(
        new DOMException(
          "Request aborted",
          "AbortError"
        )
      )
    ).toThrow(
      expect.objectContaining({
        name: "AbortError"
      })
    );
  });
});
