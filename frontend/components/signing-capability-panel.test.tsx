import {
  render,
  screen
} from "@testing-library/react";

import {
  describe,
  expect,
  it
} from "vitest";

import {
  SigningCapabilityPanel
} from "./signing-capability-panel";

import type {
  SigningCapability
} from "@/lib/signing-capability";

function capability(
  overrides:
    Partial<SigningCapability> = {}
): SigningCapability {
  return {
    status: "loading",
    available: false,
    title: "Checking signing capability",
    message:
      "The Console is checking signing availability.",
    activeKey: null,
    statusCode: null,
    reasonCode: null,
    ...overrides
  };
}

describe("SigningCapabilityPanel", () => {
  it("announces the loading state", () => {
    render(
      <SigningCapabilityPanel
        capability={capability()}
      />
    );

    expect(
      screen.getByText("Checking")
    ).toBeInTheDocument();

    expect(
      screen.getByText(
        "Checking signing capability"
      )
    ).toBeInTheDocument();
  });

  it("shows the active key when available", () => {
    render(
      <SigningCapabilityPanel
        capability={capability({
          status: "available",
          available: true,
          title:
            "Durable signing available",
          message:
            "Checkpoint signing is available.",
          statusCode: 200,
          activeKey: {
            tenant_id: "tenant-alpha",
            key_id:
              "assessment-local-2026-01",
            secret_reference:
              "env://CHECKPOINT_SECRET",
            active: true,
            created_at:
              "2026-08-02T12:00:00Z",
            retired_at: null
          }
        })}
      />
    );

    expect(
      screen.getByText("Available")
    ).toBeInTheDocument();

    expect(
      screen.getByText(
        "assessment-local-2026-01"
      )
    ).toBeInTheDocument();

    expect(
      screen.queryByText(
        /read-only mode/i
      )
    ).not.toBeInTheDocument();
  });

  it("explains unconfigured read-only mode", () => {
    render(
      <SigningCapabilityPanel
        capability={capability({
          status: "unconfigured",
          title:
            "Durable signing is not configured",
          message:
            "No active key is available.",
          statusCode: 503,
          reasonCode:
            "CHECKPOINT_SIGNING_UNAVAILABLE"
        })}
      />
    );

    expect(
      screen.getByText("Not configured")
    ).toBeInTheDocument();

    expect(
      screen.getByText(
        /remain available in read-only mode/i
      )
    ).toBeInTheDocument();
  });

  it("shows unauthorized status without exposing internals", () => {
    render(
      <SigningCapabilityPanel
        capability={capability({
          status: "unauthorized",
          title: "Signing access denied",
          message:
            "Your operator identity is not authorized.",
          statusCode: 403,
          reasonCode: "ACCESS_DENIED"
        })}
      />
    );

    expect(
      screen.getByText("Access denied")
    ).toBeInTheDocument();

    expect(
      screen.getByText(
        "Your operator identity is not authorized."
      )
    ).toBeInTheDocument();

    expect(
      screen.queryByText("ACCESS_DENIED")
    ).not.toBeInTheDocument();
  });

  it("marks unreachable capability as degraded", () => {
    render(
      <SigningCapabilityPanel
        capability={capability({
          status: "unreachable",
          title:
            "Signing service is unreachable",
          message:
            "The backend could not be reached."
        })}
      />
    );

    const panel = screen
      .getByText(
        "Signing service is unreachable"
      )
      .closest("section");

    expect(panel).toHaveAttribute(
      "data-capability-status",
      "unreachable"
    );
  });
});
